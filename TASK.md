# 100x Gem Screener — Build Task

## Project Overview
Build a crypto token screening tool that identifies potential high-alpha ("100x") opportunities on Ethereum and Solana chains. Uses free APIs to apply a 4-phase screening protocol.

## Tech Stack
- Python 3.12, managed with `uv` (NOT pip)
- Use `uv init` to create project, `uv add` for dependencies
- Dependencies: `httpx` (async HTTP), `asyncio`
- No frameworks, keep it simple

## Project Structure
```
gem-screener/
├── pyproject.toml
├── src/
│   └── gem_screener/
│       ├── __init__.py
│       ├── main.py           # Entry point - orchestrates all phases
│       ├── config.py          # Load API keys from ~/.config/*/api_key
│       ├── data_sources/
│       │   ├── __init__.py
│       │   ├── defillama.py   # TVL, revenue, fees, DEX volume, stablecoins, emissions
│       │   ├── coingecko.py   # Market cap, FDV, circulating supply, ATH
│       │   ├── etherscan.py   # Contract verification, recent tx activity
│       │   └── sentiment.py   # Fear & Greed index
│       ├── phases/
│       │   ├── __init__.py
│       │   ├── phase1_macro.py   # Macro timing & sentiment
│       │   ├── phase2_value.py   # VC-style valuation (P/E, P/B)
│       │   ├── phase3_token.py   # Tokenomics (circulation, unlocks)
│       │   └── phase4_eco.py     # Ecosystem & utility validation
│       ├── red_flags.py       # Red flag checks (one-vote veto)
│       ├── scorer.py          # Scoring model (100 points)
│       └── reporter.py        # Format output report as text
```

## API Keys Location
Read from files:
- CoinGecko: `~/.config/coingecko/api_key`
- Etherscan: `~/.config/etherscan/api_key`
- Dune (backup): `~/.config/dune/api_key`
- Solscan (backup): `~/.config/solscan/api_key`

## API Reference

### DeFiLlama (FREE, no key needed)
Base URLs vary by endpoint type:
- Protocols/TVL: `https://api.llama.fi/`
- Stablecoins: `https://stablecoins.llama.fi/`
- Yields: `https://yields.llama.fi/`
- DEX/Fees: `https://api.llama.fi/`

Key endpoints:
- `GET /protocols` → all protocols with name, chain, chains[], tvl, mcap, fdv, category
- `GET /protocol/{name}` → detailed protocol data with TVL history
- `GET /overview/fees?dataType=dailyRevenue` → protocol revenue (total24h, total30d, chains[])
- `GET /overview/dexs` → DEX volume data
- `GET /stablecoins` → stablecoin list with circulating supply
- `GET /stablecoincharts/all` → total stablecoin supply over time
- `GET /api/emission/{protocol}` → token unlock/emission schedule
- `GET /api/treasuries` → protocol treasury data

Full OpenAPI spec available at: `/home/howie-ubuntu-wsl/defillama/defillama-api.json`

### CoinGecko (key required, 10K calls/month, 30/min rate limit)
Base: `https://api.coingecko.com/api/v3/`
Auth: query param `x_cg_demo_api_key=KEY`

Key endpoints:
- `GET /coins/{id}` → full coin data (mcap, fdv, circulating_supply, total_supply, ath, ath_change_percentage)
- `GET /simple/price?ids=X&vs_currencies=usd&include_market_cap=true&include_24hr_vol=true` → quick price+mcap

IMPORTANT: Rate limit 30 req/min. Add 2-second delays between requests. Batch where possible.

### Etherscan (key required, 5 calls/sec)
Base: `https://api.etherscan.io/v2/api?chainid=1`
Auth: query param `apikey=KEY`

Key endpoints:
- `module=contract&action=getabi&address=X` → check if contract is verified (status=1 means verified)
- `module=account&action=txlist&address=X&sort=desc&offset=10` → recent transactions (activity check)
- `module=stats&action=tokensupply&contractaddress=X` → token total supply

### Fear & Greed (FREE, no key)
- `https://api.alternative.me/fng/?limit=1` → current index (value, value_classification)

## Phase Details

### Phase I: Macro Timing & Sentiment (phase1_macro.py)
1. Fear & Greed Index → if < 20: "Prime buying zone", < 40: "Acceptable", else: "Caution"
2. Stablecoin supply (USDT + USDC) and 7d/30d change trend from DeFiLlama stablecoin charts
3. Output: market_status dict with sentiment score and stablecoin trend

### Phase II: VC-Style Valuation (phase2_value.py)
For each candidate:
1. P/E = Market Cap / (30d Revenue × 12) — from DeFiLlama revenue + CoinGecko mcap
2. P/B = Market Cap / TVL — from CoinGecko mcap / DeFiLlama TVL
3. Compare against sector benchmarks

