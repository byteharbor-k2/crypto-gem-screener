"""RootData API - project metadata, funding and investor coverage."""
from __future__ import annotations

import asyncio
import httpx

from ..config import ROOTDATA_KEY
from ..models import Protocol

BASE = "https://api.rootdata.com/open"


class RootDataUnavailable(Exception):
    """Raised when RootData cannot be used in current runtime."""


def _headers() -> dict[str, str]:
    return {
        "apikey": ROOTDATA_KEY,
        "language": "en",
        "Content-Type": "application/json",
    }


async def _post_with_retry(
    client: httpx.AsyncClient,
    path: str,
    payload: dict,
    retries: int = 3,
    timeout: float = 15.0,
) -> dict | None:
    if not ROOTDATA_KEY:
        raise RootDataUnavailable("ROOTDATA_API_KEY is not configured")

    last_error = None
    for attempt in range(retries):
        try:
            r = await client.post(f"{BASE}/{path}", headers=_headers(), json=payload, timeout=timeout)
            if r.status_code == 200:
                data = r.json()
                if data.get("result") == 200:
                    return data.get("data")
                last_error = RuntimeError(data.get("message") or f"RootData result={data.get('result')}")
            else:
                last_error = RuntimeError(f"HTTP {r.status_code}")
        except Exception as e:  # pragma: no cover - defensive network guard
            last_error = e

        if attempt < retries - 1:
            await asyncio.sleep(0.6 * (attempt + 1))

    print(f"  ⚠️ RootData request failed ({path}): {last_error}")
    return None


async def get_quota(client: httpx.AsyncClient) -> dict | None:
    """Get apikey quota info to verify access and remaining credits."""
    return await _post_with_retry(client, "quotacredits", payload={})


async def search_entity(client: httpx.AsyncClient, query: str) -> dict | None:
    """Search project/VC/people and return best matched project entity."""
    data = await _post_with_retry(client, "ser_inv", payload={"query": query})
    if not isinstance(data, list):
        return None

    best = None
    for item in data:
        if not isinstance(item, dict) or item.get("type") != 1:
            continue
        name = (item.get("name") or "").strip().lower()
        if name == query.strip().lower():
            return item
        if best is None:
            best = item
    return best


async def get_project_detail(client: httpx.AsyncClient, *, project_id: int | None = None, contract_address: str = "") -> dict | None:
    """Fetch RootData project detail via project_id or contract_address."""
    payload: dict[str, object] = {"include_investors": True}
    if project_id:
        payload["project_id"] = project_id
    elif contract_address:
        payload["contract_address"] = contract_address
    else:
        return None

    return await _post_with_retry(client, "get_item", payload=payload)


async def enrich_protocols(client: httpx.AsyncClient, protocols: list[Protocol]) -> tuple[list[Protocol], bool]:
    """Enrich protocols with RootData fields. Returns (protocols, enabled)."""
    if not ROOTDATA_KEY:
        print("  ⚠️ ROOTDATA_API_KEY not found, fundamental layer will be skipped")
        return protocols, False

    quota = await get_quota(client)
    if quota:
        print(f"  RootData credits: {quota.get('credits', 'N/A')} / {quota.get('total_credits', 'N/A')}")

    enriched = 0
    for proto in protocols:
        detail = None
        # Best-effort by contract address first for ETH projects.
        if proto.contract_address and proto.contract_address.startswith("0x"):
            detail = await get_project_detail(client, contract_address=proto.contract_address)

        if not detail:
            hit = await search_entity(client, proto.name)
            if hit and isinstance(hit.get("id"), int):
                detail = await get_project_detail(client, project_id=hit["id"])

        if not isinstance(detail, dict):
            continue

        proto.rootdata_id = detail.get("project_id")
        proto.rootdata_total_funding = float(detail.get("total_funding") or 0)
        investors = detail.get("investors") or []
        if isinstance(investors, list):
            proto.rootdata_investor_count = len(investors)
            proto.rootdata_investor_names = [i.get("name", "") for i in investors if isinstance(i, dict) and i.get("name")]
        tags = detail.get("tags") or []
        if isinstance(tags, list):
            proto.rootdata_tags = [str(t) for t in tags if t]

        enriched += 1
        await asyncio.sleep(0.2)

    print(f"  RootData enriched: {enriched}/{len(protocols)}")
    return protocols, True
