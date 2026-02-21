"""Phase I: Macro Timing & Sentiment Audit."""
import httpx
from ..models import MacroStatus
from ..data_sources import sentiment, defillama


async def analyze(client: httpx.AsyncClient) -> MacroStatus:
    """Analyze macro market conditions."""
    status = MacroStatus()

    # Fear & Greed
    fng = await sentiment.get_fear_greed(client)
    status.fng_value = fng["value"]
    status.fng_label = fng["classification"]
    if status.fng_value < 20:
        status.fng_signal = "buy"
    elif status.fng_value < 40:
        status.fng_signal = "caution"
    elif status.fng_value <= 75:
        status.fng_signal = "neutral"
    else:
        status.fng_signal = "avoid"

    # Stablecoin supply with period changes
    stables = await defillama.get_stablecoin_data(client)
    status.usdt_supply = stables["usdt"]
    status.usdc_supply = stables["usdc"]
    status.usdt_7d_change = stables["usdt_7d"]
    status.usdc_7d_change = stables["usdc_7d"]
    status.usdt_30d_change = stables["usdt_30d"]
    status.usdc_30d_change = stables["usdc_30d"]
    status.stablecoin_total = stables["total"]

    # 7d total change
    status.stablecoin_7d_change = await defillama.get_stablecoin_7d_change(client)

    # Verdict
    if status.fng_value >= 75:
        status.verdict = "STAND DOWN"
    elif status.fng_value < 20 and (status.stablecoin_7d_change or 0) > 0:
        status.verdict = "GO"
    elif status.fng_value < 20:
        status.verdict = "CAUTION"  # Fear but no inflow yet
    elif status.fng_value < 40:
        status.verdict = "CAUTION"
    else:
        status.verdict = "STAND DOWN"

    return status
