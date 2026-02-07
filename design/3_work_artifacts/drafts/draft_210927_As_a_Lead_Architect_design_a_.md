```markdown
# Unified Configuration Protocol Specification (TD-265)

## 1. Overview
This document specifies the design for a new Unified Configuration Protocol. The primary goal is to resolve technical debt item `TD-265` by replacing brittle, untyped `getattr` calls with a robust, type-safe, and testable configuration access pattern.

This protocol centralizes the *loading* of configuration from source files (e.g., `.yaml`) but decentralizes its *distribution* through Dependency Injection (DI), adhering to the architectural constraints identified in the pre-flight audit.

## 2. Core Concepts & Architectural Principles

1.  **Dependency Injection (DI)**: Configuration will be explicitly passed into the constructors of the classes that need it. This eliminates "action at a distance" and makes dependencies clear. There will be **no global configuration singleton** or service locator.

2.  **Interface Segregation Principle (ISP)**: Monolithic DTOs like `HouseholdConfigDTO` and `FirmConfigDTO` will not be passed directly to components. Instead, components will depend on small, role-specific interfaces (`typing.Protocol`) that define only the configuration values they require. This reduces coupling and improves component isolation.

3.  **Centralized Loading, Decentralized Distribution**: A single `ConfigLoader` at the simulation's entry point will be responsible for reading all configuration sources and populating the master DTOs. A `ConfigurationProvider` will then use these master DTOs to provide the smaller, role-specific config interfaces to the rest of the application during object construction.

## 3. Detailed Design

### 3.1. Role-Based Configuration Protocols
The core of this design is the definition of small, granular `Protocol`s that represent a specific configuration need. These protocols are defined in `modules/system/config/api.py`.

**Example:** Instead of depending on the entire `HouseholdConfigDTO`, a job-seeking component would depend on `IHouseholdJobSearchConfig`.

```python
# In: modules/system/config/api.py

from typing import Protocol

class IHouseholdJobSearchConfig(Protocol):
    """Configuration for household job-seeking decisions."""
    wage_decay_rate: float
    reservation_wage_floor: float
    job_quit_threshold_base: float
    job_quit_prob_base: float
    job_quit_prob_scale: float
    household_min_wage_demand: float

class IFirmProductionConfig(Protocol):
    """Configuration for firm production planning."""
    firm_min_production_target: float
    firm_max_production_target: float
    overstock_threshold: float
    understock_threshold: float
    production_adjustment_factor: float
    capital_to_output_ratio: float
```

### 3.2. Configuration Provider (`IConfigProvider`)
The provider acts as a factory or bridge, vending the specific, small configuration protocols to consumers. It is initialized with the master DTOs and maps them to the required protocols.

```python
# In: modules/system/config/api.py

from typing import Type, TypeVar

T = TypeVar("T")

class IConfigProvider(Protocol):
    """
    Provides access to role-specific configuration protocols.
    This acts as a facade over the master config DTOs.
    """
    def get_config(self, config_protocol: Type[T]) -> T:
        """
        Returns an object that conforms to the requested config protocol.
        
        Raises:
            NotImplementedError: If the provider cannot satisfy the requested protocol.
        """
        ...
```

### 3.3. Implementation Strategy (Pseudo-code)

#### Step 1: Loading (Entry Point, e.g., `main.py`)
At the start of the simulation, a `ConfigLoader` reads YAML files into the master DTOs. These are then used to create a concrete `ConfigurationProvider`.

```python
# In a new file, e.g., modules/system/config/provider.py

from simulation.dtos.config_dtos import FirmConfigDTO, HouseholdConfigDTO
from .api import IConfigProvider, IHouseholdJobSearchConfig # ... and others

class ConfigurationProvider:
    """Concrete implementation of the IConfigProvider."""
    def __init__(self, household_config: HouseholdConfigDTO, firm_config: FirmConfigDTO):
        # The provider holds the master DTOs but does not expose them directly.
        # It acts as an adapter.
        self._household_config = household_config
        self._firm_config = firm_config

    def get_config(self, config_protocol: Type[T]) -> T:
        # For each protocol, we return the master DTO that satisfies it.
        # Python's structural typing handles the protocol compliance check.
        if issubclass(config_protocol, IHouseholdJobSearchConfig):
            return self._household_config
        if issubclass(config_protocol, IFirmProductionConfig):
            return self._firm_config
        # ... other mappings
        
        raise NotImplementedError(f"No provider for config protocol: {config_protocol.__name__}")

