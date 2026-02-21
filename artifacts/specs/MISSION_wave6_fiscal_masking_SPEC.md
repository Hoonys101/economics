# MISSION SPEC: wave6-fiscal-masking

## 🎯 Objective
Enhance the economic realism by resolving "Fiscal Masking," where simplistic stimuli hide underlying structural economic imbalances.

## 🛠️ Target Tech Debts
1. **TD-ECON-WAR-STIMULUS (Medium)**: Fiscal Imbalance & Stimulus Dependency
    - **Symptom**: GDP and Welfare metrics remain artificially high due to high-frequency, unconditional stimulus triggers, which masks logic errors in Firm pricing and wage models (e.g., firms paying too little, offset entirely by govt handouts).
    - **Goal**: Replace or augment the simplistic stimulus trigger with progressive taxation algorithms and productivity-indexed wage scaling within the economic policy modules.

## 📜 Instructions for Gemini
1. **Analyze**: Inspect the `Government` or `PolicyEngine` logic responsible for triggering stimulus packages. Review the firm wage calculation models.
2. **Plan**: Design an implementation that introduces progressive taxation (if missing) and ties wage demands/adjustments more closely to productivity or inflation metrics, reducing the reliance on raw "helicopter money."
3. **Spec Output**: Produce a concise Jules implementation spec that outlines the mathematical modifications to the policy engines to resolve this debt.