### Phase III: Tokenomics (phase3_token.py)
For each candidate:
1. Circulating ratio = circulating_supply / total_supply from CoinGecko → must be > 70%
2. Token emission/unlock schedule from DeFiLlama `/api/emission/{protocol}` → check for cliffs in next 6 months

### Phase IV: Ecosystem Validation (phase4_eco.py)
For each candidate:
1. Contract verified on Etherscan (for ETH tokens)
2. Recent transaction count (last 100 blocks) from Etherscan
3. DEX trading volume from DeFiLlama
4. TVL trend: 7d and 30d change percentage from DeFiLlama protocol data

## Red Flags (red_flags.py) — Any of these = immediate disqualification
1. "Air Coin": Contract not verified on Etherscan
2. "Data Fabrication": TVL change > 200% in 7 days (suspicious)
3. "Liquidity Ghosting": 24h DEX volume / mcap < 1% (no real liquidity)
4. Circulating ratio < 50% (dump risk)

## Scoring Model (scorer.py) — Total 100 points
| Dimension | Max | Logic |
|---|---|---|
| P/B (deep value) | 25 | <0.5→25, <1→20, <3→10, else→0 |
| P/E (earnings) | 20 | <10→20, <20→15, <50→10, else→0 |
| Circulation >70% | 15 | >80%→15, >70%→12, >50%→5, else→0 |
| 30d Revenue | 15 | >$500K→15, >$100K→10, >$10K→5, else→0 |
| TVL & trend | 10 | TVL>$50M→5 + 7d growth>0→5 |
| On-chain activity | 10 | Recent txns active→10, moderate→5 |
| No red flags | 5 | Pass all→5 |

## Screening Funnel
1. DeFiLlama `/protocols` → filter chains: Ethereum OR Solana
2. Filter: mcap $5M - $500M (small-mid cap gems)
3. Filter: TVL > $1M
4. CoinGecko: enrich with mcap, fdv, circulating ratio (batch, respect rate limits!)
5. Filter: circulating ratio > 50%
6. DeFiLlama revenue → compute P/E, P/B
7. Red flag checks
8. Score and rank
9. Output Top 3

## Reporter (reporter.py)
Generate a clean text report like:
```
📊 100x Gem Report — 2026-02-23

🌡️ Market Sentiment: Fear & Greed 7 (Extreme Fear) ✅ PRIME BUYING ZONE
💰 Stablecoins: USDT $182.6B | USDC $74.0B | 7d trend: +0.5%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🥇 #1 Lido (LDO) — Score: 85/100
   Category: Liquid Staking | Chain: Ethereum, Solana
   MCap: $275M | FDV: $325M | TVL: $18.3B
   P/B: 0.01 | P/E: 4.5 | Circ: 85%
   30d Revenue: $5.05M | ATH: $7.30 (-95.5%)
   ✅ Contract verified | ✅ Active on-chain | ✅ No red flags

🥈 #2 ...
🥉 #3 ...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ Filtered out (red flags): [ProjectX: unverified contract], [ProjectY: suspicious TVL spike]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Full screening: X protocols → Y after filters → Z scored → Top 3
```

## main.py Flow
```python
async def main():
    # Phase I
    macro = await phase1_macro.analyze()
    print_macro_report(macro)
    
    # Get candidates from DeFiLlama
    protocols = await defillama.get_protocols(chains=["Ethereum", "Solana"], min_tvl=1_000_000)
    
    # Enrich with CoinGecko (respect rate limits!)
    enriched = await coingecko.enrich_protocols(protocols)
    
    # Filter by mcap range and circulation
    candidates = [p for p in enriched if 5e6 <= p.mcap <= 500e6 and p.circ_ratio > 0.5]
    
    # Phase II: Valuation
    candidates = await phase2_value.analyze(candidates)
    
    # Phase III: Tokenomics
    candidates = await phase3_token.analyze(candidates)
    
    # Phase IV: Ecosystem
    candidates = await phase4_eco.analyze(candidates)
    
    # Red flag check
    candidates, flagged = red_flags.check(candidates)
    
    # Score and rank
    ranked = scorer.rank(candidates)
    
    # Report
    report = reporter.generate(macro, ranked[:3], flagged, stats)
    print(report)
```

## Important Notes
- Use `uv init` and `uv add httpx` to set up the project
- All HTTP calls should be async with httpx.AsyncClient
- CoinGecko: add 2s delay between individual coin requests (30/min limit)
- Etherscan: max 5 calls/sec
- Handle API errors gracefully (retry once, then skip)
- Use dataclasses for protocol data structures
- The script should be runnable with: `uv run python -m gem_screener`
