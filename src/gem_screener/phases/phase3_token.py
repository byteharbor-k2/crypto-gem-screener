"""Phase III: Tokenomics & Structural Integrity."""
from ..models import Protocol


def analyze(candidates: list[Protocol]) -> list[Protocol]:
    """Check circulation ratio. Compute from FDV if CoinGecko didn't provide it."""
    for p in candidates:
        # If CoinGecko didn't set circ_ratio, try from mcap/fdv
        if p.circ_ratio is None and p.fdv and p.fdv > 0 and p.mcap > 0:
            p.circ_ratio = min(p.mcap / p.fdv, 1.0)
    return candidates
