from typing import Dict, Any, Optional
from unittest.mock import MagicMock

from modules.simulation.dtos.api import FirmStateDTO
from modules.simulation.dtos.api import FinanceStateDTO, ProductionStateDTO, SalesStateDTO, HRStateDTO
from modules.household.dtos import HouseholdStateDTO
from simulation.ai.enums import Personality
from tests.utils.factories import create_firm_config_dto, create_household_config_dto
from modules.system.api import DEFAULT_CURRENCY

class MockFactory:
    """Factory for creating structured Mocks and DTOs for testing."""

    @staticmethod
    def create_firm_state_dto(
        id: int = 1,
        is_active: bool = True,
        # Finance
        balance: float = 1000.0,
        revenue_this_turn: float = 0.0,
        expenses_this_tick: float = 0.0,
        consecutive_loss_turns: int = 0,
        profit_history: Optional[list] = None,
        altman_z_score: float = 3.0,
        valuation: float = 1000.0,
        total_shares: float = 100.0,
        treasury_shares: float = 0.0,
        dividend_rate: float = 0.1,
        is_publicly_traded: bool = True,
        # Production
        current_production: float = 0.0,
        productivity_factor: float = 1.0,
        production_target: float = 100.0,
        capital_stock: float = 100.0,
        base_quality: float = 1.0,
        automation_level: float = 0.0,
        specialization: str = "food",
        inventory: Optional[Dict[str, float]] = None,
        input_inventory: Optional[Dict[str, float]] = None,
        inventory_quality: Optional[Dict[str, float]] = None,
        # Sales
        inventory_last_sale_tick: Optional[Dict[str, int]] = None,
        price_history: Optional[Dict[str, float]] = None,
        brand_awareness: float = 0.0,
        perceived_quality: float = 1.0,
        marketing_budget: float = 0.0,
        # HR
        employees: Optional[list] = None,
        employees_data: Optional[Dict[int, Any]] = None,
        # Agent Data
        agent_data: Optional[Dict[str, Any]] = None,
        system2_guidance: Optional[Dict[str, Any]] = None,
        # Parity
        sentiment_index: float = 0.5
    ) -> FirmStateDTO:
        """Creates a properly structured FirmStateDTO."""

        finance_dto = FinanceStateDTO(
            balance=balance,
            revenue_this_turn=revenue_this_turn,
            expenses_this_tick=expenses_this_tick,
            consecutive_loss_turns=consecutive_loss_turns,
            profit_history=profit_history or [],
            altman_z_score=altman_z_score,
            valuation=valuation,
            total_shares=total_shares,
            treasury_shares=treasury_shares,
            dividend_rate=dividend_rate,
            is_publicly_traded=is_publicly_traded
        )

        production_dto = ProductionStateDTO(
            current_production=current_production,
            productivity_factor=productivity_factor,
            production_target=production_target,
            capital_stock=capital_stock,
            base_quality=base_quality,
            automation_level=automation_level,
            specialization=specialization,
            inventory=inventory or {},
            input_inventory=input_inventory or {},
            inventory_quality=inventory_quality or {}
        )

        sales_dto = SalesStateDTO(
            inventory_last_sale_tick=inventory_last_sale_tick or {},
            price_history=price_history or {},
            brand_awareness=brand_awareness,
            perceived_quality=perceived_quality,
            marketing_budget=marketing_budget
        )

        hr_dto = HRStateDTO(
            employees=employees or [],
            employees_data=employees_data or {}
        )

        return FirmStateDTO(
            id=id,
            is_active=is_active,
            finance=finance_dto,
            production=production_dto,
            sales=sales_dto,
            hr=hr_dto,
            agent_data=agent_data or {},
            system2_guidance=system2_guidance or {},
            sentiment_index=sentiment_index
        )

    @staticmethod
    def create_mock_firm(
        id: int = 1,
        state_dto: Optional[FirmStateDTO] = None,
        config: Any = None,
        **kwargs
    ) -> MagicMock:
        """Creates a MagicMock representing a Firm agent."""
        firm = MagicMock()
        firm.id = id

        if state_dto is None:
            state_dto = MockFactory.create_firm_state_dto(id=id, **kwargs)

        # Setup state access
        firm.get_state_dto.return_value = state_dto
        firm.state = state_dto # Direct access compatibility

        # Setup config
        if config is None:
            config = MagicMock()
            # Default mock config values
            config.profit_history_ticks = 10
            config.overstock_threshold = 1.5
            config.understock_threshold = 0.5
            config.production_adjustment_factor = 0.1
            config.firm_min_production_target = 10
            config.firm_max_production_target = 1000
            config.firm_min_employees = 1
            config.firm_max_employees = 100
            config.base_wage = 100
            config.wage_profit_sensitivity = 0.1
            config.max_wage_premium = 0.5
            config.goods_market_sell_price = 10
            config.price_adjustment_exponent = 0.5
            config.price_adjustment_factor = 0.1
            config.min_sell_price = 1
            config.max_sell_price = 1000
            config.max_sell_quantity = 100

        firm.config = config

        # Mock other common attributes if needed
        firm.specialization = state_dto.production.specialization

        return firm

    @staticmethod
    def create_household_state_dto(
        id: int = 1,
        assets: float = 1000.0,
        inventory: Optional[Dict[str, float]] = None,
        needs: Optional[Dict[str, float]] = None,
        is_employed: bool = False,
        current_wage: float = 0.0,
        wage_modifier: float = 1.0,
        durable_assets: Optional[list] = None,
        perceived_prices: Optional[Dict[str, float]] = None,
        agent_data: Optional[Dict[str, Any]] = None,
        personality: Personality = Personality.BALANCED,
        **kwargs
    ) -> HouseholdStateDTO:
        """Creates a HouseholdStateDTO with sensible defaults."""
        return HouseholdStateDTO(
            id=id,
            assets={DEFAULT_CURRENCY: int(assets)},
            inventory=inventory or {},
            needs=needs or {"survival": 0.5, "leisure": 0.5},
            preference_asset=kwargs.get("preference_asset", 1.0),
            preference_social=kwargs.get("preference_social", 1.0),
            preference_growth=kwargs.get("preference_growth", 1.0),
            personality=personality,
            durable_assets=durable_assets or [],
            expected_inflation=kwargs.get("expected_inflation", {}),
            is_employed=is_employed,
            current_wage_pennies=int(current_wage),
            wage_modifier=wage_modifier,
            is_homeless=kwargs.get("is_homeless", False),
            residing_property_id=kwargs.get("residing_property_id"),
            owned_properties=kwargs.get("owned_properties", []),
            portfolio_holdings=kwargs.get("portfolio_holdings", {}),
            risk_aversion=kwargs.get("risk_aversion", 1.0),
            agent_data=agent_data or {},
            perceived_prices=perceived_prices or {},
            conformity=kwargs.get("conformity", 0.5),
            social_rank=kwargs.get("social_rank", 0.5),
            approval_rating=kwargs.get("approval_rating", 1),
            demand_elasticity=kwargs.get("demand_elasticity", 1.0),
            monthly_income_pennies=int(kwargs.get("monthly_income", 0.0)),
            monthly_debt_payments_pennies=int(kwargs.get("monthly_debt_payments", 0.0))
        )

    @staticmethod
    def create_mock_household(
        id: int = 1,
        state_dto: Optional[HouseholdStateDTO] = None,
        config: Any = None,
        **kwargs
    ) -> MagicMock:
        """Creates a MagicMock representing a Household agent."""
        household = MagicMock()
        household.id = id

        if state_dto is None:
            state_dto = MockFactory.create_household_state_dto(id=id, **kwargs)

        household.state = state_dto # Access pattern: agent.state
        household.get_state_dto.return_value = state_dto

        if config is None:
             # Can use the real config DTO factory if simple enough
             config = create_household_config_dto()

        household.config = config

        return household
