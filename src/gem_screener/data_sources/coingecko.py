"""CoinGecko API - market cap, FDV, circulating supply, ATH."""
import asyncio
import httpx
from ..config import COINGECKO_KEY, CG_DELAY
from ..models import Protocol

BASE = "https://api.coingecko.com/api/v3"


async def _batch_market_data(client: httpx.AsyncClient, gecko_ids: list[str]) -> dict:
    """Batch fetch market data for up to 250 coins using /coins/markets."""
    result = {}
    # CoinGecko /coins/markets supports up to 250 per page
    for i in range(0, len(gecko_ids), 250):
        batch = gecko_ids[i:i+250]
        ids_str = ",".join(batch)
        try:
            r = await client.get(
                f"{BASE}/coins/markets",
                params={
                    "vs_currency": "usd",
                    "ids": ids_str,
                    "order": "market_cap_desc",
                    "per_page": "250",
                    "page": "1",
                    "sparkline": "false",
                    "x_cg_demo_api_key": COINGECKO_KEY,
                },
                timeout=20,
            )
            if r.status_code == 200:
                for coin in r.json():
                    result[coin["id"]] = {
                        "mcap": coin.get("market_cap") or 0,
                        "fdv": coin.get("fully_diluted_valuation") or 0,
                        "price": coin.get("current_price") or 0,
                        "circ_supply": coin.get("circulating_supply") or 0,
                        "total_supply": coin.get("total_supply") or 0,
                        "ath": coin.get("ath") or 0,
                        "ath_drop_pct": coin.get("ath_change_percentage") or 0,
                    }
            await asyncio.sleep(CG_DELAY)
        except Exception as e:
            print(f"    CoinGecko batch error: {e}")
    return result


async def enrich_protocols(client: httpx.AsyncClient, protocols: list[Protocol]) -> list[Protocol]:
    """Enrich protocols with CoinGecko data using batch API."""
    to_enrich = [p for p in protocols if p.cg_id]
    gecko_ids = list(set(p.cg_id for p in to_enrich))
    print(f"  Batch fetching {len(gecko_ids)} coins from CoinGecko...")

    market_data = await _batch_market_data(client, gecko_ids)
    print(f"  Got data for {len(market_data)} coins")

    for proto in to_enrich:
        d = market_data.get(proto.cg_id)
        if not d:
            continue
        proto.mcap = d["mcap"] or proto.mcap
        proto.fdv = d["fdv"] or proto.fdv
        proto.price = d["price"]
        proto.circ_supply = d["circ_supply"]
        proto.total_supply = d["total_supply"]
        proto.ath = d["ath"]
        proto.ath_drop_pct = d["ath_drop_pct"]

        if proto.total_supply and proto.total_supply > 0 and proto.circ_supply:
            proto.circ_ratio = proto.circ_supply / proto.total_supply

    return protocols
