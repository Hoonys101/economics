# Mission Guide: Government & Welfare Complete Refactor [Bundle A]

This document consolidates the requirements for the Government module decoupling and the implementation of its full test suite.

## 1. Objectives
- **TD-226/227/228**: Decouple Government Agent into stateless services (`WelfareManager`, `TaxService`).
- **TD-300**: Stabilize DTO contracts for Government interactions.
- **TD-234**: Replace raw agent `hasattr` checks with DTO/Protocol interfaces in `WelfareService`.
- **TD-183**: Update sequence documentation to match the new orchestrator flow.
- **TD-229**: Implementation of full Test Suite (TDD approach required).

## 2. Reference Context (MUST READ)
- **Primary Spec**: [Government Decoupling & SRP Refactor](file:///c:/coding/economics/design/3_work_artifacts/drafts/draft_232211__ObjectivenResolve_TD226_.md)
- **Test Strategy**: [Government Module Test Strategy](file:///c:/coding/economics/design/3_work_artifacts/drafts/draft_232146__ObjectivenResolve_TD229_b.md)

## 3. Implementation Roadmap

### Phase 1: Core Service Extraction
1. Extract logic from `government.py` into `IWelfareManager` and `ITaxService`.
2. Enforce the use of `WelfareResultDTO` and `TaxCollectionResultDTO`.
3. Resolve circular dependencies by removing instances of `self` passed to child components.

### Phase 2: Interface Hardening (TD-234)
1. Define `IWelfareRecipient` protocol in `modules/government/welfare/api.py`.
2. Refactor `WelfareService` to accept `List[IWelfareRecipient]` or specific DTOs instead of raw agent lists.

### Phase 3: Test-Driven Hardening (TD-229)
1. Implement golden fixtures for tax and welfare scenarios.
2. Ensure 100% logic coverage for the newly extracted services.
3. Validate agent-service orchestration via integration tests.

## 4. Verification
- `pytest tests/modules/government/`
- All tests in `tests/unit/test_tax_collection.py` must pass with zero legacy failures.
