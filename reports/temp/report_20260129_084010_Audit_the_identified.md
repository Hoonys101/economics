# Report: God File SoC Audit & Refactoring Plan

## Executive Summary
The audit of `SimulationRepository`, `AIDrivenHouseholdDecisionEngine`, and `CorporateManager` confirms significant violations of the Separation of Concerns (SoC) principle. These "God Files" consolidate numerous, distinct responsibilities, making them brittle, difficult to maintain, and a bottleneck for future development. This report proposes a detailed refactoring plan to decompose these monolithic classes into smaller, specialized, and more maintainable modules.

## Detailed Analysis

### 1. `simulation/db/repository.py` (`SimulationRepository`)
- **Status**: ❌ Missing (Proper SoC)
- **Violation**: This class acts as a single data access layer for the entire simulation, managing persistence for at least 6 different domain entities. It improperly combines generic data storage with domain-specific analytical queries.
- **Evidence**:
    - **Multiple Entity Management**: `save_transaction`, `save_agent_state`, `save_market_history`, `save_economic_indicator`, `save_ai_decision` all reside in one class (`repository.py:L78-232`).
    - **Mixed Responsibilities**: The class includes both generic batch-saving methods (`save_agent_states_batch`) and highly specific analytical queries like `get_generation_stats` (`repository.py:L430-444`) and `get_attrition_counts` (`repository.py:L446-512`).

### 2. `simulation/decisions/ai_driven_household_engine.py` (`AIDrivenHouseholdDecisionEngine`)
- **Status**: ❌ Missing (Proper SoC)
- **Violation**: This class is a monolithic "brain" for household agents, intertwining unrelated concerns such as daily consumption, long-term financial planning, housing, and labor decisions.
- **Evidence**:
    - **Consumption Logic**: Handles purchasing of all goods, from basic food to Veblen-effect luxury items (`ai_driven_household_engine.py:L82-211`).
    - **Labor Logic**: Manages job quitting and seeking employment, including reservation wage calculation (`ai_driven_household_engine.py:L214-272`).
    - **Financial Management**: Contains distinct logic for general portfolio management (`_manage_portfolio`), stock trading (`_make_stock_investment_decisions`), and debt/liquidity management (`_check_emergency_liquidity`) (`ai_driven_household_engine.py:L377-526`).
    - **Housing Logic**: A dedicated `HousingManager` is used within the main decision method to handle real estate purchases (`ai_driven_household_engine.py:L344-374`).

### 3. `simulation/decisions/corporate_manager.py` (`CorporateManager`)
- **Status**: ❌ Missing (Proper SoC)
- **Violation**: This "CEO" class centralizes all corporate functions into a single manager. It acts as the department head for HR, Finance, Production, Sales, and R&D simultaneously.
- **Evidence**:
    - **HR Functions**: Manages hiring, firing, severance pay, and competitive wage adjustments (`corporate_manager.py:L268-356`).
    - **Financial Functions**: Manages debt/leverage (`_manage_debt`), dividend policy (`_manage_dividends`), and equity offerings (`_attempt_secondary_offering`) (`corporate_manager.py:L106-129`, `L166-224`).
    - **Operations/Production**: Manages production targets, raw material procurement, and CAPEX/R&D/Automation investments (`corporate_manager.py:L131-164`, `L358-386`).
    - **Sales/Pricing**: Sets product prices and creates market sell orders (`corporate_manager.py:L226-266`).

## Risk Assessment
- **High Maintenance Cost**: A small change in one domain (e.g., dividend policy) requires understanding and modifying a massive file, increasing cognitive load and the risk of unintended side effects.
- **Low Reusability**: The logic is tightly coupled, making it impossible to reuse, for example, the `PortfolioManager` logic for a different type of agent without significant refactoring.
- **Difficult to Test**: Unit testing becomes extremely complex as mocking the numerous dependencies for a single method is impractical.
- **Bottleneck for Parallel Development**: Multiple developers working on different aspects of household or firm behavior would constantly face merge conflicts in these central files.

## Refactoring Plan

### 1. Refactor `SimulationRepository`

