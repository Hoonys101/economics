# Phase 23 Debt Liquidation Strategy: The "Safety Net First" Doctrine

## 1. Executive Summary
The comprehensive audit of `TECH_DEBT_LEDGER.md` alongside `ARCH_SEQUENCING.md` reveals a critical dependency chain that dictates our liquidation strategy. We cannot safely address the high-value architectural debts (Firm Coupling, Float Corruption) because our safety net (Tests) has drifted from the actual runtime reality.

## 2. Architectural Insights
-   **The "Mock Drift" Blockade**: `TD-TEST-TX-MOCK-LAG` and `TD-TEST-LIFE-STALE` mean our current tests are verifying a version of the system that no longer exists (pre-Sequence-Refactor). Any attempt to refactor the Firm (`TD-ARCH-FIRM-COUP`) or Settlement (`TD-CRIT-FLOAT-CORE`) without fixing this first will result in false positives or unmanageable regression noise.
-   **The "Penny Standard" Imperative**: The `TD-CRIT-FLOAT-CORE` violation is not just a math error; it's a systemic integrity failure. `SettlementSystem` must be converted to `int` immediately after test stabilization to ensure M&A and dividend logic doesn't leak value.
-   **The "Stateful Firm" Reality**: We acknowledge the "Pragmatic Shift" in `ARCH_AGENTS.md` but reject the circular dependency it introduced. The roadmap prioritizes breaking the `self.parent` cycle by enforcing the SEO (Stateless Engine) pattern, but only *after* the core financial logic is solidified.

## 3. Strategic Decision: Serialization
We will execute in strict phases:
1.  **Stabilize**: Re-align Test Mocks & Lifecycle Assumptions.
2.  **Standardize**: Enforce the Penny Standard (Int) & Missing Handlers.
3.  **Refactor**: Decouple Firm Departments & Optimize AI.

## 4. Test Verification Plan
(To be executed by the implementing agents)
```python
# Verification template for Mission 1 (Test Repair)
import pytest
from tests.mocks import MockTransactionParticipant

def test_mock_protocol_adherence():
    mock = MockTransactionParticipant()
    assert isinstance(mock, ITransactionParticipant)
    assert not hasattr(mock, 'non_compliant_method')
```
