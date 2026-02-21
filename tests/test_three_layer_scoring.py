import unittest

from gem_screener import scorer
from gem_screener.models import Protocol


class ThreeLayerScoringTests(unittest.TestCase):
    def test_three_layer_score_components_present(self):
        p = Protocol(
            name="Test",
            slug="test",
            category="Infra",
            chains=["Ethereum"],
            pb=0.4,
            pe=9,
            circ_ratio=0.85,
            rev_30d=800_000,
            tvl=80_000_000,
            tvl_change_7d=12,
            recent_tx_count=60,
            contract_verified=True,
            rootdata_total_funding=120_000_000,
            rootdata_investor_count=12,
            rootdata_tags=["Infra", "AI"],
        )

        total = scorer.score(p, rootdata_enabled=True)
        self.assertEqual(total, p.rootdata_score + p.market_score + p.onchain_score)
        self.assertGreater(p.rootdata_score, 0)
        self.assertGreater(p.market_score, 0)
        self.assertGreater(p.onchain_score, 0)
        self.assertIn("rootdata", p.score_breakdown)
        self.assertIn("market", p.score_breakdown)
        self.assertIn("onchain", p.score_breakdown)

    def test_rootdata_fallback_reweights_to_100(self):
        p = Protocol(
            name="NoRoot",
            slug="noroot",
            category="DeFi",
            chains=["Ethereum"],
            pb=0.8,
            pe=15,
            circ_ratio=0.75,
            rev_30d=200_000,
            tvl=20_000_000,
            tvl_change_7d=2,
            recent_tx_count=25,
            contract_verified=True,
        )

        total = scorer.score(p, rootdata_enabled=False)
        self.assertEqual(p.rootdata_score, 0)
        self.assertGreater(p.market_score, 0)
        self.assertGreater(p.onchain_score, 0)
        self.assertLessEqual(total, 100)
        self.assertIn("disabled", p.layer_reasons["rootdata"].lower())


if __name__ == "__main__":
    unittest.main()
