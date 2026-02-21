"""Etherscan API - contract verification and on-chain activity."""
import asyncio
import httpx
from ..config import ETHERSCAN_KEY, ETHERSCAN_DELAY
from ..models import Protocol

BASE = "https://api.etherscan.io/v2/api"


async def check_contract(client: httpx.AsyncClient, address: str) -> bool | None:
    """Check if a contract is verified. Returns True/False/None."""
    if not address or not address.startswith("0x"):
        return None
    try:
        r = await client.get(
            BASE,
            params={
                "chainid": 1,
                "module": "contract",
                "action": "getabi",
                "address": address,
                "apikey": ETHERSCAN_KEY,
            },
            timeout=10,
        )
        if r.status_code == 200:
            return r.json().get("status") == "1"
    except Exception:
        pass
    return None


async def get_recent_tx_count(client: httpx.AsyncClient, address: str) -> int:
    """Get recent transaction count for a contract address."""
    if not address or not address.startswith("0x"):
        return 0
    try:
        r = await client.get(
            BASE,
            params={
                "chainid": 1,
                "module": "account",
                "action": "txlist",
                "address": address,
                "startblock": 0,
                "endblock": 99999999,
                "page": 1,
                "offset": 50,
                "sort": "desc",
                "apikey": ETHERSCAN_KEY,
            },
            timeout=10,
        )
        if r.status_code == 200:
            data = r.json()
            if data.get("status") == "1":
                return len(data.get("result", []))
    except Exception:
        pass
    return 0


async def enrich_protocols(client: httpx.AsyncClient, protocols: list[Protocol]) -> list[Protocol]:
    """Check contract verification and activity for ETH protocols."""
    eth_protos = [p for p in protocols if "Ethereum" in p.chains and p.contract_address]
    print(f"  Checking {len(eth_protos)} contracts on Etherscan...")

    for i, proto in enumerate(eth_protos):
        proto.contract_verified = await check_contract(client, proto.contract_address)
        await asyncio.sleep(ETHERSCAN_DELAY)
        proto.recent_tx_count = await get_recent_tx_count(client, proto.contract_address)
        await asyncio.sleep(ETHERSCAN_DELAY)
        if (i + 1) % 20 == 0:
            print(f"    ... {i + 1}/{len(eth_protos)} done")

    return protocols
