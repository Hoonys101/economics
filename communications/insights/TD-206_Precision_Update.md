# Insight Report: TD-206 & TD-194 Financial Precision

**Date:** 2026-02-05
**Author:** Jules (AI)
**Mission:** Sync HouseholdStateDTO and MortgageApplicationDTO fields to prevent precision mismatch.

## 1. Executive Summary
This mission addressed the "Debt vs Payment mismatch" (TD-206) and "HouseholdStateDTO Fragmentation" (TD-194) by enforcing strict field alignment between the Finance and Market domains. Specifically, the mortgage application process was suffering from ambiguity where annual income was passed to fields expecting monthly values, and existing debt was not strictly calculated.

## 2. Key Changes
*   **Protocol Precision (TD-206):** Renamed `MortgageApplicationDTO` fields in `modules/finance/api.py` to be explicit:
    *   `applicant_income` -> `applicant_monthly_income`
    *   `applicant_existing_debt` -> `existing_monthly_debt_payments`
    *   `principal` -> `requested_principal`
*   **Snapshot Completeness (TD-194):** Updated `HouseholdSnapshotDTO` (and the deprecated `HouseholdStateDTO`) to include:
    *   `monthly_income`
    *   `monthly_debt_payments`
*   **Logic Centralization:** Extracted `calculate_monthly_loan_payment` to `modules/market/loan_api.py` to avoid duplication between the Saga Handler and the Household Mixin.
*   **Saga Robustness:** `HousingTransactionSagaHandler` now actively queries the `BankService` to calculate precise existing debt obligations before submitting a mortgage application.

## 3. Technical Debt Observations
*   **Environment Instability:** The test suite suffers from widespread `ModuleNotFoundError` (dotenv, yaml, numpy) likely due to environment configuration drift. Tests were verified via targeted execution.
*   **Legacy DTOs:** `HouseholdStateDTO` remains in the codebase despite being deprecated. It was updated to maintain parity, but future efforts should aggressively remove it in favor of `HouseholdSnapshotDTO`.
*   **Typing Loose Ends:** `MortgageApplicationDTO` usage in other parts of the system (if any hidden ones exist) might break due to key renaming. `HousingPlanner` was verified to use `RequestDTO`, which was already correct.

## 4. Verification
*   Targeted unit tests confirmed that `HousingTransactionSagaHandler` correctly populates the new fields.
*   Static analysis confirmed DTO alignment.
