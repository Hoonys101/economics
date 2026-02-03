# TD-196: `IConfigManager` Interface Definition

## `modules/common/config_manager/api.py`

```python
from typing import Protocol, TypedDict, List, Tuple, Dict, Any, Optional
from abc import abstractmethod

# ==============================================================================
# DTOs for Domain-Specific Configuration
# ==============================================================================

class FiscalConfigDTO(TypedDict):
    """Configuration for government, taxation, and fiscal policy."""
    tax_brackets: List[Tuple[float, float]]
    wealth_tax_threshold: float
    annual_wealth_tax_rate: float
    unemployment_benefit_ratio: float
    stimulus_trigger_gdp_drop: float
    credit_recovery_ticks: int
    bankruptcy_xp_penalty: float
    corporate_tax_rate: float
    income_tax_rate: float
    sales_tax_rate: float
    inheritance_tax_rate: float
    potential_gdp_window: int
    gov_action_interval: int
    debt_ceiling_ratio: float
    fiscal_stance_expansion_threshold: float
    fiscal_stance_contraction_threshold: float
    policy_actuator_bounds: Dict[str, Tuple[float, float]]
    policy_actuator_step_sizes: Tuple[float, float, float]

class MarketConfigDTO(TypedDict):
    """Configuration for market dynamics, pricing, and goods."""
    goods: Dict[str, Any]
    initial_wage: float
    base_wage: float
    labor_market_min_wage: float
    price_adjustment_factor: float
    overstock_threshold: float
    understock_threshold: float
    market_price_fallback: float
    panic_buying_threshold: float
    hoarding_factor: float
    deflation_wait_threshold: float
    delay_factor: float
    price_volatility_window_ticks: int

class HouseholdConfigDTO(TypedDict):
    """Configuration for household behavior, needs, and lifecycle."""
    initial_assets_range: float
    initial_needs_mean: Dict[str, float]
    survival_need_death_threshold: float
    reproduction_age_start: int
    reproduction_age_end: int
    hours_per_tick: float
    leisure_weight: float
    primary_survival_good_id: str
    survival_need_emergency_threshold: float
    emergency_liquidation_discount: float
    bulk_buy_need_threshold: float
    job_quit_threshold_base: float
    reservation_wage_base: float


class FirmConfigDTO(TypedDict):
    """Configuration related to firm behavior, production, and strategy."""
    startup_cost: float
    startup_min_capital: float
    firm_maintenance_fee: float
    ma_enabled: bool
    liquidation_discount_rate: float
    bankruptcy_consecutive_loss_ticks: int
    hostile_takeover_discount_threshold: float
    automation_labor_reduction: float
    automation_cost_per_pct: float
    severance_pay_weeks: int


class IConfigManager(Protocol):
    """
    Interface for a configuration provider.
    Decouples modules from the concrete configuration source (e.g., config.py, .yaml).
    """

    @abstractmethod
    def get_fiscal_config(self) -> FiscalConfigDTO:
        """Returns configuration related to fiscal policy and government."""
        ...

    @abstractmethod
    def get_market_config(self) -> MarketConfigDTO:
        """Returns configuration for market dynamics."""
        ...

    @abstractmethod
    def get_household_config(self) -> HouseholdConfigDTO:
        """Returns configuration for household agents."""
        ...
    
    @abstractmethod
    def get_firm_config(self) -> FirmConfigDTO:
        """Returns configuration for firm agents."""
        ...

    @abstractmethod
    def get_raw_value(self, key: str, default: Optional[Any] = None) -> Any:
        """

        Retrieves a raw, untyped configuration value by its key.
        This is a fallback for accessing values not yet part of a typed DTO.
        Usage should be minimized and is intended as a transitional tool.
        """
        ...
```

## `design/3_work_artifacts/specs/TD-196_config_manager_spec.md`

# Spec: `IConfigManager`
- **TDR-ID**: TD-196
- **Summary**: Defines an interface to decouple all modules from the monolithic `config.py` God Object. This will be achieved by introducing a configuration manager that serves domain-specific, type-safe configuration objects (DTOs).

## 1. Problem Statement
The `config.py` file has become a "God Object," creating extreme coupling across the entire system. Any modification carries a high risk of causing cascading, unpredictable failures. The test suite is particularly vulnerable. This architecture violates the Single Responsibility Principle and makes maintenance and refactoring hazardous.

## 2. Proposed Solution
We will introduce an `IConfigManager` interface that acts as the single source of truth for configuration. Modules will no longer import `config.py` directly. Instead, they will receive an instance of `IConfigManager` (via dependency injection) and request strongly-typed configuration DTOs.

### 2.1. Phased Rollout Plan

**Phase 1: Facade Implementation**
- A concrete class `ConfigManagerFromPy` will be created that implements `IConfigManager`.
- This class will import `config.py` internally and populate the DTOs (e.g., `FiscalConfigDTO`, `MarketConfigDTO`) with the values from the file.
- This phase is purely additive and involves no modification to existing modules.

