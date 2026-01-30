import unittest
from unittest.mock import MagicMock
import math
from modules.government.components.monetary_policy_manager import MonetaryPolicyManager
from simulation.dtos.api import MarketSnapshotDTO

class TestMonetaryPolicyManager(unittest.TestCase):
    def setUp(self):
        self.config = MagicMock()
        self.config.CB_INFLATION_TARGET = 0.02
        self.config.CB_TAYLOR_ALPHA = 0.5
        self.config.CB_TAYLOR_BETA = 0.5
        self.config.CB_NEUTRAL_RATE = 0.02
        self.manager = MonetaryPolicyManager(self.config)

    def test_equilibrium(self):
        # Inflation at target (2%), Output at potential
        snapshot = MagicMock(spec=MarketSnapshotDTO)
        snapshot.inflation_rate = 0.02
        snapshot.nominal_gdp = 1000.0
        snapshot.potential_gdp = 1000.0
        snapshot.unemployment_rate = 0.05

        # i = r* + pi + alpha(pi-pi*) + beta(y-y*)
        # i = 0.02 + 0.02 + 0.5(0) + 0.5(0) = 0.04
        policy = self.manager.determine_monetary_stance(snapshot)
        self.assertAlmostEqual(policy.target_interest_rate, 0.04)

    def test_high_inflation(self):
        # Inflation 5%, Output at potential
        snapshot = MagicMock(spec=MarketSnapshotDTO)
        snapshot.inflation_rate = 0.05
        snapshot.nominal_gdp = 1000.0
        snapshot.potential_gdp = 1000.0

        # i = 0.02 + 0.05 + 0.5(0.05 - 0.02) + 0
        # i = 0.07 + 0.5(0.03) = 0.07 + 0.015 = 0.085
        policy = self.manager.determine_monetary_stance(snapshot)
        self.assertAlmostEqual(policy.target_interest_rate, 0.085)

    def test_recession(self):
        # Inflation 1%, GDP 900 vs Potential 1000
        snapshot = MagicMock(spec=MarketSnapshotDTO)
        snapshot.inflation_rate = 0.01
        snapshot.nominal_gdp = 900.0
        snapshot.potential_gdp = 1000.0

        # Output gap = ln(900) - ln(1000) approx -0.10536
        gap = math.log(900) - math.log(1000)
        expected_rate = 0.02 + 0.01 + 0.5 * (0.01 - 0.02) + 0.5 * gap
        # expected_rate approx 0.03 - 0.005 - 0.05268 = -0.02768
        # ZLB -> 0.0

        policy = self.manager.determine_monetary_stance(snapshot)
        self.assertEqual(policy.target_interest_rate, 0.0)

    def test_overheating_economy(self):
        # Inflation 4%, GDP 1100 vs Potential 1000
        snapshot = MagicMock(spec=MarketSnapshotDTO)
        snapshot.inflation_rate = 0.04
        snapshot.nominal_gdp = 1100.0
        snapshot.potential_gdp = 1000.0

        gap = math.log(1100) - math.log(1000)
        expected_rate = 0.02 + 0.04 + 0.5 * (0.04 - 0.02) + 0.5 * gap

        policy = self.manager.determine_monetary_stance(snapshot)
        self.assertAlmostEqual(policy.target_interest_rate, expected_rate)

    def test_missing_data_defaults(self):
        snapshot = MagicMock(spec=MarketSnapshotDTO)
        snapshot.inflation_rate = None
        snapshot.nominal_gdp = None
        snapshot.potential_gdp = None

        # Defaults to 0
        # i = 0.02 + 0 + 0.5(0 - 0.02) + 0
        # i = 0.02 - 0.01 = 0.01
        policy = self.manager.determine_monetary_stance(snapshot)
        self.assertAlmostEqual(policy.target_interest_rate, 0.01)

    def test_gdp_zero_or_negative(self):
        # Test 1: GDP 0 -> output_gap should be 0 (log(0) handled)
        snapshot = MagicMock(spec=MarketSnapshotDTO)
        snapshot.inflation_rate = 0.02
        snapshot.nominal_gdp = 0.0
        snapshot.potential_gdp = 1000.0

        # i = 0.02 + 0.02 + 0 + 0 = 0.04
        policy = self.manager.determine_monetary_stance(snapshot)
        self.assertAlmostEqual(policy.target_interest_rate, 0.04)

        # Test 2: Potential GDP 0 -> output_gap should be 0
        snapshot.nominal_gdp = 1000.0
        snapshot.potential_gdp = 0.0
        policy = self.manager.determine_monetary_stance(snapshot)
        self.assertAlmostEqual(policy.target_interest_rate, 0.04)

        # Test 3: Negative GDP (Impossible but robust check)
        snapshot.nominal_gdp = -100.0
        snapshot.potential_gdp = 1000.0
        policy = self.manager.determine_monetary_stance(snapshot)
        self.assertAlmostEqual(policy.target_interest_rate, 0.04)
