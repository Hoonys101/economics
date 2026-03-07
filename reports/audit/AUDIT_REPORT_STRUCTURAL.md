# AUDIT_REPORT_STRUCTURAL: Structural Integrity Audit (v3.0)

## 1. Executive Summary
This report validates adherence to the 'DTO-based Decoupling' and 'Component SoC' architecture using static analysis as specified in `AUDIT_SPEC_STRUCTURAL.md`.

## 2. God Classes
The following classes exceed the 800-line threshold or have 15+ public methods, indicating a mix of responsibilities:
- `simulation/bank.py` -> `Bank`: 396 lines, 28 public methods
- `simulation/loan_market.py` -> `LoanMarket`: 409 lines, 15 public methods
- `simulation/firms.py` -> `Firm`: 1783 lines, 100 public methods
- `simulation/world_state.py` -> `WorldState`: 335 lines, 36 public methods
- `simulation/core_agents.py` -> `Household`: 1185 lines, 102 public methods
- `simulation/components/demographics_component.py` -> `DemographicsComponent`: 141 lines, 19 public methods
- `simulation/markets/order_book_market.py` -> `OrderBookMarket`: 408 lines, 23 public methods
- `simulation/markets/stock_market.py` -> `StockMarket`: 281 lines, 16 public methods
- `simulation/systems/settlement_system.py` -> `SettlementSystem`: 963 lines, 25 public methods
- `simulation/systems/lifecycle/adapters.py` -> `BirthContextAdapter`: 95 lines, 23 public methods
- `simulation/systems/lifecycle/adapters.py` -> `DeathContextAdapter`: 106 lines, 23 public methods
- `simulation/agents/government.py` -> `Government`: 739 lines, 37 public methods
- `simulation/agents/central_bank.py` -> `CentralBank`: 397 lines, 20 public methods
- `modules/labor/system.py` -> `LaborMarket`: 258 lines, 17 public methods
- `modules/household/mixins/_properties.py` -> `HouseholdPropertiesMixin`: 231 lines, 47 public methods
- `modules/finance/system.py` -> `FinanceSystem`: 556 lines, 17 public methods
- `modules/finance/kernel/ledger.py` -> `MonetaryLedger`: 266 lines, 16 public methods
- `modules/system/registry.py` -> `GlobalRegistry`: 276 lines, 15 public methods
- `modules/system/execution/public_manager.py` -> `PublicManager`: 305 lines, 22 public methods

## 3. Dependency Inversions (Static Coupling)
Files improperly importing from `tests/`:
- None detected.

## 4. Leaky Abstractions & DTO Pattern Violations
Files passing raw agent instances (e.g., `self`) into Contexts instead of DTOs:
- None detected (based on `DecisionContext` instantiation heuristics).

## 5. Protocol Evasion
The following files contain excessive dynamic type checking (`hasattr` / `isinstance`), bypassing type-safe Protocols:
- `simulation/systems/settlement_system.py`: 33 occurrences
- `simulation/systems/housing_system.py`: 24 occurrences
- `simulation/systems/registry.py`: 21 occurrences
- `simulation/systems/lifecycle/death_system.py`: 19 occurrences
- `simulation/systems/handlers/goods_handler.py`: 18 occurrences
- `simulation/firms.py`: 17 occurrences
- `modules/system/services/command_service.py`: 16 occurrences
- `simulation/ai/household_ai.py`: 15 occurrences
- `simulation/agents/government.py`: 14 occurrences
- `simulation/decisions/household/consumption_manager.py`: 13 occurrences
- `simulation/systems/event_system.py`: 13 occurrences
- `simulation/loan_market.py`: 12 occurrences
- `simulation/decisions/ai_driven_firm_engine.py`: 12 occurrences
- `simulation/orchestration/phases/decision.py`: 12 occurrences
- `simulation/orchestration/phases/metrics.py`: 12 occurrences
- `simulation/systems/handlers/stock_handler.py`: 12 occurrences
- `modules/lifecycle/manager.py`: 11 occurrences
- `modules/housing/service.py`: 11 occurrences
- `simulation/orchestration/phases/post_sequence.py`: 10 occurrences
- `simulation/systems/handlers/monetary_handler.py`: 10 occurrences

## 6. WorldState Purity
- `WorldState` appears pure. No obvious direct instantiation of Services detected.

## 7. Sacred Sequence Integrity
- The execution sequence `Decisions -> Matching -> Transactions -> Lifecycle` appears intact.