**Phase 2: Incremental Refactoring (Module by Module)**
- One module at a time will be refactored to use the new system. For example, the `government` module will be modified to accept an `IConfigManager` in its constructor.
- Inside the `government` module, all references to `config.GBV_...` will be replaced with `self.config_manager.get_fiscal_config()['...']`.
- The corresponding tests for the `government` module will be updated to use the `MockConfigManager` (see Test Migration Strategy).
- **This task (TD-193) will be the first client of this new architecture.**

**Phase 3: Full Decoupling**
- Once all modules have been migrated, `config.py` is no longer imported by any application module except `ConfigManagerFromPy`.
- The underlying source can now be swapped (e.g., to a `ConfigManagerFromYAML`) without impacting any other part of the system, achieving the primary goal.

## 3. Interface & DTOs
See `modules/common/config_manager/api.py`. The DTOs group related constants into logical, domain-specific structures.

## 4. 🚨 Risk & Impact Audit
- **Risk**: Mass test failure.
- **Mitigation**: A comprehensive Test Migration Strategy is required. Direct modification of tests will be necessary.
- **Risk**: Circular dependencies.
- **Mitigation**: The `IConfigManager` implementation **MUST NOT** import any other application module. It is a leaf node in the dependency tree.
- **Risk**: Incomplete DTOs during transition.
- **Mitigation**: The `get_raw_value(key)` method is provided as a temporary escape hatch to access constants not yet migrated to a DTO. Its use should be logged as technical debt.

## 5. ✅ Verification & Test Migration Strategy
The key to mitigating risk is a robust testing strategy.

1.  **`MockConfigManager` Fixture**:
    - A `pytest` fixture named `mock_config_manager` will be created in `tests/conftest.py`.
    - This fixture will allow tests to easily provide custom configuration values without relying on the global `config.py`.

    ```python
    # tests/conftest.py (example)
    @pytest.fixture
    def mock_config_manager():
        manager = Mock(spec=IConfigManager)
        
        # Default fiscal config for most tests
        fiscal_config = FiscalConfigDTO(
            tax_brackets=[(1.0, 0.1), (3.0, 0.2)],
            wealth_tax_threshold=50000.0,
            # ... other fiscal values
        )
        manager.get_fiscal_config.return_value = fiscal_config
        
        # ... mock other configs ...
        
        return manager
    ```

2.  **Test Refactoring**:
    - All tests for a refactored module (e.g., `tests/modules/government_test.py`) must be updated.
    - Instead of relying on imported constants, they will use the `mock_config_manager` to set up scenarios and pass it to the module under test.

    ```python
    # tests/modules/government_test.py (example)
    def test_tax_collection_for_middle_class(mock_config_manager):
        # Arrange: Modify the default mock config for this specific test
        specific_fiscal_config = mock_config_manager.get_fiscal_config()
        specific_fiscal_config['tax_brackets'] = [(1.0, 0.15)] # New bracket for this test
        mock_config_manager.get_fiscal_config.return_value = specific_fiscal_config

        government = Government(config_manager=mock_config_manager)
        household = Household(income=2.0)

        # Act
        tax_due = government.calculate_income_tax(household)

        # Assert
        assert tax_due == 2.0 * 0.15
    ```

---

# TD-193: Sync Politics System with Specs

## `modules/government/politics/api.py`

```python
from typing import Protocol
from modules.common.config_manager.api import IConfigManager, FiscalConfigDTO

class IPolitics(Protocol):
    """
    Interface for the Politics system, which manages fiscal policies like taxation.
    """

    def __init__(self, config_manager: IConfigManager):
        """
        Initializes the Politics system with a configuration manager.
        """
        ...

    def calculate_income_tax(self, household_income: float) -> float:
        """
        Calculates income tax based on the progressive tax brackets defined in the configuration.
        """
        ...

    def is_wealth_tax_applicable(self, household_assets: float) -> bool:
        """
        Determines if a household is liable for wealth tax based on the configured threshold.
        """
        ...
```

## `design/3_work_artifacts/specs/TD-193_politics_sync_spec.md`

# Spec: Politics System Sync
- **TDR-ID**: TD-193
- **Summary**: Refactors the `Politics` system to align with centrally managed configuration. This serves as the pilot project for adopting the new `IConfigManager`.

## 1. Problem Statement
The `Politics` module (and its related systems in `government`) likely contains hardcoded values or direct imports from `config.py` for tax brackets, thresholds, and other fiscal parameters. This creates a tight coupling and makes policy changes difficult and risky.

## 2. Proposed Solution
The `Politics` module will be refactored to be completely ignorant of `config.py`. It will depend solely on the `IConfigManager` interface for all its configuration needs.

