# SPEC: Asset Recovery & Escheatment System (ARES) - TD-171

## 1. Problem Statement
When a Household or Firm dies/bankrupts, small amounts of currency ("dust") or certain asset types (Durable Goods, small share fractions) vanish from the system. In a closed-loop economy, this leads to a slow deflationary leak that undermines the M2 Audit Loop.

## 2. Structural Requirements

### A. The "Great Sieve" (Liquidation Audit)
- Every agent death or firm closure MUST trigger a final balance check.
- **Rule**: `Initial_Assets == Distributed_Assets + Escheated_Assets + Recorded_Losses`.
- If this equation does not balance, the `SimulationLogger` must fire a `FINANCIAL_VOX_CRITICAL` event.

### B. Escheatment to Government
- All non-inherited cash (Household without heirs) or residual liquidation cash (Firm without creditors/shareholders) must be transferred to the Government Treasury using a `PublicEscheatmentTransaction`.
- **Target**: `simulation/systems/inheritance_manager.py` and `simulation/systems/lifecycle_manager.py`.

### C. Durable Goods Recovery
- Currently, durable goods (cars, appliances) simply vanish upon death.
- **Protocol**: Durable goods should be transferred to the `PublicManager` to be auctioned off as "Secondary Market Goods" or recorded as "Scrap Value" destruction.

## 3. Implementation Plan
1.  **AssetRecoverySystem (ARS)**: New component in `WorldState` to track "Asset Life-to-Death" transitions.
2.  **Inheritance Refactoring**: Update `InheritanceManager` to ensure escheatment transactions are processed *before* the agent object is completely dereferenced.
3.  **Leak Monitor**: `test_finance_purity.py` will specifically track "Death Leaks".

---

# SPEC: Transactional Saga & Escrow Refactoring - TD-175

## 1. Problem Statement
Transaction logic (e.g., buying goods with sales tax) currently relies on manual `try...except` and manual rollback calls. This is error-prone, tightly coupled, and difficult to test for complex failure paths (e.g., buyer has cash for goods but not for tax).

## 2. Proposed Architecture: The Saga Pattern

### A. Escrow-First Protocol
Instead of "Transfer then Rollback", use "Reserve then Commit":
1.  **Reserve**: Move funds from Buyer to `EscrowAccount`.
2.  **Validate**: Verify all conditions (inventory space, tax eligibility).
3.  **Commit**: Move funds from `EscrowAccount` to Seller and Government.
4.  **Compensate (on failure)**: Move funds from `EscrowAccount` back to Buyer.

### B. TransactionManager decoupling
- `SagaManager` will handle the orchestration of multi-agent transfers.
- `SettlementSystem` remains the atomic executor of individual transfers.

## 3. Implementation Plan
1.  **IEscrowProvider**: Interface for components that can hold funds temporarily.
2.  **SagaDefinition**: A declarative way to define multi-step transfers.
3.  **Refactor `TransactionProcessor`**: Move away from monolithic `process_transaction` to a saga-based execution.
