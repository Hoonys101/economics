# Insight Report: BaseAgent Refactoring and Protocol Enforcement

## 1. Problem Phenomenon
The `BaseAgent` class, which serves as the foundation for all agents (`Household`, `Firm`, `Government`, etc.), had an inconsistent implementation of the `IFinancialEntity` protocol.
- `BaseAgent.assets` returned a `Dict[CurrencyCode, float]`, violating `IFinancialEntity.assets` which expects a `float` (representing the primary currency balance).
- Subclasses like `Household` and `Firm` overrode this property to comply, but `BaseAgent` itself remained non-compliant, creating a risk of runtime errors if `BaseAgent` logic was used directly or if a new subclass failed to override it.
- The `BaseAgent` constructor accepted a large number of arguments (8+), making it brittle and hard to extend.

## 2. Root Cause Analysis
- **Protocol Violation**: The `IFinancialEntity` protocol was defined to operate on `DEFAULT_CURRENCY` (returning float), but `BaseAgent` was designed as a multi-currency holder (`ICurrencyHolder`) and exposed its internal wallet dictionary directly via `.assets`.
- **Parameter Explosion**: As agents evolved, more dependencies (decision engine, logger, memory interface) were added to `BaseAgent.__init__`, leading to signature bloat.

## 3. Solution Implementation Details
- **DTO Introduction**: Introduced `BaseAgentInitDTO` in `simulation/dtos/agent_dtos.py` to encapsulate all initialization parameters. This simplifies the `__init__` signature and provides a single place to manage type hints for constructor args.
- **Protocol Enforcement**:
    - Updated `BaseAgent.assets` to return `self._wallet.get_balance(DEFAULT_CURRENCY)` (float), strictly adhering to `IFinancialEntity`.
    - Maintained `get_assets_by_currency()` for `ICurrencyHolder` compliance.
    - Updated `deposit` and `withdraw` to default to `DEFAULT_CURRENCY`.
- **Refactoring**:
    - Refactored `BaseAgent.__init__` to accept `init_config: BaseAgentInitDTO`.
    - Updated `Household` and `Firm` constructors to instantiate `BaseAgentInitDTO` and pass it to `super().__init__`.
- **Testing**: Updated `tests/unit/test_base_agent.py` and `tests/unit/test_firms.py` to reflect these changes and verify protocol compliance.

## 4. Lessons Learned & Technical Debt
- **Protocol Clarity**: Interfaces should be strictly adhered to by base classes if they claim implementation. Mixing "default implementation" that violates the interface with "subclass override" is dangerous.
- **DTO Pattern**: Using DTOs for complex constructors (Parameter Object Pattern) significantly improves readability and extensibility.
- **Test Fragility**: The test suite (`conftest.py`) had fragile dependencies on `simulation.initialization` which caused issues when environment or imports changed slightly. We fixed this by ensuring necessary packages (`numpy`, `pyyaml`) were installed and imports were robust.
- **Mocking Risks**: Tests using `Mock(spec=Class)` can hide missing attributes if the class initializes them dynamically in `__init__` (like `_econ_state` in `Household`). Tests should verify initialization logic or use more robust fixtures.