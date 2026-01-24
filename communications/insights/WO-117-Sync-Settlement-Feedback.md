# WO-117 Insights: Synchronous Settlement & Leak Hunting

## 1. SettlementSystem Feedback

The `SettlementSystem` proved robust for enforcing zero-sum transfers. However, integrating it into legacy components (`FinanceDepartment`, `Government`) required careful handling of dependencies (`reflux_system`).

**Observation**: `FinanceDepartment` was designed as an internal component but now requires external references (`reflux_system`, `settlement_system`) to perform valid transfers. This increases coupling but is necessary for closed-loop accounting.

## 2. Central Bank Identity

During verification, a crash occurred because `CentralBank` lacked an `id` attribute, which `SettlementSystem` requires for logging and validation.
- **Fix**: Added `self.id = "CENTRAL_BANK"` to `CentralBank`.
- **Recommendation**: Ensure all `IFinancialEntity` implementations strictly adhere to the protocol, including `id`.

## 3. The "Void" Investment Pattern

The discovery that Firm investments were simply `debit()`-ing money into the void highlights a pattern risk. Any "expense" in the system that isn't a transfer to another agent is effectively money destruction.
- **Lesson**: All `debit` calls should be audited. Ideally, `debit` should be protected or removed in favor of `transfer` calls only, forcing the developer to specify a destination.

## 4. Remaining Leaks

While the -100k leak is fixed, a +320 leak remains at Tick 1, and larger leaks appear later in the simulation (e.g., Tick 159: -8013). These likely stem from other legacy systems (like `CommerceSystem` or `TaxAgency` legacy paths) or `Bootstrapper` logic regarding inventory/wage initialization.
