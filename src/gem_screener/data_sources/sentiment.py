"""Fear & Greed Index from alternative.me."""
import httpx


async def get_fear_greed(client: httpx.AsyncClient) -> dict:
    """Returns {value: int, classification: str}."""
    r = await client.get("https://api.alternative.me/fng/?limit=1", timeout=10)
    r.raise_for_status()
    d = r.json()["data"][0]
    return {"value": int(d["value"]), "classification": d["value_classification"]}