### 2.1. Implementation Steps
1.  Modify the `Politics` class constructor to accept an `IConfigManager` instance.
2.  In the constructor, call `self.config_manager.get_fiscal_config()` and store the resulting `FiscalConfigDTO` in an instance variable (e.g., `self.fiscal_config`).
3.  Replace all internal usages of `config.TAX_BRACKETS` with `self.fiscal_config['tax_brackets']`.
4.  Replace all usages of `config.WEALTH_TAX_THRESHOLD` with `self.fiscal_config['wealth_tax_threshold']`.
5.  Continue for all other fiscal constants used within the module.

## 3. Pseudo-code
```python
class Politics(IPolitics):
    def __init__(self, config_manager: IConfigManager):
        self.config_manager = config_manager
        self.fiscal_config: FiscalConfigDTO = self.config_manager.get_fiscal_config()

    def calculate_income_tax(self, household_income: float) -> float:
        # Before: tax_brackets = config.TAX_BRACKETS
        # After:
        tax_brackets = self.fiscal_config['tax_brackets']
        
        tax_due = 0.0
        # ... logic using tax_brackets ...
        return tax_due

    def is_wealth_tax_applicable(self, household_assets: float) -> bool:
        # Before: threshold = config.WEALTH_TAX_THRESHOLD
        # After:
        threshold = self.fiscal_config['wealth_tax_threshold']
        
        return household_assets > threshold
```

## 4. 🚨 Risk & Impact Audit
- **Primary Risk**: Breaking tests for the `Politics` module.
- **Mitigation**: All tests in `tests/modules/government/` must be refactored to use the `mock_config_manager` fixture to inject the required fiscal configuration, as detailed in the `TD-196` specification. No direct imports of `config` should remain in the test files.

## 5. ✅ Verification Plan
- All unit tests for the `Politics` and `Government` modules must pass after refactoring.
- A new test case will be added to verify that the `Politics` module correctly responds to a change in configuration provided by the `mock_config_manager` at runtime, proving that the decoupling is successful.

---

# TD-190: Extract Magic Numbers to Constants

## `design/3_work_artifacts/specs/TD-190_magic_number_extraction_spec.md`

# Spec: Magic Number Extraction
- **TDR-ID**: TD-190
- **Summary**: Establish a process for identifying "magic numbers" in the codebase, extracting them into the central configuration, and accessing them via the `IConfigManager`.

## 1. Problem Statement
The codebase likely contains numerous hardcoded numerical literals ("magic numbers") for decision-making logic, thresholds, and factors. These make the code difficult to understand, maintain, and tune.

## 2. Proposed Solution
A systematic effort will be made to eliminate magic numbers. The `IConfigManager` provides the framework to do this in a structured way.

### 2.1. Process
1.  **Identify**: During development or code review, when a magic number is found (e.g., `if assets > 500.0:`), it is flagged.
2.  **Categorize**: Determine the domain the number belongs to (e.g., `Household Behavior`, `Market Logic`, `Firm Strategy`).
3.  **Centralize**: Add the number as a named constant to the appropriate section in `config.py`. The name must clearly state its purpose (e.g., `HOUSEHOLD_MIN_ASSETS_FOR_INVESTMENT = 500.0`).
4.  **Expose**: Add the new constant to the relevant DTO in `modules/common/config_manager/api.py`. For the example above, it would be added to `HouseholdConfigDTO`.
5.  **Refactor**: Modify the original code to use the `IConfigManager` to access the value.

    ```python
    # Before
    if household.assets > 500.0:
        # ...

    # After (in a method within the Household agent)
    min_assets = self.config.get_household_config()['min_assets_for_investment']
    if household.assets > min_assets:
        # ...
    ```

### 2.2. Candidate Magic Numbers (from `config.py` review)
The following hardcoded values from `config.py` are prime examples of what to look for elsewhere in the code and should be managed via this process:

- `HOUSEHOLD_LOW_ASSET_THRESHOLD = 100.0`
- `FIRM_DEFAULT_TOTAL_SHARES = 100.0`
- `BULK_BUY_NEED_THRESHOLD = 70.0`
- `JOB_QUIT_PROB_BASE = 0.1`
- `STOCK_SELL_PROFIT_THRESHOLD = 0.15`
- `PANIC_SELLING_ASSET_THRESHOLD = 500.0`
- All numerical literals in policy bounds, step sizes, and thresholds.

## 3. 🚨 Risk & Impact Audit
- **Risk**: Over-engineering. Not every number is "magic". A literal `0` for an initial sum or `1` for an increment is acceptable. This process should be applied to numbers that represent a business rule, threshold, or factor that might need tuning.
- **Risk**: Messy `config.py`.
- **Mitigation**: New constants must be added to the appropriate, documented section within `config.py` to maintain organization. The long-term goal is to replace `config.py` entirely, but until then, it must be kept tidy.

## 4. ✅ Verification Plan
- Code reviews are the primary enforcement mechanism.
- Reviewers must reject pull requests that introduce new, tunable magic numbers without following this process.
- Automated static analysis tools (e.g., linters with custom rules) could be configured to flag magic numbers in the future.
