"""Data models."""
from dataclasses import dataclass, field


@dataclass
class Protocol:
    name: str
    slug: str
    category: str
    chains: list[str] = field(default_factory=list)
    # DeFiLlama
    tvl: float = 0.0
    tvl_change_7d: float | None = None
    tvl_change_30d: float | None = None
    fees_24h: float = 0.0
    fees_30d: float = 0.0
    rev_24h: float = 0.0
    rev_30d: float = 0.0
    dex_vol_24h: float = 0.0
    # CoinGecko
    cg_id: str = ""
    mcap: float = 0.0
    fdv: float = 0.0
    circ_supply: float = 0.0
    total_supply: float = 0.0
    circ_ratio: float | None = None
    price: float = 0.0
    ath: float = 0.0
    ath_drop_pct: float = 0.0
    # Etherscan
    contract_address: str = ""
    contract_verified: bool | None = None
    recent_tx_count: int = 0
    # RootData
    rootdata_id: int | None = None
    rootdata_total_funding: float = 0.0
    rootdata_investor_count: int = 0
    rootdata_investor_names: list[str] = field(default_factory=list)
    rootdata_tags: list[str] = field(default_factory=list)
    # Emissions / Unlocks
    has_upcoming_unlock: bool | None = None  # True if >5% unlock in 6 months
    unlock_detail: str = ""
    # Scoring
    score: int = 0
    red_flags: list[str] = field(default_factory=list)
    score_breakdown: dict = field(default_factory=dict)
    layer_reasons: dict[str, str] = field(default_factory=dict)
    rootdata_score: int = 0
    market_score: int = 0
    onchain_score: int = 0
    # Computed
    pe: float | None = None   # MCap / Annualized Revenue
    pb: float | None = None   # MCap / TVL


@dataclass
class MacroStatus:
    fng_value: int = 0
    fng_label: str = ""
    fng_signal: str = ""  # "buy" / "caution" / "avoid"
    usdt_supply: float = 0.0
    usdc_supply: float = 0.0
    usdt_7d_change: float = 0.0
    usdc_7d_change: float = 0.0
    usdt_30d_change: float = 0.0
    usdc_30d_change: float = 0.0
    stablecoin_total: float = 0.0
    stablecoin_7d_change: float | None = None
    verdict: str = ""  # "GO" / "CAUTION" / "STAND DOWN"
