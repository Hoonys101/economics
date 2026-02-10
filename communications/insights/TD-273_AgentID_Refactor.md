# Technical Insight Report: Unified Agent ID Refactor (TD-273)

## 1. Problem Phenomenon
The codebase currently exhibits inconsistent handling of agent identifiers, leading to "stringly-typed" logic and potential runtime errors.
- **Symptoms**:
  - `IBank` interface expects `borrower_id: str`, but `Bank` implementation strictly converts it to `int` and fails otherwise.
  - `LoanInfoDTO`, `DebtStatusDTO`, and `BorrowerProfileDTO` use `str` for IDs, while `ShareholderData`, `LoanDTO`, and `DepositDTO` use `int`.
  - `WorldState.resolve_agent_id` converts string roles like "GOVERNMENT" to `int` IDs, but this logic is ad-hoc.
  - Callers like `LoanMarket` and `HousingTransactionHandler` explicitly cast `agent.id` (int) to `str()` to satisfy mismatched interfaces.
- **Stack Traces**: None observed yet, but the code is fragile. If a non-integer string (e.g., "GOVERNMENT") were passed to `Bank.grant_loan`, it would log an error and return `None` (silent failure or unexpected behavior in callers).

## 2. Root Cause Analysis
- **Historical Drift**: The system likely started with integer IDs, but string IDs were introduced for special agents (Government) or UUIDs (Loans). Interfaces were patched to accept `str` to accommodate these cases without a unified strategy.
- **Lack of Canonical Type**: There was no single source of truth for what an "Agent ID" is.
- **Protocol/Implementation Mismatch**: Interfaces (`Protocol`) were defined with `str` to be flexible/safe, but concrete implementations (`Bank`, `LoanManager`) enforced `int` logic.

## 3. Solution Implementation Details
- **Unified Type Definition**: Introduce `AgentID = NewType('AgentID', int)` and `SpecialAgentRole` literals in `modules/simulation/api.py`.
- **Interface Refactoring**:
  - Update `IBank`, `IFinancialAgent`, `IShareholderRegistry` and related DTOs (`LoanInfoDTO`, `BorrowerProfileDTO`, etc.) to use `AgentID`.
  - Remove `str` type hints for agent IDs.
- **Implementation Updates**:
  - Remove `int(id_str)` casting in `Bank` and `LoanManager`.
  - Remove `str(id_int)` casting in `LoanMarket` and `HousingTransactionHandler`.
  - Update `WorldState.agents` to `Dict[AgentID, Any]`.
- **Backward Compatibility**: `AgentID` is distinct at type-check time but compatible with `int` at runtime, minimizing disruption to logic that treats IDs as numbers (e.g., `id > 0`).

## 4. Lessons Learned & Technical Debt Identified
- **Strict Typing Pays Off**: Stringly-typed interfaces hide assumptions (e.g., "this string must be an int").
- **DTO Consistency**: DTOs crossing module boundaries must share common primitive types.
- **Protocol/Impl Alignment**: Protocols should reflect the actual constraints of the domain, not just the lowest common denominator (string).

**Technical Debt Resolved**: TD-273 (Stringly-Typed Agent Identifiers).
