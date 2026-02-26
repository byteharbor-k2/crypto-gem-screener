# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Run Commands

```bash
# Install dependencies (uses uv, NOT pip)
uv sync

# Run the screener
uv run python -m gem_screener

# Run tests
uv run python -m pytest tests/

# Run a single test
uv run python -m pytest tests/test_three_layer_scoring.py::TestThreeLayerScoring::test_three_layer_score_components_present

# Run with notification script (Telegram/OpenClaw)
./run_and_notify.sh
```

Python 3.12 is required (`.python-version`).

## Architecture

This is a **4-phase cryptocurrency screening pipeline** that identifies undervalued tokens using a systematic scoring model. The entire pipeline runs as a single async execution from `__main__.py`.

### Pipeline flow

```
Phase I (Macro)  →  Data Fetch & Filter  →  Phase II (Valuation)  →  Phase III (Tokenomics)  →  Phase IV (On-chain)  →  Red Flags  →  Scoring  →  Report
```

1. **Phase I** (`phases/phase1_macro.py`): Checks Fear & Greed Index + stablecoin flows. Can exit early if FNG ≥ 75 ("STAND DOWN").
2. **Data fetch**: Pulls all protocols from DeFiLlama, filters by chain (ETH/SOL), market cap ($5M-$500M), and TVL (>$1M).
3. **Phase II** (`phases/phase2_value.py`): Computes P/B (mcap/TVL) and P/E (mcap/annualized revenue). Revenue estimated as 50% of fees if unavailable.
4. **Phase III** (`phases/phase3_token.py`): CoinGecko batch fetch for supply data. Filters by circulation ratio ≥ 70%. Optional RootData enrichment.
5. **Phase IV** (`phases/phase4_eco.py`): Etherscan contract verification and tx activity (Ethereum only). Attaches DEX volumes and TVL trends.
6. **Red flags** (`red_flags.py`): One-vote veto — any flag disqualifies (unverified contract, TVL spike >200%/7d, TVL crash >50%/7d, circulation <50%, major unlock).
7. **Scoring** (`scorer.py`): Three-layer weighted model totaling 100 points — RootData (35), Market (35), On-chain (30). Dynamically reweights to 2-layer if RootData unavailable.
8. **Report** (`reporter.py`): Generates Telegram-friendly markdown with top 3 detailed + top 10 table.

### Key design decisions

- **All async**: Uses `httpx.AsyncClient` throughout with configurable rate-limit delays (CoinGecko: 2.2s, Etherscan: 0.25s).
- **Graceful degradation**: If RootData API key is missing, scoring automatically falls back to 2-layer model with re-normalized weights.
- **No frameworks**: Intentionally minimal — only `httpx` as external dependency. Uses stdlib `dataclasses`, `asyncio`, `unittest`.
- **CoinGecko batching**: Up to 250 coins per request, with loop-splitting for larger sets.

### Data sources (`data_sources/`)

| Module | APIs | Auth |
|---|---|---|
| `defillama.py` | TVL, fees, revenue, DEX volume, stablecoins, emissions | None (free) |
| `coingecko.py` | Market cap, FDV, supply, ATH, price | Demo API key |
| `etherscan.py` | Contract verification, tx count (ETH only) | Free API key |
| `rootdata.py` | Funding, investors, tags | API key (optional) |
| `sentiment.py` | Fear & Greed Index | None (free) |

### API key configuration

Environment variables (preferred) or file-based fallback:
- `COINGECKO_API_KEY` / `~/.config/coingecko/api_key`
- `ETHERSCAN_API_KEY` / `~/.config/etherscan/api_key`
- `ROOTDATA_API_KEY` / `~/.config/rootdata/api_key` (optional)

All thresholds and weights are centralized in `config.py`.

### Data model

`models.py` defines two dataclasses:
- **`Protocol`**: Accumulates data across all phases — DeFiLlama fields, CoinGecko fields, Etherscan fields, RootData fields, computed metrics (P/E, P/B), and scoring results.
- **`MacroStatus`**: Fear & Greed values, stablecoin supplies/flows, and GO/CAUTION/STAND DOWN verdict.
