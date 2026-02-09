import pytest
from unittest.mock import Mock, MagicMock
from simulation.agents.government import Government
from modules.government.dtos import GovernmentStateDTO, PolicyDecisionDTO, ExecutionResultDTO
from modules.government.engines.decision_engine import GovernmentDecisionEngine
from modules.government.engines.execution_engine import PolicyExecutionEngine
from simulation.dtos.api import MarketSnapshotDTO
from modules.system.api import DEFAULT_CURRENCY
from simulation.ai.enums import PolicyActionTag

class TestGovernmentRefactor:

    @pytest.fixture
    def mock_config(self):
        config = MagicMock()
        config.GOVERNMENT_POLICY_MODE = "TAYLOR_RULE"
        config.INCOME_TAX_RATE = 0.1
        config.CORPORATE_TAX_RATE = 0.2
        config.ENABLE_FISCAL_STABILIZER = True
        config.AUTO_COUNTER_CYCLICAL_ENABLED = True
        config.FISCAL_SENSITIVITY_ALPHA = 0.5
        config.TICKS_PER_YEAR = 100
        config.CB_INFLATION_TARGET = 0.02
        config.ANNUAL_WEALTH_TAX_RATE = 0.02
        config.WEALTH_TAX_THRESHOLD = 1000.0
        return config

    @pytest.fixture
    def government(self, mock_config):
        gov = Government(id=1, initial_assets=100000.0, config_module=mock_config)
        gov.settlement_system = MagicMock()
        gov.settlement_system.transfer.return_value = True
        gov.finance_system = MagicMock()
        return gov

    def test_decision_engine_taylor_rule(self, mock_config):
        """Verify DecisionEngine produces correct PolicyDecisionDTO."""
        engine = GovernmentDecisionEngine(mock_config)

        state = GovernmentStateDTO(
            tick=1,
            assets={"USD": 1000.0},
            total_debt=0.0,
            income_tax_rate=0.1,
            corporate_tax_rate=0.2,
            fiscal_policy=MagicMock(),
            ruling_party=MagicMock(),
            approval_rating=0.5,
            potential_gdp=1000.0
        )

        # Scenario: Recession (GDP < Potential)
        market_snapshot = MarketSnapshotDTO(
            tick=1,
            market_signals={},
            market_data={"total_production": 800.0}
        )

        decision = engine.decide(state, market_snapshot, MagicMock())

        assert isinstance(decision, PolicyDecisionDTO)
        assert decision.action_tag == PolicyActionTag.KEYNESIAN_FISCAL # Stimulus
        assert decision.parameters["income_tax_rate"] < 0.1 # Tax Cut
        assert "potential_gdp" in decision.parameters

    def test_execution_engine_state_update(self, mock_config):
        """Verify ExecutionEngine updates state based on decision."""
        engine = PolicyExecutionEngine()

        decision = PolicyDecisionDTO(
            action_tag=PolicyActionTag.KEYNESIAN_FISCAL,
            parameters={
                "income_tax_rate": 0.08,
                "potential_gdp": 1010.0,
                "fiscal_stance": 0.1
            }
        )

        state = GovernmentStateDTO(tick=1, assets={}, total_debt=0.0, income_tax_rate=0.1, corporate_tax_rate=0.2, fiscal_policy=MagicMock(), ruling_party=MagicMock(), approval_rating=0.5)

        context = MagicMock()

        result = engine.execute(decision, state, [], {}, context)

        assert isinstance(result, ExecutionResultDTO)
        assert result.state_updates["income_tax_rate"] == 0.08
        assert result.state_updates["potential_gdp"] == 1010.0
        assert result.state_updates["fiscal_stance"] == 0.1

    def test_orchestrator_integration(self, government):
        """Verify Government orchestrator integrates engines correctly."""
        # Setup
        government.potential_gdp = 1000.0
        government.income_tax_rate = 0.1

        market_data = {"total_production": 800.0} # Recession

        # Run Decision Logic
        government.make_policy_decision(market_data, 1, MagicMock())

        # Assert State Update
        assert government.income_tax_rate < 0.1
        assert government.potential_gdp > 0 # EMA updated

        # Assert Execution Log (Shadow Log)
        # Note: Shadow log logic is separate, we verified state update logic.

    def test_social_policy_execution(self, government):
        """Verify social policy execution flow."""
        # Setup Agents
        rich_agent = MagicMock()
        rich_agent.id = 101
        rich_agent.is_active = True
        rich_agent.assets = {DEFAULT_CURRENCY: 2000.0} # Taxable

        agents = [rich_agent]
        market_data = {
            "goods_market": {
                "basic_food_current_sell_price": 10.0
            }
        }

        # Mock Config for WelfareManager
        government.config_module.HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK = 1.0
        # Ensure ratios are floats, not mocks
        government.config_module.UNEMPLOYMENT_BENEFIT_RATIO = 0.5

        # Execute
        government.run_welfare_check(agents, market_data, 100)

        # Verify Tax Collection
        # Expect 1 transfer call: Rich -> Gov
        calls = government.settlement_system.transfer.call_args_list
        assert len(calls) == 1

        args, _ = calls[0]
        payer, payee, amount, memo = args[0], args[1], args[2], args[3]

        assert payer == rich_agent
        assert payee == government # Should be the object!
        assert amount > 0
