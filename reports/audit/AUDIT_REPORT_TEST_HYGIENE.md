# AUDIT_REPORT_TEST_HYGIENE: Test Hygiene Audit Report

## 1. Mock 품질 (Bare Mocks)
**Found 1390 occurrences of bare `MagicMock()` without spec.**

| File | Line | Content |
| :--- | :--- | :--- |
| `tests/test_server_auth.py` | 20 | `mock_sim = MagicMock()` |
| `tests/test_server_auth.py` | 22 | `mock_dashboard_service.return_value = MagicMock()` |
| `tests/test_firm_inventory_slots.py` | 14 | `core_config.logger = MagicMock()` |
| `tests/test_firm_inventory_slots.py` | 28 | `engine=MagicMock(),` |
| `tests/test_economic_tracker_precision.py` | 13 | `self.config_module = MagicMock()` |
| `tests/test_economic_tracker_precision.py` | 16 | `self.tracker.exchange_engine = MagicMock()` |
| `tests/test_economic_tracker_precision.py` | 26 | `h1._bio_state = MagicMock()` |
| `tests/test_economic_tracker_precision.py` | 31 | `h1._econ_state = MagicMock()` |
| `tests/test_economic_tracker_precision.py` | 41 | `h1._social_state = MagicMock()` |
| `tests/test_economic_tracker_precision.py` | 58 | `markets = {"goods": m1, "labor": MagicMock(), "loan_market": MagicMock(), "stock_market": MagicMock(` |
| `tests/test_firm_surgical_separation.py` | 21 | `mock_core_config = MagicMock()` |
| `tests/test_firm_surgical_separation.py` | 26 | `mock_decision_engine = MagicMock()` |
| `tests/test_firm_surgical_separation.py` | 58 | `firm.action_executor = MagicMock() # Mock execute_internal_orders delegate` |
| `tests/test_firm_surgical_separation.py` | 61 | `firm.execute_internal_orders = MagicMock()` |
| `tests/test_firm_surgical_separation.py` | 72 | `input_dto.market_snapshot = MagicMock()` |
| `tests/test_firm_surgical_separation.py` | 78 | `input_dto.market_snapshot.labor = MagicMock()` |
| `tests/test_firm_surgical_separation.py` | 97 | `mock_firm.hr_engine = MagicMock()` |
| `tests/test_firm_surgical_separation.py` | 110 | `mock_pricing_result = MagicMock()` |
| `tests/test_firm_surgical_separation.py` | 182 | `employee_mock = MagicMock()` |
| `tests/test_firm_surgical_separation.py` | 188 | `fiscal_context = MagicMock()` |
| `tests/test_firm_surgical_separation.py` | 196 | `mock_tx = MagicMock()` |
| `tests/test_firm_surgical_separation.py` | 202 | `mock_settlement = MagicMock()` |
| `tests/test_ghost_firm_prevention.py` | 21 | `sim.agent_registry = MagicMock()` |
| `tests/test_ghost_firm_prevention.py` | 22 | `sim.settlement_system = MagicMock()` |
| `tests/test_ghost_firm_prevention.py` | 23 | `sim.bank = MagicMock()` |
| `tests/test_ghost_firm_prevention.py` | 25 | `sim.world_state = MagicMock()` |
| `tests/test_ghost_firm_prevention.py` | 36 | `config_manager=MagicMock(),` |
| `tests/test_ghost_firm_prevention.py` | 37 | `config_module=MagicMock(),` |
| `tests/test_ghost_firm_prevention.py` | 39 | `repository=MagicMock(),` |
| `tests/test_ghost_firm_prevention.py` | 40 | `logger=MagicMock(),` |
| `tests/test_ghost_firm_prevention.py` | 43 | `ai_trainer=MagicMock()` |
| `tests/test_ghost_firm_prevention.py` | 78 | `central_bank = MagicMock()` |
| `tests/test_ghost_firm_prevention.py` | 81 | `firm.wallet = MagicMock()` |
| `tests/test_ghost_firm_prevention.py` | 83 | `settlement_system = MagicMock()` |
| `tests/test_ghost_firm_prevention.py` | 88 | `config = MagicMock()` |
| `tests/test_ghost_firm_prevention.py` | 102 | `central_bank = MagicMock()` |
| `tests/test_ghost_firm_prevention.py` | 103 | `agent = MagicMock() # Could be any agent, using generic` |
| `tests/test_ghost_firm_prevention.py` | 105 | `settlement_system = MagicMock()` |
| `tests/repro_td_issues.py` | 19 | `tracker = MagicMock()` |
| `tests/repro_td_issues.py` | 20 | `config = MagicMock()` |
| `tests/repro_td_issues.py` | 35 | `cb = MagicMock()` |
| `tests/repro_td_issues.py` | 41 | `config = MagicMock()` |
| `tests/repro_td_issues.py` | 43 | `gov.policy_lockout_manager = MagicMock()` |
| `tests/test_firm_brain_scan.py` | 26 | `mock_core_config = MagicMock()` |
| `tests/test_firm_brain_scan.py` | 31 | `mock_decision_engine = MagicMock()` |
| `tests/test_firm_brain_scan.py` | 33 | `mock_config_dto = MagicMock()` |
| `tests/test_firm_brain_scan.py` | 65 | `firm.action_executor = MagicMock() # Mock execute_internal_orders delegate` |
| `tests/test_firm_brain_scan.py` | 66 | `firm.execute_internal_orders = MagicMock() # Mock directly too` |
| `tests/test_firm_brain_scan.py` | 80 | `mock_budget = MagicMock()` |
| `tests/test_firm_brain_scan.py` | 132 | `override_snapshot = MagicMock() # spec=MarketSnapshotDTO causes issues if fields are missing` |
| ... | ... | *(1340 more items omitted)* |

