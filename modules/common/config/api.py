"""
API for the Configuration Management System.

Defines the interface for accessing and updating configuration, as well as the
Data Transfer Objects (DTOs) used to represent domain-specific configurations.
"""
from abc import ABC, abstractmethod
from typing import Type, TypeVar, Dict, Any, List, Tuple
from dataclasses import dataclass, replace as dataclass_replace

# Generic TypeVar for Config DTOs to ensure type safety.
T_ConfigDTO = TypeVar("T_ConfigDTO", bound="BaseConfigDTO")


@dataclass(frozen=True)
class BaseConfigDTO:
    """
    Base class for all configuration DTOs. `frozen=True` makes instances
    immutable, ensuring that configuration is not modified accidentally.
    Updates must go through the IConfigManager.
    """
    pass

@dataclass(frozen=True)
class GovernmentConfigDTO(BaseConfigDTO):
    """Configuration for government policies."""
    income_tax_rate: float
    corporate_tax_rate: float
    sales_tax_rate: float
    inheritance_tax_rate: float
    wealth_tax_threshold: float
    annual_wealth_tax_rate: float
    tax_brackets: List[Tuple[float, float]]
    gov_action_interval: int
    rd_subsidy_rate: float
    infrastructure_investment_cost: float
    infrastructure_tfp_boost: float
    unemployment_benefit_ratio: float
    stimulus_trigger_gdp_drop: float
    deficit_spending_enabled: bool
    deficit_spending_limit_ratio: float
    emergency_budget_multiplier_cap: float
    normal_budget_multiplier_cap: float
    fiscal_sensitivity_alpha: float
    potential_gdp_window: int
    tax_rate_min: float
    tax_rate_max: float
    tax_rate_base: float
    budget_allocation_min: float
    budget_allocation_max: float
    debt_ceiling_ratio: float
    fiscal_stance_expansion_threshold: float
    fiscal_stance_contraction_threshold: float
    fiscal_model: str
    public_edu_budget_ratio: float
    government_policy_mode: str
    target_inflation_rate: float
    target_unemployment_rate: float
    rl_learning_rate: float
    rl_discount_factor: float
    automation_tax_rate: float
    policy_actuator_step_sizes: Tuple[float, float, float]
    policy_actuator_bounds: Dict[str, Tuple[float, float]]


@dataclass(frozen=True)
class FinanceConfigDTO(BaseConfigDTO):
    """Configuration for the financial system."""
    initial_base_annual_rate: float
    bank_margin: float
    credit_spread_base: float
    loan_default_term: int
    ticks_per_year: float
    default_mortgage_rate: float
    bank_deposit_margin: float
    bank_credit_spread_base: float
    default_loan_term_ticks: int
    bank_solvency_buffer: float
    default_mortgage_interest_rate: float
    reserve_req_ratio: float
    initial_money_supply: float
    gold_standard_mode: bool
    neutral_real_rate: float
    dsr_critical_threshold: float
    cb_update_interval: int
    cb_inflation_target: float
    cb_taylor_alpha: float
    cb_taylor_beta: float


@dataclass(frozen=True)
class StockMarketConfigDTO(BaseConfigDTO):
    """Configuration for the stock market."""
    stock_market_enabled: bool
    stock_price_limit_rate: float
    stock_transaction_fee_rate: float
    ipo_initial_shares: float
    stock_price_method: str
    stock_book_value_multiplier: float
    stock_min_order_quantity: float
    stock_order_expiry_ticks: int
    seo_trigger_ratio: float
    seo_max_sell_ratio: float
    startup_min_capital: float
    startup_initial_shares: float
    startup_probability: float
    dividend_rate: float
    dividend_rate_min: float
    dividend_rate_max: float
    bailout_repayment_ratio: float
    friendly_merger_premium: float
    hostile_takeover_premium: float
    hostile_takeover_success_prob: float
    merger_employee_retention_rates: Tuple[float, float]
    ma_enabled: bool
    valuation_per_multiplier: float
    min_acquisition_cash_ratio: float
    liquidation_discount_rate: float
    bankruptcy_consecutive_loss_ticks: int
    bankruptcy_xp_penalty: float
    credit_recovery_ticks: int
    startup_cost: float
    startup_capital_multiplier: float
    entrepreneurship_spirit: float


