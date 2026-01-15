🕵️  Generating Report for: 'Task: Identify all hardcoded magic numbers and rule-based heuristics across the codebase. Focus: 1) config.py: Arbitrary constants. 2) simulation/agents/: Hardcoded thresholds, fixed rates, and deterministic if/else decision logic. 3) simulation/systems/: Rigid formulas that should be adaptive. Output: A detailed list of Technical Debts (TD-XXX) with file paths, code snippets, and why they require re-planning for 'Adaptive AI Migration'.'...
📖 Attached context: simulation\ai_model.py
📖 Attached context: simulation\api.py
📖 Attached context: simulation\bank.py
📖 Attached context: simulation\base_agent.py
📖 Attached context: simulation\core_agents.py
📖 Attached context: simulation\core_markets.py
📖 Attached context: simulation\decisions.py
📖 Attached context: simulation\dtos.py
📖 Attached context: simulation\engine.py
📖 Attached context: simulation\firms.py
📖 Attached context: simulation\loan_market.py
📖 Attached context: simulation\models.py
📖 Attached context: simulation\portfolio.py
📖 Attached context: simulation\schemas.py
📖 Attached context: simulation\service_firms.py
📖 Attached context: simulation\__init__.py
📖 Attached context: simulation\agents\central_bank.py
📖 Attached context: simulation\agents\government.py
📖 Attached context: simulation\ai\action_selector.py
📖 Attached context: simulation\ai\ai_training_manager.py
📖 Attached context: simulation\ai\api.py
📖 Attached context: simulation\ai\engine_registry.py
📖 Attached context: simulation\ai\enums.py
📖 Attached context: simulation\ai\firm_ai.py
📖 Attached context: simulation\ai\firm_system2_planner.py
📖 Attached context: simulation\ai\government_ai.py
📖 Attached context: simulation\ai\household_ai.py
📖 Attached context: simulation\ai\household_system2.py
📖 Attached context: simulation\ai\learning_tracker.py
📖 Attached context: simulation\ai\model_wrapper.py
📖 Attached context: simulation\ai\q_table_manager.py
📖 Attached context: simulation\ai\reward_calculator.py
📖 Attached context: simulation\ai\service_firm_ai.py
📖 Attached context: simulation\ai\state_builder.py
📖 Attached context: simulation\ai\system2_planner.py
📖 Attached context: simulation\ai\vectorized_planner.py
📖 Attached context: simulation\ai\__init__.py
📖 Attached context: simulation\brands\brand_manager.py
📖 Attached context: simulation\components\consumption_behavior.py
📖 Attached context: simulation\components\finance_department.py
📖 Attached context: simulation\components\hr_department.py
📖 Attached context: simulation\components\leisure_manager.py
📖 Attached context: simulation\components\psychology_component.py
📖 Attached context: simulation\db\database.py
📖 Attached context: simulation\db\db_manager.py
📖 Attached context: simulation\db\repository.py
📖 Attached context: simulation\db\schema.py
📖 Attached context: simulation\decisions\action_proposal.py
📖 Attached context: simulation\decisions\ai_driven_firm_engine.py
📖 Attached context: simulation\decisions\ai_driven_household_engine.py
📖 Attached context: simulation\decisions\base_decision_engine.py
📖 Attached context: simulation\decisions\corporate_manager.py
📖 Attached context: simulation\decisions\housing_manager.py
📖 Attached context: simulation\decisions\portfolio_manager.py
📖 Attached context: simulation\decisions\rule_based_firm_engine.py
📖 Attached context: simulation\decisions\rule_based_household_engine.py
📖 Attached context: simulation\decisions\standalone_rule_based_firm_engine.py
📖 Attached context: simulation\decisions\__init__.py
📖 Attached context: simulation\interface\dashboard_connector.py
📖 Attached context: simulation\interface\__init__.py
📖 Attached context: simulation\interfaces\policy_interface.py
📖 Attached context: simulation\markets\order_book_market.py
📖 Attached context: simulation\markets\stock_market.py
📖 Attached context: simulation\markets\__init__.py
📖 Attached context: simulation\metrics\economic_tracker.py
📖 Attached context: simulation\metrics\inequality_tracker.py
📖 Attached context: simulation\metrics\stock_tracker.py
📖 Attached context: simulation\policies\smart_leviathan_policy.py
📖 Attached context: simulation\policies\taylor_rule_policy.py
📖 Attached context: simulation\systems\bootstrapper.py
📖 Attached context: simulation\systems\demographic_manager.py
📖 Attached context: simulation\systems\firm_management.py
📖 Attached context: simulation\systems\generational_wealth_audit.py
📖 Attached context: simulation\systems\housing_system.py
📖 Attached context: simulation\systems\immigration_manager.py
📖 Attached context: simulation\systems\inheritance_manager.py
📖 Attached context: simulation\systems\ma_manager.py
📖 Attached context: simulation\systems\ministry_of_education.py
📖 Attached context: simulation\systems\persistence_manager.py
📖 Attached context: simulation\systems\reflux_system.py
📖 Attached context: simulation\systems\tax_agency.py
📖 Attached context: simulation\systems\technology_manager.py
📖 Attached context: simulation\systems\transaction_processor.py
📖 Attached context: simulation\utils\shadow_logger.py
📖 Attached context: simulation\viewmodels\agent_state_viewmodel.py
📖 Attached context: simulation\viewmodels\economic_indicators_viewmodel.py
📖 Attached context: simulation\viewmodels\market_history_viewmodel.py
📖 Attached context: simulation\viewmodels\snapshot_viewmodel.py
📖 Attached context: config.py
🚀 [GeminiWorker] Running task with manual: reporter.md

✅ Report Saved: C:\coding\economics\reports\temp\report_20260115_133455_Task__Identify_all_h.md
============================================================
# Report: Analysis of Hardcoded Heuristics and Technical Debt

## Executive Summary
The codebase contains a significant amount of technical debt in the form of hardcoded "magic numbers," fixed thresholds, and rule-based heuristics. This makes the simulation rigid and predictable. Migrating to a truly adaptive AI system will require refactoring these components into dynamic, learnable mechanisms.

## Detailed Analysis

### 1. Configuration File (`config.py`)
The `config.py` file centralizes many 
...
============================================================
