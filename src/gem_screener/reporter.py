"""Report generator — Telegram-friendly format."""
from datetime import datetime
from .models import MacroStatus, Protocol


def _fmt_usd(v: float) -> str:
    if v >= 1e9:
        return f"${v/1e9:.2f}B"
    if v >= 1e6:
        return f"${v/1e6:.1f}M"
    if v >= 1e3:
        return f"${v/1e3:.0f}K"
    return f"${v:.0f}"


def _medal(i: int) -> str:
    return ["🥇", "🥈", "🥉"][i] if i < 3 else f"#{i+1}"


def _pct(v: float | None) -> str:
    if v is None:
        return "N/A"
    return f"{v:+.1f}%"


def generate(
    macro: MacroStatus,
    top: list[Protocol],
    flagged: list[Protocol],
    total_screened: int,
    after_filter: int,
) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = []
    lines.append(f"🔍 100x Gem Report — {now}")
    lines.append("")

    # Macro conditions
    verdict_emoji = {"GO": "✅", "CAUTION": "🟡", "STAND DOWN": "🔴"}.get(macro.verdict, "⚪")
    lines.append(f"📊 Market Conditions:")
    lines.append(f"• Fear & Greed: {macro.fng_value} ({macro.fng_label})")
    lines.append(f"• USDT: {_fmt_usd(macro.usdt_supply)} (7d {_pct(macro.usdt_7d_change)} | 30d {_pct(macro.usdt_30d_change)})")
    lines.append(f"• USDC: {_fmt_usd(macro.usdc_supply)} (7d {_pct(macro.usdc_7d_change)} | 30d {_pct(macro.usdc_30d_change)})")
    if macro.stablecoin_7d_change is not None:
        lines.append(f"• Total Stablecoin 7d: {_pct(macro.stablecoin_7d_change)}")
    lines.append(f"• Verdict: {verdict_emoji} {macro.verdict}")
    lines.append("")

    if macro.verdict == "STAND DOWN":
        lines.append("⛔ Market too greedy. No candidates this cycle.")
        return "\n".join(lines)

    lines.append("━" * 35)

    # Top candidates
    if not top:
        lines.append("\n❌ No candidates passed all filters this cycle.")
    else:
        for i, p in enumerate(top):
            lines.append("")
            chains_str = ", ".join(p.chains)
            lines.append(f"{_medal(i)} {p.name} — {p.score}/100")
            lines.append(f"   {p.category} | {chains_str}")
            lines.append(f"   MCap: {_fmt_usd(p.mcap)} | FDV: {_fmt_usd(p.fdv)} | TVL: {_fmt_usd(p.tvl)}")

            pb_str = f"{p.pb:.2f}" if p.pb is not None else "—"
            pe_str = f"{p.pe:.1f}" if p.pe is not None else "—"
            circ_str = f"{p.circ_ratio*100:.0f}%" if p.circ_ratio is not None else "—"
            lines.append(f"   P/B: {pb_str} | P/E: {pe_str} | Circ: {circ_str}")

            rev_str = _fmt_usd(p.rev_30d) if p.rev_30d else "$0"
            fees_str = _fmt_usd(p.fees_30d) if p.fees_30d else "$0"
            lines.append(f"   Rev30d: {rev_str} | Fees30d: {fees_str}")

            if p.ath > 0:
                lines.append(f"   Price: ${p.price:.4f} | ATH: ${p.ath:.2f} ({p.ath_drop_pct:.0f}%)")

            # Checks
            checks = []
            if p.contract_verified is True:
                checks.append("✅ Verified")
            elif p.contract_verified is None and "Solana" in p.chains:
                checks.append("— Solana (no contract check)")
            if p.recent_tx_count > 0:
                checks.append(f"✅ Active ({p.recent_tx_count} tx)")
            if not p.red_flags:
                checks.append("✅ Clean")
            if checks:
                lines.append(f"   {' | '.join(checks)}")

            # Score breakdown
            bd = p.score_breakdown
            if bd:
                lines.append(
                    f"   📊 Layers: rootdata={bd.get('rootdata', 0)} + market={bd.get('market', 0)} + onchain={bd.get('onchain', 0)}"
                )
                reasons = p.layer_reasons
                if reasons:
                    lines.append(f"   🧠 RootData: {reasons.get('rootdata', '—')}")
                    lines.append(f"   🧠 Market: {reasons.get('market', '—')}")
                    lines.append(f"   🧠 On-chain: {reasons.get('onchain', '—')}")

    lines.append("")
    lines.append("━" * 35)

    # Flagged
    if flagged:
        lines.append(f"⚠️ Filtered ({len(flagged)}):")
        for p in flagged[:5]:
            lines.append(f"  • {p.name}: {', '.join(p.red_flags)}")
        if len(flagged) > 5:
            lines.append(f"  ... +{len(flagged) - 5} more")
    else:
        lines.append("✅ No red flags triggered")

    lines.append("")
    lines.append(f"📈 Funnel: {total_screened} → {after_filter} filtered → Top {len(top)}")

    return "\n".join(lines)


def generate_extended_table(ranked: list[Protocol], limit: int = 10) -> str:
    """Generate extended top-N table."""
    lines = []
    lines.append(f"\n📋 Extended Top {limit}:")
    header = f"{'#':<3}{'Name':<22}{'Pts':<5}{'R':>4}{'M':>4}{'O':>4}{'MCap':>9}{'TVL':>10}{'P/B':>6}{'P/E':>7}{'Circ':>6}{'Rev30d':>9}"
    lines.append(header)
    lines.append("─" * len(header))
    for i, p in enumerate(ranked[:limit]):
        pb = f"{p.pb:.2f}" if p.pb is not None else "—"
        pe = f"{p.pe:.1f}" if p.pe is not None else "—"
        circ = f"{p.circ_ratio*100:.0f}%" if p.circ_ratio is not None else "—"
        mcap = f"${p.mcap/1e6:.1f}M" if p.mcap else "—"
        tvl = f"${p.tvl/1e6:.1f}M" if p.tvl else "—"
        rev = f"${p.rev_30d/1e3:.0f}K" if p.rev_30d else "$0"
        lines.append(
            f"{i+1:<3}{p.name:<22}{p.score:<5}{p.rootdata_score:>4}{p.market_score:>4}{p.onchain_score:>4}{mcap:>9}{tvl:>10}{pb:>6}{pe:>7}{circ:>6}{rev:>9}"
        )
    return "\n".join(lines)
