# Mission Guide: Core Agent & Protocol Restoration

## 1. Objectives
Restore the unit and integration test suite by resolving systemic `TypeError` and `AttributeError` caused by recent architectural changes (Orchestrator-Engine pattern and Protocol hardening).

## 2. Key Failure Categories (MUST FIX)

### Tier 1: Agent Constructor Signature (17+ ERRORs)
- **Problem**: `Household.__init__()` and `Firm.__init__()` now require `core_config: AgentCoreConfigDTO` and `engine: IDecisionEngine`. Many tests still pass `id`, `assets`, etc., directly to `__init__`.
- **Affected**: `tests/unit/test_api_extensions.py`, `tests/system/test_engine.py`.
- **Action**: Use `AgentCoreConfigDTO` for instantiation. Provide mocked engines.

### Tier 2: Financial Protocol Drift (10+ FAILED)
- **Problem**: `withdraw(amount)` calls are failing because the protocol now expects `withdraw(amount, currency=...)`.
- **Affected**: `tests/integration/test_atomic_settlement.py`, `tests/integration/test_liquidation_services.py`.
- **Action**: Update all financial agent mocks to accept `currency` in `withdraw` and `deposit`.

### Tier 3: State DTO Purity
- **Problem**: Tests accessing `agent.assets` or `agent.needs` directly.
- **Affected**: `tests/integration/scenarios/test_stress_scenarios.py`, `tests/integration/test_fiscal_integrity.py`.
- **Action**: Migrate to `agent.get_state_dto().econ_state.wallet.get_balance(currency)` and similar patterns.

## 3. Implementation Plan

### Phase 1: Unit Test Restoration (Core Agents)
1. Fix `tests/unit/test_api_extensions.py`: Update `AgentViewModel` and agent setup.
2. Fix `tests/system/test_engine.py`: Correct `Simulation` initialization and agent creation in `test_simulation_initialization`.

### Phase 2: Integration Protocol Alignment
1. Update `tests/integration/test_atomic_settlement.py`: align `MockAgent` with `IFinancialAgent`.
2. Update `tests/integration/test_liquidation_services.py`: ensure mocks support multi-currency calls.

## 4. Verification
Run the following and ensure zero ERRORs and < 5 FAILED:
```bash
pytest tests/unit/test_api_extensions.py tests/system/test_engine.py tests/integration/test_atomic_settlement.py
```
