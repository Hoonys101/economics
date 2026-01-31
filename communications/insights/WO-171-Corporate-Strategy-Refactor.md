# WO-171: Corporate Strategy Refactor

## 1. Context
The user requested the decomposition of `corporate_manager.py` into strategic modules: `FinancialStrategy`, `ProductionStrategy`, and `HRStrategy`.
Upon inspection, `CorporateManager` was already delegating logic to `FinanceManager`, `OperationsManager`, and `HRManager`.
This task primarily involves refactoring these components to match the requested naming convention ("Strategy") and ensuring the "Component Pattern" is strictly followed.

## 2. Changes
- **FinanceManager** -> **FinancialStrategy**: Direct rename.
- **HRManager** -> **HRStrategy**: Direct rename.
- **OperationsManager** -> **ProductionStrategy**: Renamed to satisfy the user request.
  - *Insight*: `OperationsManager` handled Production, Procurement, Automation, R&D, and Capex. Renaming it to `ProductionStrategy` might imply a narrower scope, but we retained the full scope to preserve functionality. In the future, R&D and Capex might deserve their own strategies (e.g., `InnovationStrategy`, `InvestmentStrategy`).

## 3. Technical Debt & Observations
- **Scope of ProductionStrategy**: The name `ProductionStrategy` is slightly misleading as it covers all non-Sales/HR/Finance operations, including R&D and Capex. This was done to match the user's explicit extraction targets without over-fragmenting the codebase abruptly.
- **CorporateManager**: Remains as the Orchestrator (Facade) for the firm's decision-making process.
- **SalesManager**: Left as `SalesManager` as it was not in the extraction list, though for consistency it could be `SalesStrategy`.

## 4. Verification
- Verified that all logic remains intact after renaming.
- Updated unit tests to reflect new class names.