## 2. DTO Substitution Anti-Pattern
No DTO substitution anti-patterns found in fixtures.

## 3. 커버리지 사각지대 (Coverage Blind Spots)
**Found 12 modules without corresponding test directories.**

- `agent_framework`
- `analytics`
- `hr`
- `events`
- `lifecycle`
- `inventory`
- `market`
- `platform`
- `api`
- `tools`
- `housing`
- `testing`

## 4. Fixture 조직 (Fixture Organization)
Fixture organization is clean.

## 5. Teardown 위생 (Teardown Hygiene)
**Found 49 test classes with `setUp` but no `tearDown`.**

| File | Class Name |
| :--- | :--- |
| `tests/test_economic_tracker_precision.py` | `TestEconomicTrackerPrecision` |
| `tests/test_liquidation_math.py` | `TestLiquidationMath` |
| `tests/common/test_protocol.py` | `TestProtocolShield` |
| `tests/integration/test_government_ai_logic.py` | `TestGovernmentAILogic` |
| `tests/integration/test_liquidation_waterfall.py` | `TestLiquidationWaterfallIntegration` |
| `tests/integration/test_generational_wealth_audit.py` | `TestGenerationalWealthAudit` |
| `tests/integration/test_liquidation_services.py` | `TestLiquidationServices` |
| `tests/integration/test_phase20_scaffolding.py` | `TestPhase20Scaffolding` |
| `tests/integration/test_multicurrency_liquidation.py` | `TestMultiCurrencyLiquidation` |
| `tests/integration/test_wo048_breeding.py` | `TestWO048Breeding` |
| `tests/integration/scenarios/verify_socio_tech_logic.py` | `TestHouseholdAI_TimeAllocation` |
| `tests/integration/scenarios/verify_multi_good_market.py` | `TestMultiGoodMarket` |
| `tests/integration/scenarios/verify_economic_equilibrium.py` | `TestEconomicConservation` |
| `tests/integration/scenarios/verify_service_market.py` | `TestServiceMarket` |
| `tests/integration/scenarios/verify_gold_standard.py` | `VerifyGoldStandard` |
| `tests/integration/scenarios/verify_labor_dynamics.py` | `TestLaborDynamics` |
| `tests/integration/scenarios/verify_wo103_phase1.py` | `TestWO103Phase1` |
| `tests/integration/scenarios/verify_population_dynamics.py` | `TestPopulationDynamics` |
| `tests/integration/scenarios/verify_corporate_tax.py` | `TestCorporateTax` |
| `tests/modules/household/test_marriage_system.py` | `TestMarriageSystem` |
| `tests/modules/firm/test_budget_gatekeeper.py` | `TestBudgetGatekeeper` |
| `tests/modules/finance/test_exchange_engine.py` | `TestCurrencyExchangeEngine` |
| `tests/system/test_audit_integrity.py` | `TestEconomicIntegrityAudit` |
| `tests/unit/test_sensory_purity.py` | `TestSensoryPurity` |
| `tests/unit/test_smart_leviathan_policy.py` | `TestSmartLeviathanPolicy` |
| `tests/unit/test_bank_decomposition.py` | `TestBankDecomposition` |
| `tests/unit/test_household_system2.py` | `TestHouseholdSystem2` |
| `tests/unit/test_learning_tracker.py` | `TestLearningTracker` |
| `tests/unit/test_metrics_hardening.py` | `TestMetricsHardening` |
| `tests/unit/test_marketing_roi.py` | `TestMarketingROI` |
| `tests/unit/test_handlers_fix.py` | `TestHandlerFix` |
| `tests/unit/test_api_history.py` | `TestHistoryAPI` |
| `tests/unit/test_transaction_handlers.py` | `TestGoodsTransactionHandler` |
| `tests/unit/test_transaction_handlers.py` | `TestLaborTransactionHandler` |
| `tests/unit/test_socio_tech.py` | `TestSocioTechDynamics` |
| `tests/unit/components/test_demographics_component.py` | `TestDemographicsComponent` |
| `tests/unit/systems/test_liquidation_manager.py` | `TestLiquidationManager` |
| `tests/unit/systems/test_firm_management_leak.py` | `TestFirmManagementLeak` |
| `tests/unit/systems/test_ministry_of_education.py` | `TestMinistryOfEducation` |
| `tests/unit/systems/test_firm_management_refactor.py` | `TestFirmManagementRefactor` |
| `tests/unit/systems/test_housing_system.py` | `TestHousingSystemRefactor` |
| `tests/unit/systems/test_ma_manager.py` | `TestMAManager` |
| `tests/unit/systems/test_tax_agency.py` | `TestTaxAgency` |
| `tests/unit/systems/handlers/test_liquidation_handlers.py` | `TestInventoryLiquidationHandler` |
| `tests/unit/systems/handlers/test_housing_handler.py` | `TestHousingTransactionHandler` |
| `tests/unit/finance/call_market/test_service.py` | `TestCallMarketService` |
| `tests/unit/simulation/systems/test_analytics_system_purity.py` | `TestAnalyticsSystemPurity` |
| `tests/unit/modules/government/components/test_monetary_policy_manager.py` | `TestMonetaryPolicyManager` |
| `tests/unit/modules/finance/test_double_entry.py` | `TestDoubleEntry` |

## 6. 검증 유틸리티 동기화 감사 (Verification Utilities)
- **`tests/integration/scenarios/verification/verify_inheritance.py`**: Contains bare MagicMock(), may not reflect recent DTO/Purity refactorings.