@dataclass(frozen=True)
class HouseholdConfigDTO(BaseConfigDTO):
    """Configuration for household behavior."""
    initial_household_assets_mean: float
    initial_household_assets_range: float
    initial_household_liquidity_need_mean: float
    initial_household_liquidity_need_range: float
    household_min_food_inventory: float
    target_food_buffer_quantity: float
    # skipping complex dicts like INITIAL_HOUSEHOLD_NEEDS_MEAN for now or simplifying
    household_min_wage_demand: float
    household_reservation_price_base: float
    household_need_price_multiplier: float
    household_asset_price_multiplier: float
    household_price_elasticity_factor: float
    household_stockpiling_bonus_factor: float
    household_max_purchase_quantity: float
    household_food_price_elasticity: float
    household_food_stockpile_target_ticks: int
    household_food_consumption_per_tick: float
    household_min_food_inventory_ticks: int
    survival_need_consumption_threshold: float
    food_consumption_quantity: float
    food_consumption_max_per_tick: float
    food_purchase_max_per_tick: float
    survival_need_death_threshold: float
    assets_death_threshold: float
    household_death_turns_threshold: int
    household_investment_budget_ratio: float
    household_min_assets_for_investment: float
    stock_sell_profit_threshold: float
    stock_buy_discount_threshold: float
    stock_investment_diversification_count: int
    stock_investment_equity_delta_threshold: float
    panic_selling_asset_threshold: float
    reproduction_age_start: int
    reproduction_age_end: int
    childcare_time_required: float
    housework_base_hours: float
    social_capillarity_cost: float
    unnamed_child_mortality_rate: float
    child_monthly_cost: float
    opportunity_cost_factor: float
    raising_years: int
    child_emotional_value_base: float
    old_age_support_rate: float
    support_years: int
    household_low_asset_threshold: float
    household_low_asset_wage: float
    household_default_wage: float
    household_assets_threshold_for_labor_supply: float
    forced_labor_exploration_probability: float
    default_fallback_price: float


class IConfigManager(ABC):
    """
    An interface for a centralized configuration management system.

    It is responsible for loading, providing, and updating domain-specific
    configuration DTOs. This approach avoids a monolithic config file and
    prevents circular dependencies.
    """

    @abstractmethod
    def get_config(self, domain_name: str, dto_class: Type[T_ConfigDTO]) -> T_ConfigDTO:
        """
        Retrieves the configuration for a specific domain as a typed DTO.

        Args:
            domain_name: The name of the configuration domain (e.g., "finance", "government").
            dto_class: The dataclass type to which the configuration should be deserialized.

        Returns:
            An immutable instance of the requested configuration DTO.

        Raises:
            KeyError: If the domain does not exist.
            ValidationError: If the loaded data fails to deserialize to the DTO.
        """
        ...

    @abstractmethod
    def update_config(self, domain_name: str, new_config_dto: BaseConfigDTO) -> None:
        """
        Updates the configuration for a specific domain at runtime.

        This method is crucial for systems like the Politics module to enact
        policy changes without creating circular dependencies. The caller is
        responsible for constructing and passing the new DTO.

        Args:
            domain_name: The name of the configuration domain to update.
            new_config_dto: The new configuration DTO instance.
        """
        ...

    @abstractmethod
    def get_all_configs(self) -> Dict[str, BaseConfigDTO]:
        """
        Retrieves all loaded configuration domains and their DTOs.

        Returns:
            A dictionary mapping domain names to their configuration DTOs.
        """
        ...

    @abstractmethod
    def register_domain(self, domain_name: str, dto_class: Type[T_ConfigDTO], default_data: Dict[str, Any]) -> None:
        """
        Registers a new configuration domain, its DTO class, and default values.
        This allows modules to self-register their configuration needs.

        Args:
            domain_name: The unique name for the configuration domain.
            dto_class: The dataclass representing the domain's configuration.
            default_data: A dictionary with the default configuration values.
        """
        ...
