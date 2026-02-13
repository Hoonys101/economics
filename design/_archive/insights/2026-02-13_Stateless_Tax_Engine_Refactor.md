# Insight: MS-0128 Tax Engine Refactoring

**Date:** 2024-05-22
**Author:** Jules (AI Assistant)
**Related Spec:** `design/3_work_artifacts/specs/tax_engine_spec.md`

## Overview
This document captures insights and challenges identified during the refactoring of the stateful `TaxService` into a purely functional `TaxEngine`.

## Problem Statement
The legacy `TaxService` (God Object) directly mutated agent state, creating hidden dependencies and making the system difficult to test and reason about. It also mixed tax calculation logic (pure) with tax collection logic (side-effect).

## Challenges Identified

### 1. Ambiguity of Taxable Income
- **Definition:** What constitutes "taxable income" is not consistently defined across the simulation.
- **Components:** Gross income, net income, capital gains, and government transfers.
- **Resolution:** The new engine requires a strict `TaxPayerDetailsDTO` where `taxable_income` is a single, pre-aggregated float. This pushes the complexity of defining income to the orchestrator (or the agent itself), making the engine simpler and purely calculation-based.

### 2. Stateful Dependencies
- **Implicit Inputs:** The old service implicitly relied on agent attributes like `agent.assets` or `agent.inventory`.
- **Side Effects:** The old service directly deducted tax from `agent.wallet`, bypassing the `SettlementSystem` in some cases.
- **Resolution:** The new `TaxEngine` is stateless. It takes `TaxPayerDetailsDTO` as input and returns `TaxCalculationOutputDTO`. All state mutations (deductions) are handled by the orchestrator via the `SettlementSystem`.

### 3. Verification Gaps
- **Testing:** The old service was difficult to unit test due to its dependencies on the entire simulation state.
- **Resolution:** The new engine is purely functional and can be exhaustively unit tested with simple DTO inputs.

## Recommendations
1. **Strict Separation:** Enforce a strict separation between calculation (Engine) and collection (Orchestrator).
2. **Standardized Input:** Use the `TaxPayerDetailsDTO` as the canonical definition of a taxpayer's financial status for tax purposes.
3. **Audit Trail:** The orchestrator must log the calculation results before executing the collection, providing a clear audit trail.

## Status
This refactoring is a critical step in the SEO hardening initiative. The insights here guide the implementation of the new `TaxEngine` and the rewritten `TaxService` orchestrator.
