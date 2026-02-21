"""Scoring model — 3-layer weighted score (100 points max)."""
from __future__ import annotations

from . import config
from .models import Protocol


def _scale(raw: float, max_raw: float, weight: int) -> int:
    if max_raw <= 0 or weight <= 0:
        return 0
    raw = max(0.0, min(raw, max_raw))
    return int(round(raw / max_raw * weight))


def _fundamental_raw(p: Protocol) -> tuple[float, str]:
    raw = 0.0
    reasons = []

    if p.rootdata_total_funding >= 100_000_000:
        raw += 10
        reasons.append("large funding")
    elif p.rootdata_total_funding >= 20_000_000:
        raw += 7
        reasons.append("solid funding")
    elif p.rootdata_total_funding > 0:
        raw += 4
        reasons.append("early funding")

    if p.rootdata_investor_count >= 10:
        raw += 10
        reasons.append("broad investor backing")
    elif p.rootdata_investor_count >= 5:
        raw += 7
        reasons.append("multi-VC backing")
    elif p.rootdata_investor_count >= 1:
        raw += 4
        reasons.append("has named investors")

    if p.rootdata_tags:
        raw += min(5, len(p.rootdata_tags))
        reasons.append("clear narrative tags")

    return raw, ", ".join(reasons) if reasons else "no RootData signal"


def _market_raw(p: Protocol) -> tuple[float, str]:
    raw = 0.0
    reasons = []

    # Value (P/B)
    if p.pb is not None:
        if p.pb < 0.5:
            raw += 12
            reasons.append("deep value P/B")
        elif p.pb < 1:
            raw += 9
            reasons.append("value P/B")
        elif p.pb < 3:
            raw += 5

    # Earnings valuation (P/E)
    if p.pe is not None:
        if p.pe < 10:
            raw += 10
            reasons.append("cheap P/E")
        elif p.pe < 20:
            raw += 7
        elif p.pe < 50:
            raw += 4

    # Circulation health
    if p.circ_ratio is not None:
        if p.circ_ratio > 0.80:
            raw += 8
            reasons.append("high circulation")
        elif p.circ_ratio > 0.70:
            raw += 6
        elif p.circ_ratio > 0.50:
            raw += 3

    # Revenue quality
    if p.rev_30d > 500_000:
        raw += 5
        reasons.append("strong 30d revenue")
    elif p.rev_30d > 100_000:
        raw += 3

    return raw, ", ".join(reasons) if reasons else "no market signal"


def _onchain_raw(p: Protocol) -> tuple[float, str]:
    raw = 0.0
    reasons = []

    # Activity
    if p.recent_tx_count >= 40:
        raw += 12
        reasons.append("high tx activity")
    elif p.recent_tx_count >= 20:
        raw += 9
    elif p.recent_tx_count > 0:
        raw += 5
    elif "Ethereum" not in p.chains:
        raw += 6
        reasons.append("neutral non-ETH activity")

    # TVL scale and trend
    if p.tvl > 50_000_000:
        raw += 7
        reasons.append("large TVL")
    elif p.tvl > 10_000_000:
        raw += 4

    if p.tvl_change_7d is not None and p.tvl_change_7d > 0:
        raw += 6
        reasons.append("positive TVL trend")
    elif p.tvl_change_7d is not None and p.tvl_change_7d > -5:
        raw += 3

    # Contract verification quality signal
    if p.contract_verified is True:
        raw += 3
        reasons.append("verified contract")

    # Clean profile bonus
    if not p.red_flags:
        raw += 2

    return raw, ", ".join(reasons) if reasons else "no on-chain signal"


def score(p: Protocol, *, rootdata_enabled: bool = True) -> int:
    """Compute weighted score for a single protocol."""
    weights = {
        "rootdata": config.ROOTDATA_WEIGHT if rootdata_enabled else 0,
        "market": config.MARKET_WEIGHT,
        "onchain": config.ONCHAIN_WEIGHT,
    }
    total_weight = sum(weights.values())
    if total_weight <= 0:
        p.score_breakdown = {"rootdata": 0, "market": 0, "onchain": 0}
        p.layer_reasons = {
            "rootdata": "disabled",
            "market": "disabled",
            "onchain": "disabled",
        }
        p.rootdata_score = p.market_score = p.onchain_score = 0
        return 0

    fund_raw, fund_reason = _fundamental_raw(p)
    mkt_raw, mkt_reason = _market_raw(p)
    on_raw, on_reason = _onchain_raw(p)

    # Normalize active weights to 100 if a layer is disabled.
    norm_factor = 100 / total_weight
    adj_fund_w = int(round(weights["rootdata"] * norm_factor))
    adj_mkt_w = int(round(weights["market"] * norm_factor))
    adj_on_w = 100 - adj_fund_w - adj_mkt_w

    p.rootdata_score = _scale(fund_raw, max_raw=25, weight=adj_fund_w)
    p.market_score = _scale(mkt_raw, max_raw=35, weight=adj_mkt_w)
    p.onchain_score = _scale(on_raw, max_raw=30, weight=adj_on_w)

    p.score_breakdown = {
        "rootdata": p.rootdata_score,
        "market": p.market_score,
        "onchain": p.onchain_score,
    }
    p.layer_reasons = {
        "rootdata": fund_reason if rootdata_enabled else "RootData disabled (missing API key)",
        "market": mkt_reason,
        "onchain": on_reason,
    }
    return p.rootdata_score + p.market_score + p.onchain_score


def rank(candidates: list[Protocol], *, rootdata_enabled: bool = True) -> list[Protocol]:
    """Score all candidates and sort by score descending."""
    for p in candidates:
        p.score = score(p, rootdata_enabled=rootdata_enabled)
    candidates.sort(key=lambda x: (-x.score, x.pe or 999))
    return candidates
