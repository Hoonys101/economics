# Technical Insight Report: DTO Consistency Audit

## 1. Problem Phenomenon
During the audit of `simulation/dtos`, `simulation/models`, and `modules/**/api.py`, several inconsistencies and fragile patterns were identified:
- **Duplicate Concepts:** The system maintains both `StockOrder` (deprecated) and `CanonicalOrderDTO` (standard) for market orders. This forces the usage of adapter functions like `convert_legacy_order_to_canonical` which relies on duck typing (`hasattr`).
- **Fragile State Extraction:** The `FirmStateDTO.from_firm` factory method performs over 15 `hasattr` checks to scrape data from `Firm` objects. This indicates that `Firm` does not expose a clean, contract-based interface for state export.
- **Weak Typing:** `TransactionDTO` is defined as `Any` in `simulation/dtos/transactions.py`, bypassing type safety for critical financial records.

## 2. Root Cause Analysis
- **Organic Growth:** As the system evolved from a monolithic simulation to a modular architecture (modules/**), new DTOs were introduced (e.g., `CanonicalOrderDTO`) without fully removing the old ones (`StockOrder`).
- **Lack of Strict Protocols:** The `Firm` agent likely grew by adding attributes dynamically or via mixins, leading to `FirmStateDTO` having to "guess" which attributes are present using `hasattr`.
- **Backward Compatibility:** Efforts to maintain backward compatibility with legacy analysis tools or serialized data led to keeping `TransactionDTO = Any` and `StockOrder`.

## 3. Solution Implementation Details
The proposed consolidation plan involves:
1.  **Standardization:** Explicitly deprecate `StockOrder` and alias `Order` solely to `CanonicalOrderDTO`.
2.  **Protocol-Driven Design:** Introduce `IFirmStateProvider` interface. The `Firm` agent must implement this interface to return its state in a structured format, eliminating the need for `from_firm` to inspect internal attributes.
3.  **Type Safety:** Replace `TransactionDTO = Any` with the concrete `simulation.models.Transaction` dataclass.
4.  **Interface Consolidation:** Deprecate `IFinancialEntity` (single-currency) in favor of `IFinancialAgent` (multi-currency) across all modules.

## 4. Lessons Learned & Technical Debt Identified
- **DTO Purity:** DTOs should be dumb containers. Factory methods that perform logic or inspection (like `from_firm`) violate this purity and couple the DTO to the internal implementation of the source object.
- **Protocol Usage:** Agents should expose their state via strictly typed Protocols (`ISensoryDataProvider`, `IFirmStateProvider`) rather than allowing consumers to inspect them via `hasattr`.
- **Debt:** The existence of `convert_legacy_order_to_canonical` is technical debt that masks the underlying issue of inconsistent data structures.
