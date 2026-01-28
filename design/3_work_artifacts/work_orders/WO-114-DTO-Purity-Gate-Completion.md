# Work Order: WO-114 - DTO Purity Gate Completion

## 1. Context
- **Technical Debt**: TD-103 (Leaky AI Abstraction)
- **Objective**: Complete the "Abstraction Wall" by fully decoupling decision engines from agent instances.
- **Status**: Chief Architect (Antigravity) has initiated the refactoring, modifying `DecisionContext`, `BaseDecisionEngine`, and the context creation logic in `Household` and `Firm`.
- **References**: `design/specs/DTO_PURITY_GATE_SPEC.md`

## 2. Tasks for Jules
1. **Engine Refactoring**:
    - Audit all classes inheriting from `BaseDecisionEngine`.
    - Ensure they only use `context.state` (DTO) and `context.config` (DTO).
    - Specifically check `RuleBasedFirmEngine`, `StandaloneRuleBasedFirmEngine`, and any others.
    - Remove or ignore the deprecated `household` and `firm` fields in `DecisionContext`.
2. **Logic Migration**:
    - If an engine calls an agent method (e.g., `context.firm.some_method()`), move that logic into a stateless helper method within the engine or a utility class.
3. **Verification**:
    - Fix all failing unit tests caused by the change in `DecisionContext` signature.
    - Add a test case that verifies the Purity Gate (assertion fails if DTOs are missing).

## 3. Reporting Requirement
- Submit a **Technical Debt Report** as per `scr_launcher.md`.
- Identify any "Hidden Dependencies" found during refactoring.
