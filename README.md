# 🔍 Crypto Gem Screener

[English](#english) | [中文](#中文)

---

<a id="english"></a>

## English

A systematic crypto screening tool that identifies potentially undervalued "100x gems" using a rigorous 4-phase due diligence protocol. Built with Python, powered by on-chain data.

### How It Works

The screener runs a VC-style pipeline, filtering ~2000 protocols down to the top 3 candidates:

```
~2000 protocols → Chain filter → MCap/TVL filter → Valuation → Tokenomics → Ecosystem → Red flags → Score → Top 3
```

**Phase I — Macro Timing**
- Fear & Greed Index (only buy in Extreme Fear < 20)
- Stablecoin inflow tracking (USDT/USDC supply changes)

**Phase II — Valuation**
- P/E ratio (Market Cap / Annualized Revenue)
- P/B ratio (Market Cap / TVL)
- Targets deep value: P/B < 1

**Phase III — Tokenomics**
- Circulating supply ratio ≥ 70%
- Token unlock schedule check

**Phase IV — Ecosystem**
- Smart contract verification (Etherscan)
- On-chain transaction activity
- DEX volume analysis

**Red Flags (instant reject):**
- Unverified contracts
- TVL spike > 200% in 7d (wash trading)
- TVL crash > 50% in 7d
- Circulation < 50%

### Scoring Model (100 points)

Three-layer weighted model (configurable in `config.py`):

| Layer | Weight | Key Signals |
|------|--------|-------------|
| Fundamental (RootData) | 35 | Funding size, investor breadth, narrative tags |
| Market (CoinGecko + valuation) | 35 | P/B, P/E, circulation ratio, 30d revenue |
| On-chain (Etherscan + DeFiLlama) | 30 | Contract activity, TVL scale/trend, verification, clean profile |

If `ROOTDATA_API_KEY` is missing or RootData is unavailable, the screener auto-falls back to a 2-layer model and re-normalizes active weights to keep total score at 100.

### Data Sources

| Source | Coverage | Auth |
|--------|----------|------|
| [DeFiLlama](https://defillama.com/) | TVL, fees, revenue, DEX volume, stablecoins | Free, no key |
| [CoinGecko](https://www.coingecko.com/) | Market cap, FDV, circulating supply | Free demo key |
| [Etherscan](https://etherscan.io/) | Contract verification, tx activity | Free key |
| [RootData](https://www.rootdata.com/Api) | Project metadata, funding rounds, investor coverage | API key required |
| [Alternative.me](https://alternative.me/) | Fear & Greed Index | Free, no key |

### Quick Start

```bash
# Clone
git clone https://github.com/Howie-New/crypto-gem-screener.git
cd crypto-gem-screener

# Install (requires Python 3.12+ and uv)
uv sync

# Set API keys
mkdir -p ~/.config/coingecko ~/.config/etherscan ~/.config/rootdata
echo "YOUR_COINGECKO_KEY" > ~/.config/coingecko/api_key
echo "YOUR_ETHERSCAN_KEY" > ~/.config/etherscan/api_key
echo "YOUR_ROOTDATA_KEY" > ~/.config/rootdata/api_key

# Or use environment variables
export COINGECKO_API_KEY="your-key"
export ETHERSCAN_API_KEY="your-key"
export ROOTDATA_API_KEY="your-key"

# Run
uv run python -m gem_screener
```

### Configuration

Edit `src/gem_screener/config.py` to adjust screening parameters:

```python
CHAINS = ["Ethereum", "Solana"]   # Target chains
MCAP_MIN = 5_000_000             # $5M minimum market cap
MCAP_MAX = 500_000_000           # $500M maximum
TVL_MIN = 1_000_000              # $1M minimum TVL
CIRC_RATIO_MIN = 0.70            # 70% minimum circulation
```

### Sample Output

```
🔍 100x Gem Report — 2026-02-21 15:26

📊 Market Conditions:
• Fear & Greed: 8 (Extreme Fear)
• USDT: $182.54B (7d -0.6% | 30d -2.3%)
• USDC: $74.48B (7d +1.3% | 30d +0.3%)
• Verdict: ✅ GO

🥇 Usual — 97/100
   RWA | Ethereum
   MCap: $24.1M | FDV: $24.2M | TVL: $108.7M
   P/B: 0.22 | P/E: 3.9 | Circ: 100%
   📊 pb=25 + pe=20 + circ=15 + rev=15 + tvl=7 + activity=10 + clean=5

🥈 Rocket Pool — 95/100
🥉 Lido — 95/100
```

### Disclaimer

⚠️ **This tool is for research and educational purposes only.** It is NOT financial advice. Always do your own research (DYOR) before making any investment decisions. Crypto is highly volatile and you may lose your entire investment.

---

<a id="中文"></a>

## 中文

一个系统性加密货币筛选工具，使用严格的四阶段尽调流程，识别被低估的潜在"百倍币"。Python 构建，链上数据驱动。

### 工作原理

筛选器运行 VC 级别的筛选管道，从约 2000 个协议中筛选出 Top 3：

```
~2000 协议 → 链筛选 → 市值/TVL 筛选 → 估值分析 → 代币经济学 → 生态验证 → 红线检查 → 评分 → Top 3
```

**第一阶段 — 宏观择时**
- 恐惧贪婪指数（仅在极度恐惧 < 20 时买入）
- 稳定币流入追踪（USDT/USDC 供应变化）

**第二阶段 — 估值筛选**
- P/E 比率（市值 / 年化收入）
- P/B 比率（市值 / TVL）
- 寻找深度价值：P/B < 1

**第三阶段 — 代币经济学**
- 流通比例 ≥ 70%
- 代币解锁时间表检查

**第四阶段 — 生态验证**
- 智能合约验证（Etherscan）
- 链上交易活跃度
- DEX 交易量分析

**红线（一票否决）：**
- 未验证合约
- TVL 7天暴涨 > 200%（刷量嫌疑）
- TVL 7天暴跌 > 50%
- 流通量 < 50%

### 评分模型（满分 100）

采用三层加权模型（可在 `config.py` 调整）：

| 层级 | 权重 | 关键因子 |
|------|------|---------|
| 基本面层（RootData） | 35分 | 融资规模、投资方覆盖、叙事标签 |
| 市场层（CoinGecko + 估值） | 35分 | P/B、P/E、流通率、30天收入 |
| 链上层（Etherscan + DeFiLlama） | 30分 | 合约活跃度、TVL规模/趋势、验证状态、红线清洁度 |

若未配置 `ROOTDATA_API_KEY` 或 RootData 临时不可用，系统会自动降级为双层模型，并对剩余层级权重重新归一化，总分仍保持 100。

### 数据源

| 来源 | 覆盖 | 认证 |
|------|------|------|
| [DeFiLlama](https://defillama.com/) | TVL、费用、收入、DEX交易量、稳定币 | 免费，无需 key |
| [CoinGecko](https://www.coingecko.com/) | 市值、FDV、流通量 | 免费 demo key |
| [Etherscan](https://etherscan.io/) | 合约验证、交易活跃度 | 免费 key |
| [RootData](https://www.rootdata.com/Api) | 项目资料、融资信息、投资方覆盖 | 需要 API key |
| [Alternative.me](https://alternative.me/) | 恐惧贪婪指数 | 免费，无需 key |

### 快速开始

```bash
# 克隆
git clone https://github.com/Howie-New/crypto-gem-screener.git
cd crypto-gem-screener

# 安装（需要 Python 3.12+ 和 uv）
uv sync

# 设置 API Keys
mkdir -p ~/.config/coingecko ~/.config/etherscan
echo "你的_COINGECKO_KEY" > ~/.config/coingecko/api_key
echo "你的_ETHERSCAN_KEY" > ~/.config/etherscan/api_key

# 或使用环境变量
export COINGECKO_API_KEY="your-key"
export ETHERSCAN_API_KEY="your-key"
export ROOTDATA_API_KEY="your-key"

# 运行
uv run python -m gem_screener
```

### 配置

编辑 `src/gem_screener/config.py` 调整筛选参数：

```python
CHAINS = ["Ethereum", "Solana"]   # 目标链
MCAP_MIN = 5_000_000             # 最低市值 $5M
MCAP_MAX = 500_000_000           # 最高市值 $500M
TVL_MIN = 1_000_000              # 最低 TVL $1M
CIRC_RATIO_MIN = 0.70            # 最低流通率 70%
```

### ⚠️ 免责声明

**本工具仅供研究和学习使用，不构成任何投资建议。** 在做任何投资决策前请自行研究（DYOR）。加密货币波动极大，你可能会损失全部投资。

---

## License

MIT

## Author

Built by [Howie-New](https://github.com/Howie-New) with the help of [OpenClaw](https://openclaw.ai/) 🦞⚔️
