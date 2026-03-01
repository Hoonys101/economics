# MISSION_spec: Connectivity & SSoT Enforcement (Wave 4)

**Target Phase**: Wave 4 - Connectivity & SSoT Enforcement
**Status**: DRAFT / SPECIFYING
**Priority**: CRITICAL (Systemic Integrity)

## 1. Context & Objectives
The **Project Watchtower Audit** identified a systemic risk where modules bypass the `SettlementSystem` and `IInventoryHandler` by directly mutating `.cash`, `.assets`, or `.inventory`. Additionally, generic `"transfer"` transactions are often "invisible" to the Monetary Ledger.

### Goals:
1. **SSoT Visibility**: Ensure 100% of value shifts are visible to the `MonetaryLedger`.
2. **Runtime Enforcement**: Explicitly prevent and fail on direct state mutations outside approved handlers.

---

## 2. Proposed Changes

### 2.1. [NEW] GenericTransferHandler
Implement or update the transaction handler for the generic `"transfer"` type to ensure P2P visibility.

- **File**: `simulation/systems/handlers/transfer_handler.py` (or new)
- **Logic**:
  - Intercept `"transfer"` transactions.
  - Notify `MonetaryLedger` of the shift.
  - Verify that if the transfer crosses the M2 boundary (System vs Agent), expansion/contraction is recorded.

### 2.2. [ENFORCEMENT] Financial & Inventory Sentry
Implement a runtime guard to block "Protocol Evasion".

- **Files**: 
  - `modules/finance/api.py` (Protocol update)
  - `modules/simulation/api.py` (IInventoryHandler update)
  - `simulation/systems/settlement_system.py` (Sentry Orchestration)

- **Concept**:
```python
# In SettlementSystem
class FinancialSentry:
    _is_active = False
    
    @classmethod
    def unlock(cls):
        cls._is_active = True
        
    @classmethod
    def lock(cls):
        cls._is_active = False

# In Agent / Household / Firm
@property
def cash(self):
    return self._cash

@cash.setter
def cash(self, value):
    if not FinancialSentry._is_active and not self._is_initializing:
        raise SystemicIntegrityError("Direct mutation of .cash is FORBIDDEN. Use SettlementSystem.")
    self._cash = value
```

---

## 3. Verification Plan

### 3.1. Automated Tests
- **Test Sentry Violation**: Create a unit test that attempts to manually increment `agent.cash`. Verify it raises `SystemicIntegrityError`.
- **Test Transfer Visibility**: Perform a `"transfer"` between two agents and verify `MonetaryLedger.get_total_m2_pennies()` reflects the change immediately if applicable.

### 3.2. Evidence Requirements
- Log output showing `SystemicIntegrityError` during a deliberate violation test.
- Screenshot of the `MonetaryLedger` expansion counters after a generic transfer.
