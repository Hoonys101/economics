import pytest
from unittest.mock import MagicMock, call
from simulation.factories.firm_factory import FirmFactory
from simulation.systems.bootstrapper import Bootstrapper
from modules.simulation.api import IBirthContext, IFinanceTickContext, FirmConfigDTO
from modules.system.api import IAgentRegistry
from modules.finance.api import IMonetaryAuthority, ICentralBank
from simulation.ai.enums import Personality

class TestFirmFactoryAtomicRegistration:

    @pytest.fixture
    def mock_birth_context(self):
        context = MagicMock(spec=IBirthContext)
        context.next_agent_id = 999
        context.agent_registry = MagicMock(spec=IAgentRegistry)
        context.logger = MagicMock()
        return context

    @pytest.fixture
    def mock_finance_context(self):
        context = MagicMock(spec=IFinanceTickContext)
        context.current_time = 10
        context.settlement_system = MagicMock(spec=IMonetaryAuthority)
        context.central_bank = MagicMock(spec=ICentralBank)
        return context

    def test_firm_atomic_registration(self, mock_birth_context, mock_finance_context):
        """
        Verify `create_firm` first calls `agent_registry.register` BEFORE it accesses `settlement_system.register_account`.
        """
        from tests.utils.factories import create_firm_config_dto
        config_dto = create_firm_config_dto()
        config_dto.specialization = "food"
        config_dto.productivity_factor = 1.0
        config_dto.sector = "FOOD"
        factory = FirmFactory(config_module=MagicMock())

        firm = factory.create_firm(
            name="TestFirm",
            config_dto=config_dto,
            birth_context=mock_birth_context,
            finance_context=mock_finance_context,
            specialization="food",
            decision_engine=MagicMock()
        )

        # Ensure Agent ID is taken from birth context
        assert firm.id == 999

        # Ensure global registration happened
        mock_birth_context.agent_registry.register.assert_called_once_with(firm)

        # Ensure settlement system registered the account
        mock_finance_context.settlement_system.register_account.assert_called_once()

        # Verify order of operations (We want to ensure registry comes before bank account)
        # Using mock_calls across independent mocks isn't natively ordered via `.mock_calls` unless attached to a parent.
        # But we can simulate a manager mock to track order:
        manager = MagicMock()
        manager.attach_mock(mock_birth_context.agent_registry, "registry")
        manager.attach_mock(mock_finance_context.settlement_system, "settlement")

        # Re-run to capture order
        mock_birth_context.agent_registry.reset_mock()
        mock_finance_context.settlement_system.reset_mock()

        factory.create_firm(
            name="TestFirm2",
            config_dto=config_dto,
            birth_context=mock_birth_context,
            finance_context=mock_finance_context,
            specialization="food",
            decision_engine=MagicMock()
        )

        from unittest.mock import ANY
        expected_calls = [
            call.registry.register(ANY),
            call.settlement.register_account(ANY, ANY)
        ]

        # assert has_calls matches the order of the provided list
        manager.assert_has_calls(expected_calls, any_order=False)


class TestBootstrapperProtocolPurity:
    def test_bootstrapper_protocol_purity(self):
        """
        Instantiate `Bootstrapper.inject_liquidity_for_firm` with a dummy class that has `.create_and_transfer`
        but is not registered as an `ISettlementSystem` (`IMonetaryAuthority`). Assert that it raises `TypeError`.
        """
        class FakeSettlementSystem:
            def create_and_transfer(self, *args, **kwargs):
                return True

        fake_system = FakeSettlementSystem()
        mock_central_bank = MagicMock(spec=ICentralBank)
        firm = MagicMock()

        with pytest.raises(TypeError) as exc:
            Bootstrapper.inject_liquidity_for_firm(firm, config=MagicMock(), settlement_system=fake_system, central_bank=mock_central_bank)

        assert "must implement ISettlementSystem" in str(exc.value)
