# Mission Guide: Phase 10.3 Structural Integrity (Judicial Waterfall & Finance Commands)

## 1. Objectives
- **[TD-JUD-ASSET]**: Implement Hierarchical Seizure Waterfall (Cash -> Stock -> Inventory) in `JudicialSystem`.
- **[TD-FIN-PURE]**: Purify `FinanceSystem` by separating Loan Validation (Stateless) from Execution (Saga/Orchestrator).

## 2. Core Components (Reference Context)
- **Judicial System**:
  - API: [modules/governance/judicial/api.py](file:///c:/coding/economics/modules/governance/judicial/api.py)
  - Implementation: [modules/governance/judicial/system.py](file:///c:/coding/economics/modules/governance/judicial/system.py)
- **Finance System**:
  - API: [modules/finance/api.py](file:///c:/coding/economics/modules/finance/api.py)
  - Implementation: [modules/finance/system.py](file:///c:/coding/economics/modules/finance/system.py)
- **Technical Specification**: [spec_ph10_3_judicial_finance.md](file:///C:/Users/Gram%20Pro/.gemini/antigravity/brain/0cb8ba1c-c94d-4541-8e7f-e99f34c009f7/spec_ph10_3_judicial_finance.md)

## 3. Implementation Roadmap

### Phase 1: Judicial Seizure Waterfall
1.  **API Update**:
    - Define `SeizureWaterfallResultDTO`.
    - Define `DebtRestructuringRequiredEvent` (Event Type: `DEBT_RESTRUCTURING_REQUIRED`).
2.  **Implementation Refactor**:
    - Rename `execute_asset_seizure` to `execute_seizure_waterfall`.
    - Implement hierarchical logic:
      - **Stage 1 (Cash)**: Check `IFinancialEntity.assets`.
      - **Stage 2 (Stocks)**: Check `IPortfolioHandler` (if available, clear portfolio).
      - **Stage 3 (Inventory)**: Check `ILiquidatable` (per TD-269).
    - If debt remains after all stages, publish `DEBT_RESTRUCTURING_REQUIRED`.

### Phase 2: Finance System Command Pattern
1.  **API Update**:
    - Define `GrantBailoutCommand` (encapsulates amount, interest, covenants).
2.  **Implementation Refactor**:
    - Refactor `grant_bailout_loan` into `request_bailout_loan`.
    - **Rule**: `request_bailout_loan` MUST be stateless. It validates the government budget, calculates terms, and returns the `GrantBailoutCommand`. It MUST NOT update the firm's state or trigger the `SettlementSystem` directly.

## 4. Verification (Success Criteria)
- [ ] `pytest tests/unit/governance/test_judicial_system.py`: Update to verify the waterfall stages and event emission.
- [ ] `pytest tests/unit/finance/test_finance_system.py` (or equivalent): Verify `request_bailout_loan` returns the correct Command DTO without side-effects.
- [ ] No monetary leaks (M2 integrity) during test executions.
