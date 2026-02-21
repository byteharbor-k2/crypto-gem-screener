"""Red flag checks — any flag = disqualification."""
from .models import Protocol
from . import config


def check(candidates: list[Protocol]) -> tuple[list[Protocol], list[Protocol]]:
    """Returns (passed, flagged) lists."""
    passed = []
    flagged = []

    for p in candidates:
        flags = []

        # 1. Air Coin: contract not verified (ETH only, and only if address exists)
        if "Ethereum" in p.chains and p.contract_address and p.contract_address.startswith("0x"):
            if p.contract_verified is False:
                flags.append("Unverified contract")

        # 2. Data Fabrication: TVL spike > 200% in 7d
        if p.tvl_change_7d is not None and p.tvl_change_7d > 200:
            flags.append(f"Suspicious TVL spike ({p.tvl_change_7d:.0f}% 7d)")

        # 3. TVL crash: TVL dropped > 50% in 7d (possible rug / exodus)
        if p.tvl_change_7d is not None and p.tvl_change_7d < -50:
            flags.append(f"TVL crash ({p.tvl_change_7d:.0f}% 7d)")

        # 4. Circulation below hard minimum
        if p.circ_ratio is not None and p.circ_ratio < config.CIRC_RATIO_HARD_MIN:
            flags.append(f"Dangerously low circulation ({p.circ_ratio*100:.0f}%)")

        # 5. Upcoming major unlock (>5% in 6 months)
        if p.has_upcoming_unlock is True:
            flags.append(f"Major unlock: {p.unlock_detail}")

        # NOTE: We intentionally do NOT flag low DEX volume as a red flag for
        # non-DEX protocols. A lending protocol or yield aggregator won't have
        # direct DEX volume.

        p.red_flags = flags
        if flags:
            flagged.append(p)
        else:
            passed.append(p)

    return passed, flagged
