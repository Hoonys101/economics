# Spec: Configuration System Refactoring (TD-190, TD-193, TD-196)

## 1. Overview & Goals

This document outlines the specification for a critical refactoring of the project's configuration system.

### 1.1. Problem Statement

The current configuration system, centralized in `config.py`, has become a "God Object." It creates high coupling across all modules, violates the Single Responsibility Principle (SRP), and poses significant risks to testing and maintainability. The recent pre-flight audit identified critical risks related to hidden dependencies, circular imports, and the extensive impact of any changes on the existing test suite.

### 1.2. Project Goals

The primary goals of this refactoring are:
1.  **Decouple Modules**: Eliminate direct dependencies on the monolithic `config.py` by introducing a unified, abstracted interface (`IConfigManager`).
2.  **Enforce SRP**: Decompose the monolithic `config.py` into smaller, domain-specific configuration files, improving organization and maintainability.
3.  **Ensure Testability**: Provide a clear and simple path for migrating existing tests and writing new ones, with a focus on easy configuration mocking and overriding.
4.  **Prevent Circular Dependencies**: Establish a unidirectional data flow where runtime configuration changes are *pushed* to the configuration system, not pulled by it.

---

## 2. Detailed Design (TD-196: IConfigManager Interface)

To address the "God Object" and coupling issues, we will introduce a new interface, `IConfigManager`, and a set of domain-specific Data Transfer Objects (DTOs).

### 2.1. `IConfigManager` Interface

The `IConfigManager` will be the single entry point for all configuration access. Its responsibilities are to load, provide, and update configurations.

-   **Location**: `modules/common/config/api.py`
-   **Specification**: See Section 7 for the full `api.py` file content.

```python
class IConfigManager(ABC):
    @abstractmethod
    def get_config(self, domain_name: str, dto_class: Type[T_ConfigDTO]) -> T_ConfigDTO:
        # Retrieves an immutable, typed configuration DTO for a domain.
        ...

    @abstractmethod
    def update_config(self, domain_name: str, new_config_dto: BaseConfigDTO) -> None:
        # Atomically updates a domain's configuration at runtime.
        ...
```

### 2.2. Configuration DTOs

All configuration will be exposed as immutable `dataclasses`. This enforces type safety and prevents runtime modifications outside the control of the `IConfigManager`.

```python
@dataclass(frozen=True)
class BaseConfigDTO:
    pass

@dataclass(frozen=True)
class GovernmentConfigDTO(BaseConfigDTO):
    income_tax_rate: float
    corporate_tax_rate: float
    # ... other government-related fields
```

---

## 3. Configuration Decomposition (TD-190: Extract Magic Numbers)

To dismantle the `config.py` monolith and align with SRP, all configuration variables will be moved into a structured directory of YAML or Python files.

### 3.1. New Directory Structure

The `config/` directory will be reorganized to hold domain-specific configurations.

```
config/
├── domains/
│   ├── government.py
│   ├── finance.py
│   ├── stock_market.py
│   ├── household.py
│   └── ... (one file per domain)
├── simulation.yaml
└── scenarios/
    └── ...
```

### 3.2. Extraction Process (Routine)

1.  **Identify Domain**: Group related constants from `config.py` into a logical domain (e.g., all `TAX_` variables belong to `government`).
2.  **Create DTO**: Define a corresponding `...ConfigDTO` dataclass in the appropriate `api.py` file (or a new `modules/<domain>/dtos.py`).
3.  **Create Domain File**: Create a `config/domains/<domain_name>.py` file. This file will contain a single dictionary or dataclass instance with the configuration values.
4.  **Migrate Values**: Move the constants from `config.py` into the new domain file.
5.  **Register Domain**: The `IConfigManager` implementation will be responsible for loading these files and mapping them to their respective DTOs upon initialization.

---

## 4. Politics System Integration (TD-193)

This section explicitly addresses the circular dependency risk identified in the audit. The `Politics` system will modify policy by pushing changes to the `IConfigManager`, ensuring a unidirectional data flow.

### 4.1. Pseudo-code: Updating Tax Policy

```python
# In modules/government/politics_system.py

from modules.common.config.api import IConfigManager, GovernmentConfigDTO

class PoliticsSystem:
    def __init__(self, config_manager: IConfigManager):
        self._config_manager = config_manager

    def enact_new_tax_policy(self, simulation_state):
        # 1. Analyze simulation state to decide on new policy
        new_rate = self._calculate_new_tax_rate(simulation_state.gdp, simulation_state.unemployment)

        # 2. Get the CURRENT configuration DTO
        # This ensures we only change what's necessary and don't lose other settings.
        current_gov_config = self._config_manager.get_config("government", GovernmentConfigDTO)

        # 3. Create a NEW DTO with the updated value.
        # dataclasses.replace is perfect for this, creating a new immutable instance.
        new_gov_config = dataclasses.replace(current_gov_config, income_tax_rate=new_rate)

        # 4. PUSH the new configuration to the manager.
        # The config manager handles the update. No circular import is needed.
        self._config_manager.update_config("government", new_gov_config)

        print(f"Politics system enacted new income tax rate: {new_rate}")

# In the main simulation loop:
# config_manager is passed during initialization
politics_system = PoliticsSystem(config_manager)
politics_system.enact_new_tax_policy(current_state)
```

