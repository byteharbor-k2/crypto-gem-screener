"""Main entry point — orchestrates all screening phases."""
import asyncio
import sys
import httpx
from . import config
from .data_sources import defillama, coingecko, etherscan, rootdata
from .phases import phase1_macro, phase2_value, phase3_token, phase4_eco
from . import red_flags, scorer, reporter


async def main():
    print("=" * 50)
    print("🔍 100x Gem Screener v2")
    print("=" * 50)

    async with httpx.AsyncClient(timeout=30) as client:
        # ─── Phase I: Macro Timing ───
        print("\n📊 Phase I: Macro Timing & Sentiment...")
        macro = await phase1_macro.analyze(client)
        print(f"  Fear & Greed: {macro.fng_value} ({macro.fng_label})")
        print(f"  USDT: ${macro.usdt_supply/1e9:.1f}B (7d {macro.usdt_7d_change:+.2f}% | 30d {macro.usdt_30d_change:+.2f}%)")
        print(f"  USDC: ${macro.usdc_supply/1e9:.1f}B (7d {macro.usdc_7d_change:+.2f}% | 30d {macro.usdc_30d_change:+.2f}%)")
        print(f"  Verdict: {macro.verdict}")

        # Early exit if market too greedy
        if macro.verdict == "STAND DOWN" and macro.fng_value >= 75:
            report = reporter.generate(macro, [], [], 0, 0)
            print("\n" + report)
            return report

        # ─── Fetch raw data ───
        print("\n📡 Fetching protocol data from DeFiLlama...")
        protocols = await defillama.get_protocols(client, config.CHAINS)
        total_screened = len(protocols)
        print(f"  Found {total_screened} protocols on {'/'.join(config.CHAINS)}")

        # Fees + Revenue data
        print("  Fetching fees & revenue data...")
        fees_revenue = await defillama.get_fees_and_revenue(client, config.CHAINS)
        print(f"  Fees/revenue data for {len(fees_revenue)} protocols")

        # DEX volumes
        print("  Fetching DEX volumes...")
        dex_volumes = await defillama.get_dex_volumes(client, config.CHAINS)
        print(f"  DEX volume data for {len(dex_volumes)} protocols")

        # ─── Initial filter ───
        print("\n🔽 Filtering candidates...")
        candidates = [
            p for p in protocols
            if config.MCAP_MIN <= p.mcap <= config.MCAP_MAX and p.tvl >= config.TVL_MIN
        ]
        print(f"  After mcap($5M-$500M)/TVL(>$1M) filter: {len(candidates)}")

        if not candidates:
            print("❌ No candidates found matching criteria!")
            return ""

        # ─── Phase II: Valuation ───
        print("\n📊 Phase II: Valuation (P/E, P/B)...")
        candidates = phase2_value.analyze(candidates, fees_revenue)
        with_revenue = [p for p in candidates if p.rev_30d > 0]
        print(f"  {len(with_revenue)}/{len(candidates)} have revenue data")

        # ─── CoinGecko enrichment ───
        print("\n📊 Phase III: Tokenomics (CoinGecko enrichment)...")
        candidates = await coingecko.enrich_protocols(client, candidates)
        candidates = phase3_token.analyze(candidates)

        # Filter by circulation
        pre_circ = len(candidates)
        candidates = [
            p for p in candidates
            if p.circ_ratio is None or p.circ_ratio >= config.CIRC_RATIO_MIN
        ]
        print(f"  After circulation filter (≥70%): {len(candidates)} (dropped {pre_circ - len(candidates)})")
        after_filter = len(candidates)

        # ─── RootData enrichment (fundamental layer) ───
        print("\n📊 RootData enrichment...")
        candidates, rootdata_enabled = await rootdata.enrich_protocols(client, candidates)

        # ─── Phase IV: Ecosystem ───
        print("\n📊 Phase IV: Ecosystem validation...")
        candidates = phase4_eco.analyze(candidates, dex_volumes)
        candidates = await etherscan.enrich_protocols(client, candidates)

        # ─── Red flags ───
        print("\n🚩 Red flag checks...")
        passed, flagged = red_flags.check(candidates)
        print(f"  Passed: {len(passed)} | Flagged: {len(flagged)}")

        # ─── Score & rank ───
        print("\n⭐ Scoring & ranking...")
        ranked = scorer.rank(passed, rootdata_enabled=rootdata_enabled)

        # ─── Report ───
        print("\n" + "=" * 50)
        report = reporter.generate(macro, ranked[:3], flagged, total_screened, after_filter)
        print(report)

        # Extended table
        if ranked:
            table = reporter.generate_extended_table(ranked, limit=10)
            print(table)

        return report


def run():
    """Entry point."""
    return asyncio.run(main())


if __name__ == "__main__":
    run()
