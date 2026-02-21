# MISSION SPEC: wave6-ai-debt-aware

## 🎯 Objective
Resolve constraints blindness in AI models, focusing heavily on enabling the AI to comprehend and react to its own debt status.

## 🛠️ Target Tech Debts
1. **TD-AI-DEBT-AWARE (Medium)**: AI Constraint Blindness (Log Spam)
    - **Symptom**: `FirmSystem2Planner` continues to propose aggressive R&D or expansion investments even when the firm is at or past its debt ceiling, causing "Intent Spamming" in the logs as orders are rejected by the Finance Engine.
    - **Goal**: Update `FirmSystem2Planner._calculate_npv` (or related planning heuristics) to explicitly model debt interest, repayment flows, and current debt ratios (DTI) before proposing intents.

## 📜 Instructions for Gemini
1. **Analyze**: Review `FirmSystem2Planner` and the AI input DTOs. Identify where debt information is missing from the state evaluation.
2. **Plan**: Formulate the changes needed to pass the `current_debt_ratio` or `debt_service_burden` into the AI's heuristic functions and adjust the NPV calculations to penalize strategies when heavily indebted.
3. **Spec Output**: Generate an actionable Jules implementation spec to modify the AI planning logic and inject the missing DTO fields.