# In main.py or orchestrator
# loader = YamlConfigLoader("config/economy_params.yaml")
# household_cfg_dto = loader.load_household_config()
# firm_cfg_dto = loader.load_firm_config()
#
# config_provider = ConfigurationProvider(household_cfg_dto, firm_cfg_dto)
```

#### Step 2: Usage (Component Level)
Components declare their dependency on a specific config `Protocol` in their constructor.

```python
# In: modules/household/some_logic.py

from modules.system.config.api import IHouseholdJobSearchConfig

class HouseholdJobLogic:
    def __init__(self, config: IHouseholdJobSearchConfig):
        self._config = config

    def decide_to_quit_job(self, current_wage: float) -> bool:
        quit_threshold = self._config.job_quit_threshold_base * self._config.reservation_wage_floor
        if current_wage < quit_threshold:
            # ... uses self._config.job_quit_prob_base etc.
            return True
        return False
```

#### Step 3: Injection (Object Creation)
The entity responsible for creating components (e.g., an Orchestrator or Factory) uses the `config_provider` to get the required dependency and inject it.

```python
# In orchestrator
from modules.household.some_logic import HouseholdJobLogic
from modules.system.config.api import IHouseholdJobSearchConfig

# ... during agent creation ...
job_search_config = config_provider.get_config(IHouseholdJobSearchConfig)
household.job_logic = HouseholdJobLogic(config=job_search_config)
```

## 4. Verification Plan & Mocking Guide
This design greatly simplifies testing by decoupling components from the global configuration state.

-   **Testing Strategy**: Unit tests should instantiate the required configuration protocol directly, providing only the necessary values for the test case. This avoids the need to set up the entire configuration system or use complex mocking frameworks like `mock.patch`.
-   **Example**:

    ```python
    # In: tests/household/test_some_logic.py
    from dataclasses import dataclass
    from modules.household.some_logic import HouseholdJobLogic
    from modules.system.config.api import IHouseholdJobSearchConfig

    @dataclass
    class MockJobConfig(IHouseholdJobSearchConfig):
        """A concrete, isolated config object for testing."""
        wage_decay_rate: float = 0.99
        reservation_wage_floor: float = 100.0
        job_quit_threshold_base: float = 1.1
        job_quit_prob_base: float = 0.1
        job_quit_prob_scale: float = 0.5
        household_min_wage_demand: float = 90.0

    def test_decide_to_quit_when_wage_is_below_threshold():
        # Arrange
        config = MockJobConfig(reservation_wage_floor=100.0, job_quit_threshold_base=1.2)
        job_logic = HouseholdJobLogic(config=config)

        # Act
        should_quit = job_logic.decide_to_quit_job(current_wage=110.0) # 110 < 100 * 1.2

        # Assert
        assert should_quit is True
    ```

## 5. Risk & Impact Audit (Addressing Pre-flight Checks)

-   **Risk 1: "God" Config Object (TD-190)**: This design explicitly prevents a God object by using Dependency Injection. Components receive fine-grained interfaces, not a monolithic provider.
-   **Risk 2: Propagating SRP Violations**: This design directly addresses SRP violations by introducing and enforcing the use of role-specific `Protocol`s. The monolithic `...ConfigDTO`s are now an implementation detail of the loading mechanism, not a part of the public interface for components.
-   **Risk 3: Circular Dependencies (TD-270)**: The `ConfigLoader` and `ConfigurationProvider` are foundational, low-level services. They have no dependencies on any domain logic (agents, markets, etc.), only on the DTOs and source files, thus preventing circular references.
-   **Risk 4: Test Failure & Refactoring Burden**: The refactoring burden is acknowledged. However, the proposed testing strategy is significantly simpler and more robust than patching `getattr`. It promotes better test isolation and long-term maintainability. The refactoring can be done incrementally, module by module.

## 6. Mandatory Reporting Verification
Insights gained during the implementation of this protocol, particularly regarding the most entangled and difficult-to-separate configuration parameters, will be documented in a new report: `communications/insights/TD-265_config_protocol_insights.md`. This will serve as a guide for future refactoring of the master `economy_params.yaml` file itself.
```
# In file: modules/system/config/api.py
from typing import Protocol, Type, TypeVar, Tuple, Dict, Any

T = TypeVar("T")


# --- Generic Provider Interface ---

class IConfigProvider(Protocol):
    """
    Provides access to role-specific, fine-grained configuration protocols.
    This acts as a facade over master config DTOs, promoting the
    Interface Segregation Principle.
    """
    def get_config(self, config_protocol: Type[T]) -> T:
        """
        Returns an object that conforms to the requested config protocol.

        This method allows components to request only the configuration they need,
        without being coupled to the entire configuration structure.

        Args:
            config_protocol: The Protocol class defining the required configuration.

        Returns:
            An object that structurally matches the requested protocol.

        Raises:
            NotImplementedError: If the provider cannot satisfy the requested protocol.
        """
        ...


