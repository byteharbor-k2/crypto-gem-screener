"""Scoring model — 100 points max."""
from .models import Protocol


def score(p: Protocol) -> int:
    """Compute score for a single protocol. Returns (total, breakdown)."""
    breakdown = {}

    # P/B: deep value (25 pts)
    if p.pb is not None:
        if p.pb < 0.5:
            breakdown["pb"] = 25
        elif p.pb < 1:
            breakdown["pb"] = 20
        elif p.pb < 3:
            breakdown["pb"] = 10
        else:
            breakdown["pb"] = 0
    else:
        breakdown["pb"] = 0

    # P/E: earnings valuation (20 pts)
    if p.pe is not None:
        if p.pe < 10:
            breakdown["pe"] = 20
        elif p.pe < 20:
            breakdown["pe"] = 15
        elif p.pe < 50:
            breakdown["pe"] = 10
        else:
            breakdown["pe"] = 0
    else:
        breakdown["pe"] = 0

    # Circulation ratio (15 pts)
    if p.circ_ratio is not None:
        if p.circ_ratio > 0.80:
            breakdown["circ"] = 15
        elif p.circ_ratio > 0.70:
            breakdown["circ"] = 12
        elif p.circ_ratio > 0.50:
            breakdown["circ"] = 5
        else:
            breakdown["circ"] = 0
    else:
        breakdown["circ"] = 0

    # 30d Revenue — real earnings (15 pts)
    if p.rev_30d > 500_000:
        breakdown["rev"] = 15
    elif p.rev_30d > 100_000:
        breakdown["rev"] = 10
    elif p.rev_30d > 10_000:
        breakdown["rev"] = 5
    else:
        breakdown["rev"] = 0

    # TVL scale & trend (10 pts)
    tvl_pts = 0
    if p.tvl > 50_000_000:
        tvl_pts += 5
    elif p.tvl > 10_000_000:
        tvl_pts += 3
    if p.tvl_change_7d is not None and p.tvl_change_7d > 0:
        tvl_pts += 5
    elif p.tvl_change_7d is not None and p.tvl_change_7d > -5:
        tvl_pts += 2
    breakdown["tvl"] = min(tvl_pts, 10)

    # On-chain activity (10 pts)
    if p.recent_tx_count >= 40:
        breakdown["activity"] = 10
    elif p.recent_tx_count >= 20:
        breakdown["activity"] = 7
    elif p.recent_tx_count > 0:
        breakdown["activity"] = 3
    else:
        # Solana protocols won't have Etherscan data — don't penalize
        if "Ethereum" not in p.chains:
            breakdown["activity"] = 5  # neutral for non-ETH
        else:
            breakdown["activity"] = 0

    # No red flags (5 pts)
    breakdown["clean"] = 5 if not p.red_flags else 0

    p.score_breakdown = breakdown
    return sum(breakdown.values())


def rank(candidates: list[Protocol]) -> list[Protocol]:
    """Score all candidates and sort by score descending."""
    for p in candidates:
        p.score = score(p)
    candidates.sort(key=lambda x: (-x.score, x.pe or 999))
    return candidates
