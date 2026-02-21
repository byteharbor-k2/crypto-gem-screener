"""Phase II: VC-Style Valuation Filter (P/E, P/B)."""
from ..models import Protocol


def analyze(candidates: list[Protocol], fees_revenue: dict[str, dict]) -> list[Protocol]:
    """Compute P/E and P/B ratios for each candidate."""
    for p in candidates:
        # Attach fees and revenue data
        data = fees_revenue.get(p.name.lower(), {})
        p.fees_24h = data.get("fees24h", 0)
        p.fees_30d = data.get("fees30d", 0)
        p.rev_24h = data.get("rev24h", 0)
        p.rev_30d = data.get("rev30d", 0)

        # If no explicit revenue data, estimate as 50% of fees (common split)
        if p.rev_30d == 0 and p.fees_30d > 0:
            p.rev_30d = p.fees_30d * 0.5
            p.rev_24h = p.fees_24h * 0.5

        # P/B = MCap / TVL (TVL as proxy for "book value")
        if p.tvl > 0 and p.mcap > 0:
            p.pb = p.mcap / p.tvl

        # P/E = MCap / Annualized Revenue
        annual_rev = p.rev_30d * 12 if p.rev_30d else 0
        if annual_rev > 0 and p.mcap > 0:
            p.pe = p.mcap / annual_rev

    return candidates
