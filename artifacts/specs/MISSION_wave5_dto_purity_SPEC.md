# MISSION SPEC: wave5-dto-purity

## 🎯 Objective
Resolve outstanding Data and DTO Purity technical debts to ensure consistent data contracts across the UI and Market modules.

## 🛠️ Target Tech Debts
1. **TD-UI-DTO-PURITY (Medium)**: Cockpit UI uses dict indexing instead of Pydantic models for telemetry.
    - **Symptom**: `dashboard/` (or similar UI layer) manually deserializes websocket payloads.
    - **Goal**: Enforce Pydantic DTO usage in the frontend-backend event interface.
2. **TD-DEPR-STOCK-DTO (Low)**: `StockOrder` is deprecated.
    - **Symptom**: Legacy usage of `StockOrder` in `modules/market/` or agent logic.
    - **Goal**: Replace all occurrences with `CanonicalOrderDTO`.

## 📜 Instructions for Gemini
1. **Analyze**: Search for `StockOrder` and identify its call sites. Review the UI/telemetry data ingestion flow (likely around `modules/system/telemetry_exchange.py` or `.ts`/UI equivalent if applicable).
2. **Plan**: Formulate the required changes to enforce `CanonicalOrderDTO` and update the UI serialization/deserialization logic.
3. **Spec Output**: Generate a precise, actionable Jules implementation spec that details exactly which files to edit, what lines to change, and how to verify the fix using `pytest`.

Ensure the spec adheres to the project's strict Zero-Sum and Protocol Purity guardrails.
