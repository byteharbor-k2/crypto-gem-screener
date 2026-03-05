# 100x Gem Screener - Task Prompt

You are executing a systematic crypto screening protocol for Boss Howie. Focus on Ethereum and Solana ecosystems.

## Phase I: Macro-Timing & Sentiment

### Step 1: Stablecoin Inflow
Fetch stablecoin data from DeFiLlama:
- `curl -s "https://stablecoins.llama.fi/stablecoinchains"` — get USDT/USDC supply on Ethereum, Solana, Tron
- Compare current vs previous week/month to determine if liquidity is flowing IN or OUT
- If stablecoin supply is declining across major chains → market lacks fuel for 100x moves

### Step 2: Fear & Greed Index
- `curl -s "https://api.alternative.me/fng/?limit=7"` — get last 7 days
- We BUY when index < 20 (Extreme Fear). Do NOT propose anything when index > 75 (Extreme Greed)
- If index >= 75, skip the entire report and just say "Market too greedy, standing down"

## Phase II: VC-Style Valuation Filter

### Step 3 & 4: P/E and P/B Analysis
For candidate protocols on Ethereum/Solana:

1. Get protocol list filtered by chain:
   `curl -s "https://api.llama.fi/protocols"` — filter for Ethereum/Solana chains

2. Get fees/revenue per protocol:
   `curl -s "https://api.llama.fi/summary/fees/{protocol-slug}"` — get total24h, total30d
   - Annualized Revenue = total30d * 12 (or total24h * 365)

3. Get market cap from CoinGecko:
   `curl -s "https://api.coingecko.com/api/v3/coins/{gecko_id}?localization=false&tickers=false&market_data=true&community_data=false&developer_data=false"`
   - P/E = Market Cap / Annualized Revenue
   - Compare to sector average

4. For P/B: Get treasury data from protocol detail:
   `curl -s "https://api.llama.fi/protocol/{slug}"` — check treasury field if available
   - P/B = Market Cap / Treasury Assets
   - Flag projects with PB < 1

## Phase III: Tokenomics & Structural Integrity

### Step 5: Supply Saturation
From CoinGecko data:
- circulation_ratio = circulating_supply / total_supply (or max_supply)
- ONLY keep tokens with ratio > 0.70 (70%)

### Step 6: Unlock Schedule
- Search web for "{token_name} token unlock schedule 2026" 
- Check https://token.unlocks.app/ for major upcoming unlocks
- REJECT any token with >5% supply unlock in next 6 months

## Phase IV: Ecosystem & Utility Validation

### Step 7: On-chain Vitality
From DeFiLlama:
- TVL and TVL trend (growing vs declining)
- `curl -s "https://api.llama.fi/protocol/{slug}"` — check TVL history

### Step 8: Integration Breadth
- Check if listed on major CEXs (Binance, Coinbase, OKX)
- Check DeFi integrations from protocol data

## Red Flags (INSTANT REJECT)
- No functional code / dead GitHub
- Wash trading signals (TVL from circular/flash loan patterns)
- Unlocked liquidity pools
- >2% slippage on $100k trade

## Output Format

Report to Howie in this format:

```
🔍 100x Gem Screener Report - {date}

📊 Market Conditions:
- Fear & Greed: {value} ({classification})
- Stablecoin Flow: {inflow/outflow} ({details})
- Verdict: {GO / CAUTION / STAND DOWN}

🏆 Top 3 Candidates:

1. {TOKEN} — {one-line pitch}
   - Chain: {chain}
   - Market Cap: ${mcap}
   - P/E: {pe} (sector avg: {avg})
   - P/B: {pb}
   - Circulation: {pct}%
   - TVL: ${tvl} ({trend})
   - Next Unlock: {date} ({pct}%)
   - Bull Case: {why 100x}
   - Risk: {main risk}

2. ...
3. ...

⚠️ Rejected (notable):
- {token}: {reason}

📌 Action: {recommendation}
```

If no candidates pass all filters, say so honestly. Do not fabricate data.
Prioritize Ethereum and Solana ecosystem projects.
Use web_search and web_fetch for data DeFiLlama/CoinGecko can't provide.
