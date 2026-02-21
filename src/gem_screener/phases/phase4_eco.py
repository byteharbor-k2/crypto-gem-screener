"""Phase IV: Ecosystem & Utility Validation."""
from ..models import Protocol


def analyze(candidates: list[Protocol], dex_volumes: dict[str, float]) -> list[Protocol]:
    """Attach DEX volume data."""
    for p in candidates:
        p.dex_vol_24h = dex_volumes.get(p.name.lower(), 0)
    return candidates
