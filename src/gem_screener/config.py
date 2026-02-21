"""Configuration — API keys and screening parameters."""
import os
from pathlib import Path


def _read_key(service: str, env_var: str = "") -> str:
    """Read API key from env var, then fall back to ~/.config/<service>/api_key."""
    if env_var and os.environ.get(env_var):
        return os.environ[env_var]
    p = Path.home() / ".config" / service / "api_key"
    if p.exists():
        return p.read_text().strip()
    return ""


COINGECKO_KEY = _read_key("coingecko", "COINGECKO_API_KEY")
ETHERSCAN_KEY = _read_key("etherscan", "ETHERSCAN_API_KEY")
DUNE_KEY = _read_key("dune", "DUNE_API_KEY")

# Rate limits
CG_DELAY = 2.2        # seconds between CoinGecko requests (30/min with demo key)
ETHERSCAN_DELAY = 0.25 # 5 calls/sec

# Screening parameters
CHAINS = ["Ethereum", "Solana"]
MCAP_MIN = 5_000_000        # $5M minimum market cap
MCAP_MAX = 500_000_000      # $500M maximum (exclude mega caps)
TVL_MIN = 1_000_000         # $1M minimum TVL
CIRC_RATIO_MIN = 0.70       # 70% minimum circulation (protocol requirement)
CIRC_RATIO_HARD_MIN = 0.50  # 50% hard floor (red flag below this)

# Categories to exclude (not investable protocols)
EXCLUDE_CATEGORIES = {"CEX", "Chain", "Bridge", "Canonical Bridge"}
