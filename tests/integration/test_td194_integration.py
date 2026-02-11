import pytest
from unittest.mock import Mock, MagicMock
from simulation.core_agents import Household
from simulation.firms import Firm
from simulation.dtos.api import DecisionInputDTO
from modules.system.api import MarketSnapshotDTO, MarketSignalDTO, HousingMarketSnapshotDTO, LoanMarketSnapshotDTO, LaborMarketSnapshotDTO
from modules.simulation.api import AgentCoreConfigDTO
from tests.utils.factories import create_household_config_dto, create_firm_config_dto
from simulation.models import Talent, Order
from simulation.ai.api import Personality

class TestTD194Integration:
    def test_household_make_decision_integrity(self):
        # 1. Setup Household
        config = create_household_config_dto()

        # Mock Decision Engine
        decision_engine = MagicMock()
        decision_engine.make_decisions.return_value = ([], (Mock(), Mock())) # orders, metadata

        # Talent needs to be valid
        talent = Talent(base_learning_rate=0.5, max_potential={})

        core_config = AgentCoreConfigDTO(
            id=1,
            name="Household_1",
            value_orientation="neutral",
            initial_needs={"survival": 0.5},
            logger=MagicMock(),
            memory_interface=None
        )

        household = Household(
            core_config=core_config,
            engine=decision_engine,
            talent=talent,
            goods_data=[],
            personality=Personality.BALANCED,
            config_dto=config
        )
        household.deposit(100000)

        # 2. Setup Input DTO
        market_snapshot = MarketSnapshotDTO(
            tick=1,
            market_signals={},
            market_data={},
            housing=HousingMarketSnapshotDTO(
                for_sale_units=[],
                units_for_rent=[],
                avg_rent_price=100.0,
                avg_sale_price=20000.0
            ),
            loan=LoanMarketSnapshotDTO(interest_rate=0.05),
            labor=LaborMarketSnapshotDTO(avg_wage=10.0)
        )

        input_dto = DecisionInputDTO(
            goods_data=[],
            market_data={},
            current_time=1,
            market_snapshot=market_snapshot
        )

        # 3. Execution
        orders, meta = household.make_decision(input_dto)

        # 4. Verification
        assert isinstance(orders, list)

    def test_firm_make_decision_integrity(self):
        # 1. Setup Firm
        config = create_firm_config_dto()

        decision_engine = MagicMock()
        decision_engine.make_decisions.return_value = ([], Mock())

        core_config = AgentCoreConfigDTO(
            id=1,
            name="Firm_1",
            value_orientation="profit",
            initial_needs={"liquidity_need": 1000.0},
            logger=MagicMock(),
            memory_interface=None
        )

        firm = Firm(
            core_config=core_config,
            engine=decision_engine,
            specialization="goods",
            productivity_factor=1.0,
            config_dto=config
        )
        firm.deposit(1000000)

        # 2. Setup Input DTO
        signals = {
            "goods": MarketSignalDTO(
                market_id="goods",
                item_id="goods",
                best_bid=10.0,
                best_ask=12.0,
                last_traded_price=11.0,
                last_trade_tick=1,
                price_history_7d=[],
                volatility_7d=0.0,
                order_book_depth_buy=5,
                order_book_depth_sell=5,
                total_bid_quantity=100.0,
                total_ask_quantity=50.0,
                is_frozen=False
            )
        }

        market_snapshot = MarketSnapshotDTO(
            tick=1,
            market_signals=signals,
            market_data={},
            housing=None,
            loan=None,
            labor=None
        )

        input_dto = DecisionInputDTO(
            goods_data=[],
            market_data={},
            current_time=1,
            market_snapshot=market_snapshot
        )

        # 3. Execution
        orders, meta = firm.make_decision(input_dto)

        # 4. Verification
        assert isinstance(orders, list)
