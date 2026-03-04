# Specification: 3-Tier Scenario Reporting Engine (Physics, Macro, Micro)

## 1. Logic Steps (Pseudo-code)

### 3-Tier Data Harvesting Flow
```python
# Physics Tier Harvesting (Strict Integer Penny Standard)
def get_metrics(self, world_state: IWorldStateMetricsProvider) -> Dict[str, Any]:
    money_supply: MoneySupplyDTO = world_state.calculate_total_money()
    return {
        "m2_supply_pennies": money_supply.total_m2_pennies,
        "system_debt_pennies": money_supply.system_debt_pennies,
        "m2_delta": money_supply.total_m2_pennies - EXPECTED_BASELINE # Validated invariant
    }

# Macro Tier Harvesting
def get_metrics(self, world_state: IWorldStateMetricsProvider) -> Dict[str, Any]:
    indicators: EconomicIndicatorsDTO = world_state.get_economic_indicators()
    return {
        "gdp": indicators.gdp,
        "cpi": indicators.cpi,
        "unemployment_rate": getattr(indicators, 'unemployment_rate', 0.0) # Ensure mapped in DTO
    }

# Micro Tier Harvesting
def get_metrics(self, world_state: IWorldStateMetricsProvider) -> Dict[str, Any]:
    panic_index: float = world_state.get_market_panic_index()
    return {
        "market_panic_index": panic_index,
        "withdrawal_pressure_alert": panic_index > CRITICAL_THRESHOLD
    }
```

### Markdown Report Generation Template (Orchestrator Level)
The Orchestrator aggregates the metrics from the three Judges and populates a markdown template:
```markdown
## 📊 Scenario Evaluation Report: [Scenario ID]

### 🪐 Tier 1: Physics Integrity
* M2 Total: `{physics.m2_supply_pennies}` pennies
* System Debt: `{physics.system_debt_pennies}` pennies
* Zero-Sum Violation: `{physics.m2_delta}`

### 📈 Tier 2: Macro Health
* GDP Output: `{macro.gdp}`
* CPI: `{macro.cpi}`

### 👥 Tier 3: Micro Sentiment
* Panic Index: `{micro.market_panic_index}`
```

## 2. Exceptions
- `MetricUnavailableError`: Raised if the underlying provider fails to construct a required DTO or if a subsystem (like `EconomicIndicatorTracker`) has crashed.
- `ProtocolImplementationError`: Raised if `world_state` passed to the Judges fails to implement `IWorldStateMetricsProvider`.
- `FloatIncursionError`: Raised in `PhysicsIntegrityJudge` if monetary metrics somehow leak as floats instead of integers.

## 3. Interface 명세 (DTO/Protocol Field Summary)
- **`IWorldStateMetricsProvider` (Protocol)**:
  - `calculate_total_money() -> MoneySupplyDTO`
  - `get_economic_indicators() -> EconomicIndicatorsDTO`
  - `get_market_panic_index() -> float`
- **Judges**: `PhysicsIntegrityJudge`, `MacroHealthJudge`, `MicroSentimentJudge`. Each bound strictly to Single Responsibility corresponding to their Tier.

## 4. 검증 계획 (Testing & Verification Strategy)

- **New Test Cases**:
  - Unit tests for each Judge verifying correct data extraction from a strictly mocked `IWorldStateMetricsProvider`.
  - Assert that `PhysicsIntegrityJudge` explicitly enforces the integer penny standard.
- **Existing Test Impact (CRITICAL)**:
  - Extending the `IWorldState` requirements means all existing mocks in `tests/` must be updated.
  - **Fix Strategy**: In `conftest.py`, ensure `mock_world_state` uses `MagicMock(spec=IWorldStateMetricsProvider)` and provides default `return_value`s for `calculate_total_money`, `get_economic_indicators`, and `get_market_panic_index`.
- **Integration Check**: Verify that `WorldState` concrete class fully implements the new `IWorldStateMetricsProvider` methods properly decoupled from direct Tracker instance exposures.

## 5. Risk & Impact Audit (기술적 위험 분석)

- **DTO/DAO Interface Impact**: By utilizing existing pure DTOs (`MoneySupplyDTO`, `EconomicIndicatorsDTO`), we successfully decouple the scenario judges from God Classes like `EconomicIndicatorTracker`.
- **순환 참조 위험 (Circular Dependency)**: Solved. The Judges import DTOs and Protocols from `api.py` namespaces. They DO NOT import concrete simulation logic or concrete trackers.
- **TECH_DEBT_LEDGER Audit**:
  - **`TD-TEST-MOCK-REGRESSION`**: The risk of mock drift is actively mitigated by strictly typing the mock updates in the `conftest.py` setup. The protocol extension resolves the hidden God Class dependency identified in the pre-flight check.
  - **`TD-FIN-LIQUIDATION-DUST`**: The Physics Judge relies heavily on Penny-strict logic (`total_m2_pennies`). This will naturally highlight any floating-point dust leaks from liquidations.

## 6. Mandatory Reporting Verification
🚨 **MANDATORY**: A detailed insight report has been independently generated at `communications/insights/WO-SPEC-SCENARIO-REPORTER.md`. Do not deploy these judges without full `pytest` regression checks passing.
