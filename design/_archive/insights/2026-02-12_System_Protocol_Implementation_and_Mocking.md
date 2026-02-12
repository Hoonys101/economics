# Insight Report: Fix Integrity Tests (Stale Attributes)

## Executive Summary
This mission addressed failing integrity tests (`test_fiscal_integrity.py`) that were asserting against stale `gov.assets` attributes. The investigation revealed that the root cause was not just the test assertion method, but a defect in the `Government` agent implementation where it inherited the `IFinancialAgent` Protocol but failed to implement the required `_deposit` and `_withdraw` methods. This caused `SettlementSystem` transfers to execute strictly as no-ops (due to Protocol default behavior or silent failure patterns), leaving the agent's wallet unchanged.

Additionally, `test_settlement_system_atomic.py` was found to be broken due to mock objects not satisfying `IFinancialAgent` protocol checks at runtime, causing cash balances to be ignored during settlement creation.

## Key Findings

### 1. Protocol Inheritance vs. Implementation
The `Government` class inherited `IFinancialAgent` in its definition:
```python
class Government(ICurrencyHolder, IFinancialEntity, IFinancialAgent, ISensoryDataProvider):
```
However, it did not implement `_deposit` or `_withdraw`. Since `IFinancialAgent` is a `Protocol` and not an `ABC` with abstract methods enforced at instantiation, the class could be instantiated. At runtime, `isinstance(gov, IFinancialAgent)` returned `True`. When `SettlementSystem` called `gov._deposit()`, it executed the protocol's empty body (no-op), resulting in a successful transaction log but no state change in the wallet.

**Fix**: Implemented `_deposit`, `_withdraw`, `get_all_balances`, and `total_wealth` in `Government`, delegating to `self.wallet`.

### 2. Single Source of Truth (SSoT) in Tests
The tests were asserting `gov.assets`, which is a property wrapping `self.wallet`. While this is technically correct for the agent, the instruction was to use `settlement_system.get_balance(gov.id)`.
For `settlement_system.get_balance()` to work in unit/integration tests, `settlement_system.agent_registry` must be mocked to resolve the agent ID to the agent instance. The default fixture did not provide this.

**Fix**: Updated tests to mock `settlement_system.agent_registry` and use `get_balance()`.

### 3. Mocking Protocols
In `test_settlement_system_atomic.py`, the `deceased` agent was being mocked using `golden_households` (likely `SimpleNamespace` or basic mocks) or `MagicMock`.
`SettlementSystem` uses `isinstance(agent, IFinancialAgent)` to detect capabilities. Standard mocks do not satisfy this check unless `spec` is provided.
The tests were failing to capture cash (0 instead of 1000) because `isinstance` checks failed.

**Fix**: Defined a `MockSettlementAgent` class inheriting all required protocols and used `MagicMock(spec=MockSettlementAgent)` for test agents.

## Technical Debt & Recommendations

1.  **Protocol Enforcement**: Consider using `ABC` or a custom metaclass to enforce implementation of Protocol methods in Agents, or add validtaion in `SettlementSystem` to ensure agents actually have the methods (though `isinstance` should be enough if implemented correctly).
2.  **Test Fixtures**: The `golden_households` fixture seems to return objects that are not fully compliant with new financial protocols. This should be audited.
3.  **Registry in Tests**: `SettlementSystem` relies heavily on `agent_registry`. Test fixtures for `SettlementSystem` should probably auto-configure a mock registry to avoid repetitive setup in every test.

## Verification
- `tests/integration/test_fiscal_integrity.py`: Passed (Gov balance 5000, Bank balance 6000).
- `tests/integration/test_settlement_system_atomic.py`: Passed (Scenario 1, 2, 3).
- Manual reproduction script confirmed `Government` state updates correctly after the fix.