# --- Role-Based Protocols for Households ---

class IHouseholdSurvivalConfig(Protocol):
    """Configuration related to a household's basic survival needs."""
    survival_need_consumption_threshold: float
    target_food_buffer_quantity: float
    survival_critical_turns: float
    survival_need_death_threshold: float
    assets_death_threshold: float
    household_death_turns_threshold: float
    survival_need_emergency_threshold: float
    primary_survival_good_id: str
    survival_bid_premium: float
    fallback_survival_cost: float


class IHouseholdJobSearchConfig(Protocol):
    """Configuration for household job-seeking and employment decisions."""
    wage_decay_rate: float
    reservation_wage_floor: float
    labor_market_min_wage: float
    household_low_asset_threshold: float
    household_low_asset_wage: float
    household_default_wage: float
    job_quit_threshold_base: float
    job_quit_prob_base: float
    job_quit_prob_scale: float
    wage_memory_length: int
    wage_recovery_rate: float
    household_min_wage_demand: float
    initial_wage: float


class IHouseholdConsumptionConfig(Protocol):
    """Configuration related to household purchasing and consumption behavior."""
    food_purchase_max_per_tick: float
    market_price_fallback: float
    need_factor_base: float
    need_factor_scale: float
    household_max_purchase_quantity: float
    bulk_buy_need_threshold: float
    panic_buying_threshold: float
    hoarding_factor: float
    deflation_wait_threshold: float
    delay_factor: float
    budget_limit_normal_ratio: float
    budget_limit_urgent_need: float
    budget_limit_urgent_ratio: float
    min_purchase_quantity: float
    elasticity_mapping: Dict[str, float]
    max_willingness_to_pay_multiplier: float
    household_consumable_goods: list[str]
    price_memory_length: int


class IHouseholdInvestmentConfig(Protocol):
    """Configuration for household investment, debt, and financial decisions."""
    stock_market_enabled: bool
    household_min_assets_for_investment: float
    stock_investment_equity_delta_threshold: float
    stock_investment_diversification_count: int
    expected_startup_roi: float
    startup_cost: float
    debt_repayment_ratio: float
    debt_repayment_cap: float
    debt_liquidity_ratio: float
    emergency_liquidation_discount: float
    emergency_stock_liquidation_fallback_price: float
    panic_selling_asset_threshold: float


# --- Role-Based Protocols for Firms ---

class IFirmProductionConfig(Protocol):
    """Configuration for firm production and inventory management."""
    firm_min_production_target: float
    firm_max_production_target: float
    automation_cost_per_pct: float
    automation_labor_reduction: float
    overstock_threshold: float
    understock_threshold: float
    production_adjustment_factor: float
    capital_to_output_ratio: float
    inventory_holding_cost_rate: float
    capital_depreciation_rate: float


class IFirmPricingConfig(Protocol):
    """Configuration for firm pricing strategies."""
    max_sell_quantity: float
    invisible_hand_sensitivity: float
    default_target_margin: float
    max_price_staleness_ticks: int
    fire_sale_asset_threshold: float
    fire_sale_inventory_threshold: float
    fire_sale_inventory_target: float
    fire_sale_discount: float
    fire_sale_cost_discount: float
    sale_timeout_ticks: int
    dynamic_price_reduction_factor: float


class IFirmFinancialsConfig(Protocol):
    """Configuration related to a firm's financial health, dividends, and taxes."""
    startup_cost: float
    seo_trigger_ratio: float
    seo_max_sell_ratio: float
    firm_safety_margin: float
    automation_tax_rate: float
    altman_z_score_threshold: float
    dividend_suspension_loss_ticks: int
    dividend_rate: float
    dividend_rate_min: float
    dividend_rate_max: float
    corporate_tax_rate: float
    valuation_per_multiplier: float
    ipo_initial_shares: float
    bailout_repayment_ratio: float
    firm_maintenance_fee: float


class IFirmHRConfig(Protocol):
    """Configuration for a firm's Human Resources and labor management."""
    labor_alpha: float
    severance_pay_weeks: float
    labor_market_min_wage: float
    labor_elasticity_min: float


# --- General System Protocols ---

class ISystemTimeConfig(Protocol):
    """Configuration related to simulation time and cycles."""
    ticks_per_year: int
```
