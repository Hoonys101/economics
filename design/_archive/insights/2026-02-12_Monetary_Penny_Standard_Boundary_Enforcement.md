# Implementation Insight: Government Penny Migration (IMPL-PENNY-GOV)

**Date:** 2026-02-12
**Author:** Jules (Agent)
**Scope:** `modules/government`, `simulation/systems/transaction_manager.py`
**Status:** Completed

## 1. Overview
This migration eliminates floating-point drift in government financial operations by enforcing integer-based (penny) calculations. It specifically targets tax collection, welfare distribution, and bond issuance, ensuring compliance with the "Penny Standard".

## 2. Key Changes

### 2.1. DTO & Interface Hardening
The following DTOs were refactored to use `int` for monetary values:
- **`modules/government/dtos.py`**:
    - `PaymentRequestDTO`: `amount: float` -> `int`
    - `TaxCollectionResultDTO`: `total_collected: float` -> `int`
    - `WelfareResultDTO`: `total_paid: float` -> `int`
    - `ExecutionResultDTO`: `monetary_ledger_updates: Dict[str, float]` -> `Dict[str, int]`
    - `TaxBracketDTO`: `floor` and `ceiling` -> `int`
    - `GovernmentStateDTO`: `assets`, `total_debt` -> `int` (Dict values and scalar)
- **`modules/government/treasury/api.py`**:
    - `BondDTO`: `face_value: float` -> `int`
    - `TreasuryOperationResultDTO`: `cash_exchanged: float` -> `int`
    - `ITreasuryService`: `target_cash_amount: float` -> `int`

### 2.2. Logic Updates
- **`FiscalPolicyManager`**:
    - Updated `determine_fiscal_stance` to treat market prices (`MarketSnapshotDTO`) as **Float Dollars**.
    - Explicitly converts dollars to pennies using `round_to_pennies(price * 100)`.
    - Removed unsafe heuristic checks (e.g., `if price < 1000.0`).
    - Calculates `survival_cost` and tax brackets in pennies.
- **`TaxService`**:
    - Updated `calculate_wealth_tax` to use `int` thresholds directly.
    - Removed legacy logic that multiplied config values by 100 dynamically. Now relies on `constants.py` providing correct penny values.
- **`TaxationSystem`**:
    - Updated `calculate_income_tax` and `calculate_corporate_tax` to perform integer math.
    - Updated `calculate_tax_intents` to handle `avg_food_price` as float dollars -> pennies.
- **`WelfareManager`**:
    - Updated `get_survival_cost` to return pennies (max(..., 1000)).
    - Updated welfare checks and bailouts to issue `PaymentRequestDTO` with integer amounts.

### 2.3. Constants
- **`modules/government/constants.py`**: Updated default financial constants to pennies:
    - `DEFAULT_WEALTH_TAX_THRESHOLD`: 50,000.0 -> 5,000,000
    - `DEFAULT_BASIC_FOOD_PRICE`: 5.0 -> 500
    - `DEFAULT_INFRASTRUCTURE_INVESTMENT_COST`: 5,000.0 -> 500,000

### 2.4. TransactionManager Adapter Hardening
- **`TransactionManager`**:
    - Removed heuristic checks for float-to-int conversion.
    - Standardized on `round_to_pennies(val * 100)` for food prices coming from market data (Float Dollars).
    - Ensures `Transaction` objects are created with integer trade values.

## 3. Assumptions & Guardrails
- **Market Prices are Dollars**: The system assumes `MarketSnapshotDTO` and live market data provide prices in float dollars (e.g., `5.0` for $5). This is converted to pennies (`500`) at the ingestion point (Government/TransactionManager).
- **Config Constants are Pennies**: `modules/government/constants.py` now defines defaults in pennies. Legacy config files (JSON) providing float dollars might need migration or rely on the explicit conversion logic added in `TaxationSystem` fallback paths.
- **Zero-Sum Integrity**: All tax and welfare transfers are now strictly integer-based, eliminating fractional penny leaks.

## 4. Verification
- **Unit Tests**: `modules/government/tax/tests/test_service.py` passes.
- **Migration Script**: `scripts/verify_penny_migration_gov.py` confirms correct handling of:
    - Wealth tax thresholds (int).
    - Survival cost calculation from dollar inputs.
    - Income tax brackets and liability (int).
    - Welfare floor logic ($10 min).

## 5. Residual Debt / Next Steps
- **Market System**: The Market System still uses floats for pricing (`MarketSnapshotDTO`). A future migration should standardize market prices to integers if possible, or formalize the Dollar interface.
- **Config Loading**: Ensure `ConfigManager` correctly handles type conversion for older config files if they assume dollars but the code now expects pennies (mostly handled by explicit checks, but worth monitoring).
