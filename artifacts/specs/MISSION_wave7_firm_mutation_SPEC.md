# MISSION SPEC: wave7-firm-mutation

## 🎯 Objective
Finalize the architectural purity of the Firm agent by enforcing the Stateless Engine and Orchestrator (SEO) pattern completely.

## 🛠️ Target Tech Debts
1. **TD-ARCH-FIRM-MUTATION (Medium)**: Firm In-place State Mutation
    - **Symptom**: `firm.py` passes state objects like `self.sales_state` directly to engines (e.g., `BrandEngine`, `SalesEngine`), which mutate them in-place instead of returning `ResultDTOs`.
    - **Goal**: Refactor engines to be pure functions that take a State DTO and return an Action/Result DTO, which the Orchestrator then applies.
2. **TD-ARCH-FIRM-COUP (High)**: Parent Pointer Pollution
    - **Symptom**: `Department` classes in `Firm` initialized with `self.parent = firm`.
    - **Goal**: Remove `.attach(self)` and `self.parent` references. Components must remain decoupled data structures operated on by Engines.

## 📜 Instructions for Gemini
1. **Analyze**: Review `firm.py`, `SalesEngine`, `BrandEngine`, and `Firm` components. Identify all instances of in-place mutation and parent pointer usage (`self.parent`).
2. **Plan**: Define the DTO inputs/outputs required to make the engines stateless. Plan the removal of parent pointers and the shift of orchestration logic fully to the `Firm` agent's core `tick` loop.
3. **Spec Output**: Generate the Jules implementation spec needed to enforce strict SEO purity within the `Firm` module line-by-line.
