🕵️  Generating Report for: '# ⚖️ Domain Auditor: Systems, Persistence & LifeCycles

## Identity
You are the **Systems & Infrastructure Auditor**. Your focus is on the simulation's heartbeat, persistence layers, and cross-cutting concerns.

## Mission
Verify that the simulation's "plumbing" (Ticks, Persistence, Birth/Death) remains robust and doesn't introduce hidden leaks or performance degradations.

## Audit Checklist (SoC focus)
1. **Lifecycle Suture**: Do `LifecycleManager` events (Birth/Death) correctly update the `SettlementSystem`'s currency holders?
2. **Persistence Purity**: Does the `PersistenceManager` access agent internals incorrectly, or is it strictly using serialization interfaces?
3. **Tick Orchestration**: Is there logic drift between `ARCH_SEQUENCING.md` and `tick_orchestrator.py`?
4. **Resource Management**: Check for SQLite file lock risks or WebSocket leak patterns.

## Output Format
### 🚥 Domain Grade: [PASS/FAIL/WARNING]
### ❌ Violations
| File | Line | Violation | Severity |
| :--- | :--- | :--- | :--- |
### 💡 Abstracted Feedback (For Management)
Provide a 3-bullet summary of the most critical structural drift found.


[TASK]
Run this audit on the provided context files and output the result.'...
📖 Attached context: simulation\systems\accounting.py
📖 Attached context: simulation\systems\api.py
📖 Attached context: simulation\systems\bootstrapper.py
📖 Attached context: simulation\systems\central_bank_system.py
📖 Attached context: simulation\systems\commerce_system.py
📖 Attached context: simulation\systems\demographic_manager.py
📖 Attached context: simulation\systems\event_system.py
📖 Attached context: simulation\systems\firm_management.py
📖 Attached context: simulation\systems\generational_wealth_audit.py
📖 Attached context: simulation\systems\housing_system.py
📖 Attached context: simulation\systems\immigration_manager.py
📖 Attached context: simulation\systems\inheritance_manager.py
📖 Attached context: simulation\systems\labor_market_analyzer.py
📖 Attached context: simulation\systems\lifecycle_manager.py
📖 Attached context: simulation\systems\liquidation_handlers.py
📖 Attached context: simulation\systems\liquidation_manager.py
📖 Attached context: simulation\systems\ma_manager.py
📖 Attached context: simulation\systems\ministry_of_education.py
📖 Attached context: simulation\systems\persistence_manager.py
📖 Attached context: simulation\systems\registry.py
📖 Attached context: simulation\systems\sensory_system.py
📖 Attached context: simulation\systems\settlement_system.py
📖 Attached context: simulation\systems\social_system.py
📖 Attached context: simulation\systems\system_effects_manager.py
📖 Attached context: simulation\systems\tax_agency.py
📖 Attached context: simulation\systems\technology_manager.py
📖 Attached context: simulation\systems\transaction_manager.py
📖 Attached context: simulation\systems\transaction_processor.py
📖 Attached context: simulation\systems\__init__.py
📖 Attached context: simulation\systems\handlers\asset_transfer_handler.py
📖 Attached context: simulation\systems\handlers\emergency_handler.py
📖 Attached context: simulation\systems\handlers\escheatment_handler.py
📖 Attached context: simulation\systems\handlers\financial_handler.py
📖 Attached context: simulation\systems\handlers\goods_handler.py
📖 Attached context: simulation\systems\handlers\government_spending_handler.py
📖 Attached context: simulation\systems\handlers\inheritance_handler.py
📖 Attached context: simulation\systems\handlers\labor_handler.py
📖 Attached context: simulation\systems\handlers\monetary_handler.py
📖 Attached context: simulation\systems\handlers\public_manager_handler.py
📖 Attached context: simulation\systems\handlers\stock_handler.py
📖 Attached context: simulation\systems\handlers\__init__.py
📖 Attached context: simulation\systems\tech\api.py
📖 Attached context: utils\simulation_builder.py
📖 Attached context: design\1_governance\architecture\ARCH_SEQUENCING.md
🚀 [GeminiWorker] Running task with manual: reporter.md

✅ Report Saved: C:\coding\economics\reports\temp\report_20260206_230858_Domain_Auditor.md
============================================================
# 🚥 Domain Grade: WARNING

### ❌ Violations
| File | Line | Violation | Severity |
| :--- | :--- | :--- | :--- |
| `simulation\systems\persistence_manager.py` | 51 | Direct access to agent property: `agent.assets` | **High** |
| `simulation\systems\persistence_manager.py` | 56 | Direct access to agent property: `agent.is_employed` | **High** |
| `simulation\systems\persistence_manager.py` | 57 | Direct access to agent property: `agent.employer_id` | **High** |
| `simulation\systems\persistence_m
...
============================================================