This design strictly enforces that the `Politics` system is a *client* of the `IConfigManager` and does not require the configuration system to know anything about it.

---

## 5. Test Migration & Verification Plan

This plan addresses the critical risk of breaking the existing test suite.

### 5.1. The `mock_config` Fixture

A dedicated `pytest` fixture will be created to provide a mock `IConfigManager` that simplifies overriding configuration for test cases. This avoids complex mocking logic in every test file.

-   **Location**: `tests/conftest.py`

#### 5.1.1. Fixture Usage Example

```python
# in tests/modules/household/test_decision.py

def test_household_buys_food_when_wage_is_high(mock_config):
    # ARRANGE
    # Override a specific value for this test case.
    mock_config.override("finance.initial_base_annual_rate", 0.50)
    mock_config.override("household.base_wage", 100.0)

    # The household will now be instantiated with a config manager
    # that returns these overridden values.
    household = Household(config_manager=mock_config)
    market = Market(config_manager=mock_config)

    # ACT
    ...

    # ASSERT
    ...
```

### 5.2. Phased Migration Strategy

1.  **Phase 1: Implement `IConfigManager` and `mock_config`**: The core interface and test fixture are implemented first.
2.  **Phase 2: New Modules & Tests**: All *new* modules and tests written MUST use the `IConfigManager` pattern. Direct imports from `config.py` in new code are prohibited.
3.  **Phase 3: Gradual Refactoring (Tech Debt)**: Existing tests will be migrated to use the `mock_config` fixture incrementally as part of the ongoing technical debt reduction process. A P0 ticket will be created for each module to track migration progress.

### 5.3. Golden Data & Scenarios

Configuration is an integral part of a scenario definition. The `IConfigManager` implementation should be able to load configuration sets from the `config/scenarios/` directory, allowing entire simulation runs to be defined by a single scenario file that includes its specific configuration.

---

## 6. Risk & Impact Audit (Mitigation Plan)

This section explicitly documents how the proposed design mitigates the risks from the pre-flight audit.

-   **Risk 1: Hidden Dependencies & God Classes**
    -   **Mitigation**: The `IConfigManager` provides domain-specific, typed DTOs (`FinanceConfig`, `GovernmentConfig`). Modules now only depend on the configuration they need, not the entire monolithic object. This enforces the Interface Segregation Principle.

-   **Risk 2: Potential Circular Imports**
    -   **Mitigation**: The `update_config` method enforces a unidirectional data flow. Systems like `Politics` *push* changes to the manager. The manager is a passive recipient and never imports from application-level modules, preventing import loops.

-   **Risk 3: Violation of Single Responsibility Principle (SRP)**
    -   **Mitigation**: The decomposition plan (TD-190) to split `config.py` into `config/domains/*.py` directly addresses this. Each file will be responsible for a single domain of configuration.

-   **Risk 4: Risks to Existing Tests**
    -   **Mitigation**: The `mock_config` pytest fixture provides a simple, low-friction path for test migration. It abstracts away the complexity of mocking the manager, allowing test authors to focus on overriding specific values needed for their test case. The phased migration plan makes this large-scale change manageable.

---

## 7. `modules/common/config/api.py`

This file defines the public contract for the entire configuration system.

```python
"""
API for the Configuration Management System.

Defines the interface for accessing and updating configuration, as well as the
Data Transfer Objects (DTOs) used to represent domain-specific configurations.
"""
from abc import ABC, abstractmethod
from typing import Type, TypeVar, Dict, Any
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

# --- Example DTOs to illustrate the pattern ---

@dataclass(frozen=True)
class GovernmentConfigDTO(BaseConfigDTO):
    """Configuration for government policies."""
    income_tax_rate: float
    corporate_tax_rate: float
    sales_tax_rate: float
    wealth_tax_threshold: float
    annual_wealth_tax_rate: float
    tax_brackets: list
    gov_action_interval: int


@dataclass(frozen=True)
class FinanceConfigDTO(BaseConfigDTO):
    """Configuration for the financial system."""
    initial_base_annual_rate: float
    bank_margin: float
    credit_spread_base: float
    loan_default_term: int
    ticks_per_year: float


@dataclass(frozen=True)
class StockMarketConfigDTO(BaseConfigDTO):
    """Configuration for the stock market."""
    stock_market_enabled: bool
    stock_price_limit_rate: float
    stock_transaction_fee_rate: float
    ipo_initial_shares: float

```
