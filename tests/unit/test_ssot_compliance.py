import pytest
from unittest.mock import MagicMock, patch, ANY
from simulation.systems.inheritance_manager import InheritanceManager
from simulation.systems.settlement_system import SettlementSystem
from simulation.core_agents import Household
from simulation.agents.government import Government
from simulation.models import Transaction
from modules.system.api import DEFAULT_CURRENCY
from modules.finance.api import IFinancialEntity, IFinancialAgent
from simulation.dtos.api import SimulationState

class TestSSoTCompliance:

    @pytest.fixture
    def mock_simulation(self):
        sim = MagicMock(spec=SimulationState)
        sim.time = 100
        sim.agents = {}
        sim.real_estate_units = []
        sim.stock_market = MagicMock()
        sim.stock_market.get_daily_avg_price.return_value = 10.0

        # Setup TransactionProcessor
        sim.transaction_processor = MagicMock()
        sim.transaction_processor.execute.return_value = [MagicMock(success=True)]

        return sim

    @pytest.fixture
    def mock_household(self):
        # We don't use spec=Household because InheritanceManager accesses private _bio_state directly
        # and spec only sees class attributes/properties.
        h = MagicMock()
        h.id = 101
        h._econ_state = MagicMock()
        # Initial cash: 500.0 -> 50000 pennies ideally, but current code uses float assets
        h._econ_state.assets = {DEFAULT_CURRENCY: 500.0}
        h._econ_state.portfolio.holdings = {}
        h._bio_state.children_ids = []
        h._bio_state.is_active = False # Deceased
        return h

    @pytest.fixture
    def mock_government(self):
        g = MagicMock(spec=Government)
        g.id = 1
        return g

    def test_inheritance_transaction_pennies(self, mock_simulation, mock_household, mock_government):
        """
        Verifies that InheritanceManager creates transactions with total_pennies set.
        This test is expected to FAIL before the fix.
        """
        config = MagicMock()
        config.INHERITANCE_TAX_RATE = 0.1 # 10%
        config.INHERITANCE_DEDUCTION = 0.0 # No deduction

        manager = InheritanceManager(config)

        # Mock transaction processor to capture transactions
        captured_txs = []
        def capture(sim, txs):
            captured_txs.extend(txs)
            return [MagicMock(success=True)]

        mock_simulation.transaction_processor.execute.side_effect = capture

        # Execute
        manager.process_death(mock_household, mock_government, mock_simulation)

        # Verify Transactions
        # We expect a tax transaction.
        # Wealth = 500. Tax = 50.
        assert len(captured_txs) > 0
        tax_tx = next((tx for tx in captured_txs if tx.transaction_type == "tax"), None)
        assert tax_tx is not None

        # Check SSoT compliance
        # Before fix: total_pennies might be 0 or unset (default 0)
        # After fix: total_pennies should be int(50 * 100) = 5000

        print(f"Tax Transaction Total Pennies: {tax_tx.total_pennies}")
        assert tax_tx.total_pennies == 5000, f"Expected 5000 pennies, got {tax_tx.total_pennies}"
        assert isinstance(tax_tx.total_pennies, int)

    def test_settlement_protocol_compliance_get_balance(self):
        """
        Verifies that SettlementSystem.get_balance rejects invalid agents or returns 0 gracefully,
        but STRICTLY checks protocols.
        """
        settlement = SettlementSystem()
        settlement.agent_registry = MagicMock()

        # Case 1: Agent implements IFinancialEntity (balance_pennies)
        entity_agent = MagicMock(spec=IFinancialEntity)
        entity_agent.balance_pennies = 12345
        settlement.agent_registry.get_agent.return_value = entity_agent

        bal = settlement.get_balance(1, DEFAULT_CURRENCY)
        assert bal == 12345

        # Case 2: Agent implements IFinancialAgent (get_balance())
        financial_agent = MagicMock(spec=IFinancialAgent)
        financial_agent.get_balance.return_value = 67890
        settlement.agent_registry.get_agent.return_value = financial_agent

        bal = settlement.get_balance(2, DEFAULT_CURRENCY)
        assert bal == 67890

        # Case 3: Agent implements NEITHER (should return 0 or log warning)
        invalid_agent = MagicMock() # No spec
        # Ensure it doesn't accidentally pass checks
        del invalid_agent.balance_pennies
        del invalid_agent.get_balance

        settlement.agent_registry.get_agent.return_value = invalid_agent

        bal = settlement.get_balance(3, DEFAULT_CURRENCY)
        assert bal == 0