**Objective**: Decompose the God Repository into smaller, entity-specific repositories.

| New Module | Responsibility | Code to Move (from `SimulationRepository`) |
| :--- | :--- | :--- |
| `simulation/db/agent_repository.py` | CRUD for `agent_states`. Agent-specific queries. | `save_agent_state`, `save_agent_states_batch`, `get_agent_states`, `get_generation_stats`, `get_attrition_counts` |
| `simulation/db/market_repository.py` | CRUD for `transactions` and `market_history`. | `save_transaction`, `save_transactions_batch`, `save_market_history`, `save_market_history_batch`, `get_transactions`, `get_market_history` |
| `simulation/db/analytics_repository.py`| CRUD for `economic_indicators` and `ai_decisions_history`. | `save_economic_indicator`, `save_economic_indicators_batch`, `get_economic_indicators`, `get_latest_economic_indicator`, `save_ai_decision` |
| `simulation/db/run_repository.py` | CRUD for `simulation_runs`. | `save_simulation_run`, `update_simulation_run_end_time` |

### 2. Refactor `AIDrivenHouseholdDecisionEngine`

**Objective**: Delegate specific decisions to specialized sub-managers. The engine becomes a coordinator.

| New Module | Responsibility | Code to Move (from `AIDrivenHouseholdDecisionEngine`) |
| :--- | :--- | :--- |
| `simulation/decisions/household/consumption_manager.py` | Manages all buy orders for goods. Calculates utility, handles hoarding/Veblen effects, and determines WTP. | The main loop over `goods_list` in `_make_decisions_internal` (`L82-211`). |
| `simulation/decisions/household/labor_manager.py` | Manages all labor-related decisions: quitting, seeking jobs, and calculating reservation wage. | All logic for `is_employed` and `not is_employed` scenarios (`L214-272`). |
| `simulation/decisions/household/asset_manager.py` | A high-level manager that uses the `PortfolioManager` and a new `StockManager` to handle all financial asset decisions. | `_manage_portfolio`, `_check_emergency_liquidity`. It will orchestrate the other financial modules. |
| `simulation/decisions/household/stock_trader.py` | Manages buying and selling stocks based on a target equity allocation. | `_make_stock_investment_decisions`, `_place_buy_orders`, `_place_sell_orders` (`L443-526`). |
| `simulation/decisions/household/housing_manager.py` | (Already exists conceptually) Formalize its role. It should be instantiated and called by the engine, not have its logic embedded. | All logic related to `HousingManager` and real estate (`L344-374`). |

### 3. Refactor `CorporateManager`

**Objective**: Model the `CorporateManager` as a C-Suite that delegates tasks to departmental managers.

| New Module | Responsibility | Code to Move (from `CorporateManager`) |
| :--- | :--- | :--- |
| `simulation/decisions/firm/hr_manager.py` | Manages all employee-related actions: hiring, firing, wage setting, and severance. | `_manage_hiring`, `_adjust_wage_for_vacancies` (`L268-356`). |
| `simulation/decisions/firm/finance_manager.py` | Manages the firm's capital structure: debt, dividends, and equity offerings (SEOs). | `_manage_debt`, `_manage_dividends`, `_attempt_secondary_offering` (`L106-129`, `L166-224`). |
| `simulation/decisions/firm/operations_manager.py`| Manages production, procurement, and capital investments (CAPEX, R&D, Automation). | `_manage_production_target`, `_manage_procurement`, `_manage_automation`, `_manage_r_and_d`, `_manage_capex` (`L73-90`, `L131-164`, `L358-386`). |
| `simulation/decisions/firm/sales_manager.py` | Manages inventory, pricing strategy, and posting offers to the market. | `_manage_pricing` (`L226-266`). |

## Conclusion
The current design, while functional, has accumulated significant technical debt by violating SoC principles. The proposed refactoring will introduce a modular, maintainable, and scalable architecture. By breaking down these God Files, the system will become more robust, easier to test, and better equipped to handle future complexity. It is strongly recommended to prioritize this refactoring effort to ensure the long-term health of the codebase.
