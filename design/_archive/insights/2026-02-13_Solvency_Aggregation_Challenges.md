# Insight: MS-0128 Solvency Data Aggregation

**Date:** 2024-05-22
**Author:** Jules (AI Assistant)
**Related Spec:** `design/3_work_artifacts/specs/finance_solvency_spec.md`

## Overview
This document outlines the complexities and challenges associated with defining and aggregating "total assets" and "total liabilities" for different agent types (Firms, Households, Government) within the new Solvency Check Engine.

## Challenges

### 1. Definition of "Asset"
The term "asset" is currently ambiguous in the context of solvency.
- **Physical Assets:** How should inventory be valued? At cost, market price, or a discounted "liquidation value"?
- **Financial Assets:** Cash is straightforward, but what about illiquid financial instruments like long-term bonds or pending receivables?
- **Intangible Assets:** Should brand value or intellectual property be considered for solvency? Current recommendation is to exclude these to ensure a conservative assessment.

### 2. Liability Aggregation
Aggregating liabilities is also non-trivial.
- **Short-term vs. Long-term:** Should all debt be treated equally? A firm might be solvent in the long run but illiquid in the short run. The current simple `total_liabilities` metric might be too blunt.
- **Contingent Liabilities:** Pending lawsuits or warranties are difficult to quantify but represent real financial risk.

### 3. Agent-Specific Nuances
- **Firms:** Have complex balance sheets with inventory, machines, and potentially inter-firm loans.
- **Households:** Assets include housing (illiquid) and cash. Liabilities are primarily mortgages.
- **Government:** The concept of "solvency" is different for a sovereign entity that can issue currency (though in this simulation, we enforce constraints).

## Recommendations
1. **Conservative Valuation:** For the initial implementation, value all non-cash assets at a discount (e.g., 50% of market price) to provide a safety margin.
2. **Standardized DTOs:** Use strict DTOs to enforce what counts as an asset/liability, preventing "creative accounting" by agents.
3. **Iterative Refinement:** Start with a simple `Cash + Inventory (Discounted) - Total Debt` formula and refine as the simulation evolves.

## Status
This insight serves as a prerequisite for the implementation of the `SolvencyCheckEngine`. The orchestrator responsible for populating the `SolvencyCheckInputDTO` must implement the logic to aggregate these values according to the decisions made here.
