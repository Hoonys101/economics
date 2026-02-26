import unittest
from unittest.mock import MagicMock, PropertyMock
from simulation.systems.analytics_system import AnalyticsSystem
from simulation.core_agents import Household
from simulation.firms import Firm
from simulation.models import Transaction
from simulation.dtos import AgentStateData, EconomicIndicatorData
from modules.household.dtos import HouseholdSnapshotDTO, EconStateDTO, BioStateDTO, SocialStateDTO
from modules.simulation.dtos.api import FirmStateDTO
from modules.system.api import DEFAULT_CURRENCY

class TestAnalyticsSystemPurity(unittest.TestCase):
    def setUp(self):
        self.analytics_system = AnalyticsSystem()
        self.world_state = MagicMock()
        self.world_state.run_id = "test_run"
        self.world_state.time = 100
        self.world_state.transactions = []
        self.world_state.tracker = MagicMock()
        self.world_state.tracker.get_latest_indicators.return_value = {}
        self.world_state.household_time_allocation = {}

    def test_aggregate_tick_data_uses_snapshots_only(self):
        """
        Verify that aggregate_tick_data does NOT call direct state accessors on Agents,
        but instead relies on create_snapshot_dto() or get_state_dto().
        """
        # Mock Household
        household = MagicMock(spec=Household)
        household.id = 1
        household.is_active = True

        # Configure Snapshot Mock
        snapshot = MagicMock(spec=HouseholdSnapshotDTO)
        snapshot.econ_state = MagicMock(spec=EconStateDTO)
        snapshot.econ_state.is_employed = True
        snapshot.econ_state.employer_id = 101
        snapshot.econ_state.inventory = {"food": 10.0}
        snapshot.econ_state.assets = {DEFAULT_CURRENCY: 5000}
        snapshot.econ_state.labor_income_this_tick_pennies = 1000
        snapshot.econ_state.capital_income_this_tick_pennies = 500

        snapshot.bio_state = MagicMock(spec=BioStateDTO)
        snapshot.bio_state.needs = {"survival": 0.5, "labor_need": 0.2}
        snapshot.bio_state.generation = 1

        household.create_snapshot_dto.return_value = snapshot
        household.config = MagicMock()
        household.config.SHOPPING_HOURS = 2.0
        household.config.HOURS_PER_TICK = 24.0

        # Mock Firm
        firm = MagicMock(spec=Firm)
        firm.id = 101
        firm.is_active = True

        # Configure Firm State DTO Mock
        firm_state = MagicMock(spec=FirmStateDTO)
        firm_state.production = MagicMock()
        firm_state.production.inventory = {"food": 100.0}
        firm_state.production.current_production = 50.0
        firm_state.hr = MagicMock()
        firm_state.hr.employees = [1]
        firm_state.finance = MagicMock()
        firm_state.finance.assets = {DEFAULT_CURRENCY: 100000} # Mocking property access if needed
        # Or if it uses balance dict

        firm.get_state_dto.return_value = firm_state

        # Setup World State Agents
        self.world_state.agents = {1: household, 101: firm}
        self.world_state.households = [household]

        # --- EXECUTE ---
        self.analytics_system.aggregate_tick_data(self.world_state)

        # --- VERIFY ---

        # 1. Household: Ensure create_snapshot_dto was called
        household.create_snapshot_dto.assert_called()

        # 2. Firm: Ensure get_state_dto was called
        firm.get_state_dto.assert_called_once()

        # 3. FORBIDDEN CALLS: Ensure get_assets_by_currency is NOT called
        # This is the key "Purity" check.
        household.get_assets_by_currency.assert_not_called()
        firm.get_assets_by_currency.assert_not_called()

        # 4. Ensure properties like 'needs' are not accessed directly on agent if they exist as props
        # (Though they are usually on bio_component, legacy accessors might exist)
        # We can't easily assert property access wasn't made unless we mock them as PropertyMock and check call_count.
        # But asserting get_assets_by_currency_not_called is a strong signal for now given the code structure.

if __name__ == '__main__':
    unittest.main()
