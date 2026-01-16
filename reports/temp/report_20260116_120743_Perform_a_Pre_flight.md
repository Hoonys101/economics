# Pre-Flight Audit: Firm SoC Refactor

## Executive Summary
The `Firm` class currently exhibits significant coupling between production, sales, and financial logic. Key state variables like `inventory` and `inventory_quality` are directly modified by production and read by sales functions. The `update_needs` method is a critical nexus of mixed responsibilities, handling everything from marketing expenditure to inventory costs and tax payments. Refactoring into `ProductionDepartment` and `SalesDepartment` is feasible but will require careful state management and a clear definition of the order of operations to avoid logical inconsistencies.

## Detailed Analysis

### 1. Hidden Dependencies & Shared State
- **Status**: ⚠️ Partial
- **Evidence**:
    - `inventory`: `produce` method directly writes to `self.inventory` (`firms.py:L601`), which is a necessary input for the `SalesDepartment` to know what it can sell.
    - `inventory_quality`: `produce` calculates and writes the weighted average quality (`firms.py:L600`), which is then read by `post_ask` to create a `brand_snapshot` for sales orders (`firms.py:L415`). This creates a direct data flow dependency from Production to Sales.
    - `last_prices`: This dictionary is used by `_calculate_invisible_hand_price` (Sales/Pricing) as a baseline (`firms.py:L805`) and `get_inventory_value` (Finance/Valuation) (`firms.py:L391`). This shared state is read by multiple potential departments.
    - `specialization`: This attribute is fundamental to both `produce` to determine what to make, and sales logic like `post_ask` and `_calculate_invisible_hand_price` to identify the market and product.
    - `input_inventory`: Read and written by `produce` (`firms.py:L588, L595`), but the decision to purchase raw materials (inputs) would likely be driven by sales forecasts, creating an indirect dependency loop.
- **Notes**: The tightest coupling is between the output of `produce` and the inputs for `post_ask`. A `ProductionDepartment` must formally publish its output (quantity and quality) for the `SalesDepartment` to consume each tick.

### 2. Methods with Mixed Responsibilities
- **Status**: ⚠️ Partial
- **Evidence**:
    - `update_needs`: This is the primary method with mixed concerns. It handles:
        - **Production/Logistics**: Inventory holding costs (`firms.py:L825`).
        - **HR**: Triggers payroll processing (`firms.py:L836`).
        - **Sales/Marketing**: Calculates and applies marketing spend (`firms.py:L844-855`) and updates `BrandManager` (`firms.py:L859`).
        - **Finance**: Pays maintenance fees and taxes (`firms.py:L866-867`) and checks for bankruptcy (`firms.py:L876`).
    - `produce`: While mostly production-focused, it directly modifies the `inventory` and `inventory_quality` state (`firms.py:L600-601`) rather than returning its output to be managed by a separate inventory or state manager.
- **Notes**: The `update_needs` method should be dismantled, with its logic distributed to the appropriate new departments (`SalesDepartment` handles marketing, `ProductionDepartment` could handle holding costs, `FinanceDepartment` handles taxes).

### 3. Potential Circular Dependencies
- **Status**: ⚠️ Partial
- **Evidence**:
    - **Sales <-> Finance**: A logical dependency loop exists. The `_adjust_marketing_budget` function (Sales) requires `revenue_this_turn` and `last_revenue` from the `FinanceDepartment` (`firms.py:L473`). The `FinanceDepartment`, in turn, depends on sales transactions to calculate this revenue.
    - **Simulation/Top-Level**: No explicit circular dependencies with the `Simulation` object were found. External objects like `markets`, `government`, and `households` are passed down as method arguments (e.g., `make_decision`, `distribute_dividends`), which is a clean architectural pattern that avoids circular imports.
- **Notes**: The Sales/Finance loop is not an import cycle but a logical one that can be managed by a defined order of operations (e.g., decisions for tick `T` are based on results from tick `T-1`). This is standard practice and not a high-risk issue, but it must be maintained during refactoring.

## Risk Assessment
- **State Management**: The primary risk is managing shared state (`inventory`, `inventory_quality`, `capital_stock`) during the refactor. If both `ProductionDepartment` and `SalesDepartment` are allowed to modify this state directly, it could lead to race conditions or inconsistent data. A clear ownership model is needed (e.g., the `Firm` class owns the state, and departments operate on it via controlled methods).
- **Order of Operations**: Dismantling `update_needs` requires establishing a new, explicit sequence of calls at the `Firm` or `Simulation` level (e.g., `1. produce`, `2. run_sales_logic`, `3. pay_expenses`, `4. pay_taxes`). An incorrect order could lead to firms making decisions on stale data.
- **AI/Decision Context**: The `get_agent_data` method (`firms.py:L735`) aggregates data from all aspects of the firm for the AI. As logic is moved to new departments, this method will need significant rework to gather data from these new sources, which could be complex.

## Conclusion
The audit confirms that the `Firm` class is a strong candidate for a `Separation of Concerns` refactoring. The dependencies are identifiable and manageable. The proposed extraction of `ProductionDepartment` and `SalesDepartment` is feasible, provided that a clear plan is made for:
1.  Breaking down the `update_needs` method and re-assigning its responsibilities.
2.  Implementing a clear state management pattern for shared resources like `inventory`.
3.  Ensuring the logical order of operations between the new departments is preserved.
