"""DeFiLlama API — TVL, fees, revenue, DEX volume, stablecoins, emissions."""
import httpx
from ..models import Protocol
from .. import config

API = "https://api.llama.fi"
STABLES_API = "https://stablecoins.llama.fi"


async def get_protocols(client: httpx.AsyncClient, chains: list[str]) -> list[Protocol]:
    """Fetch all protocols, filter by chain, return Protocol objects."""
    r = await client.get(f"{API}/protocols", timeout=30)
    r.raise_for_status()
    results = []
    for p in r.json():
        p_chains = p.get("chains", [])
        if not any(c in p_chains for c in chains):
            continue
        cat = p.get("category", "")
        if cat in config.EXCLUDE_CATEGORIES:
            continue
        mcap = p.get("mcap") or 0
        tvl = p.get("tvl") or 0
        prot = Protocol(
            name=p.get("name", ""),
            slug=p.get("slug", p.get("name", "").lower().replace(" ", "-")),
            category=cat,
            chains=[c for c in p_chains if c in chains],
            tvl=tvl,
            tvl_change_7d=p.get("change_7d"),
            tvl_change_30d=p.get("change_1m"),
            mcap=mcap,
            fdv=p.get("fdv") or 0,
            cg_id=p.get("gecko_id", ""),
            contract_address=p.get("address", ""),
        )
        results.append(prot)
    return results


async def get_fees_and_revenue(client: httpx.AsyncClient, chains: list[str]) -> dict[str, dict]:
    """Get BOTH fees and revenue. Returns {name_lower: {fees24h, fees30d, rev24h, rev30d}}."""
    result = {}

    # Fetch fees
    r = await client.get(
        f"{API}/overview/fees",
        params={"excludeTotalDataChart": "true", "excludeTotalDataChartBreakdown": "true"},
        timeout=30,
    )
    r.raise_for_status()
    for p in r.json().get("protocols", []):
        p_chains = p.get("chains") or []
        if any(c in p_chains for c in chains):
            name = p.get("name", "").lower()
            result[name] = {
                "fees24h": p.get("total24h") or 0,
                "fees30d": p.get("total30d") or 0,
                "rev24h": 0,
                "rev30d": 0,
            }

    # Fetch revenue (separate call with dataType=dailyRevenue)
    try:
        r2 = await client.get(
            f"{API}/overview/fees",
            params={
                "excludeTotalDataChart": "true",
                "excludeTotalDataChartBreakdown": "true",
                "dataType": "dailyRevenue",
            },
            timeout=30,
        )
        r2.raise_for_status()
        for p in r2.json().get("protocols", []):
            p_chains = p.get("chains") or []
            if any(c in p_chains for c in chains):
                name = p.get("name", "").lower()
                if name not in result:
                    result[name] = {"fees24h": 0, "fees30d": 0, "rev24h": 0, "rev30d": 0}
                result[name]["rev24h"] = p.get("total24h") or 0
                result[name]["rev30d"] = p.get("total30d") or 0
    except Exception:
        pass

    return result


async def get_dex_volumes(client: httpx.AsyncClient, chains: list[str]) -> dict[str, float]:
    """Get DEX 24h volume by protocol name. Returns {name_lower: vol24h}."""
    r = await client.get(
        f"{API}/overview/dexs",
        params={"excludeTotalDataChart": "true", "excludeTotalDataChartBreakdown": "true"},
        timeout=30,
    )
    r.raise_for_status()
    result = {}
    for p in r.json().get("protocols", []):
        p_chains = p.get("chains") or []
        if any(c in p_chains for c in chains):
            result[p.get("name", "").lower()] = p.get("total24h") or 0
    return result


async def get_stablecoin_data(client: httpx.AsyncClient) -> dict:
    """Get stablecoin supplies with period changes."""
    r = await client.get(f"{STABLES_API}/stablecoins?includePrices=true", timeout=15)
    r.raise_for_status()
    assets = r.json().get("peggedAssets", [])

    data = {"usdt": 0, "usdc": 0, "total": 0,
            "usdt_7d": 0, "usdc_7d": 0, "usdt_30d": 0, "usdc_30d": 0}

    for a in assets:
        circ = a.get("circulating", {}).get("peggedUSD", 0) or 0
        circ_w = a.get("circulatingPrevWeek", {}).get("peggedUSD", 0) or 0
        circ_m = a.get("circulatingPrevMonth", {}).get("peggedUSD", 0) or 0
        data["total"] += circ

        if a.get("symbol") == "USDT":
            data["usdt"] = circ
            data["usdt_7d"] = ((circ - circ_w) / circ_w * 100) if circ_w else 0
            data["usdt_30d"] = ((circ - circ_m) / circ_m * 100) if circ_m else 0
        elif a.get("symbol") == "USDC":
            data["usdc"] = circ
            data["usdc_7d"] = ((circ - circ_w) / circ_w * 100) if circ_w else 0
            data["usdc_30d"] = ((circ - circ_m) / circ_m * 100) if circ_m else 0

    return data


async def get_stablecoin_7d_change(client: httpx.AsyncClient) -> float | None:
    """Get 7d total stablecoin supply change percentage."""
    try:
        r = await client.get(f"{STABLES_API}/stablecoincharts/all", timeout=15)
        r.raise_for_status()
        data = r.json()
        if len(data) >= 8:
            now = sum(v for v in data[-1].get("totalCirculating", {}).values())
            week_ago = sum(v for v in data[-8].get("totalCirculating", {}).values())
            if week_ago > 0:
                return (now - week_ago) / week_ago * 100
    except Exception:
        pass
    return None


async def get_emissions(client: httpx.AsyncClient, slug: str) -> dict | None:
    """Get token emission/unlock schedule for a protocol."""
    try:
        r = await client.get(f"{API}/api/emission/{slug}", timeout=10)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None
