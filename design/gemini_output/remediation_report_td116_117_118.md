# 🏥 Remediation Proposal: Structural Purity & Economic Integrity (TD-116, 117, 118)

---

## 🔍 Context
Following the Audit Report of 2026-01-26, this proposal outlines the fixes for three critical Technical Debt items:
- **TD-116**: Floating-point residuals in asset distribution causing "Ghost Money".
- **TD-117**: Structural Purity violation (Agents accessing live Market objects).
- **TD-118**: Sequence Deviation (CommerceSystem running outside the Sacred Sequence).

---

## 🛠 Proposed Changes

### 1. [TD-116] Economic Integrity Fixes
To prevent money creation from rounding errors during inheritance:
```python
# simulation/systems/transaction_processor.py

# CHANGE: Use floor and capture residual for the last heir
count = len(heir_ids)
import math
base_amount = math.floor((total_cash / count) * 100) / 100.0

for i in range(count - 1):
    settlement.transfer(buyer, heir, base_amount, "inheritance_part")

# Last heir gets the remainder (total_cash - sum(base_amounts))
last_heir = agents.get(heir_ids[-1])
remaining = buyer.assets
settlement.transfer(buyer, last_heir, remaining, "inheritance_final")
```

### 2. [TD-117] Structural Purity (DTO-Only Decisions)
Remove direct access to `Market` and `Government` objects by providing pure data snapshots.

#### A. New Data Transfer Objects
```python
# simulation/dtos/api.py

@dataclass
class MarketSnapshotDTO:
    prices: Dict[str, float]
    volumes: Dict[str, float]
    asks: Dict[str, List[Order]] # For seller selection

@dataclass
class GovernmentPolicyDTO:
    income_tax_rate: float
    base_interest_rate: float
```

#### B. Signature Updates
Agents will now receive these DTOs instead of live objects:
- `Household.make_decision(market_snapshot: MarketSnapshotDTO, ...)`
- `Firm.make_decision(market_snapshot: MarketSnapshotDTO, ...)`

### 3. [TD-118] Sacred Sequence Alignment
Integrate `CommerceSystem` into the 4-Phase execution model within `TickScheduler`.

- **Phase 1 (Decisions)**: Call `state.commerce_system.get_consumption_transactions()` to plan purchases.
- **Phase 3 (Transactions)**: Process these transactions through the standard processor.
- **Phase 4 (Lifecycle)**: Call `state.commerce_system.finalize_consumption_and_leisure()` to apply effects.

---

## ✅ Verification Plan
1. **Zero-Sum Test**: Run `tests/physics/test_money_supply.py` to ensure no delta > 1e-9.
2. **Purity Audit**: Use `grep` to ensure `Household` logic never calls methods on `Market` objects or `Government` objects.
3. **Execution Trace**: Verify in logs that `CommerceSystem` methods run in the correct tick phases.
