# MISSION SPEC: wave5-config-purity

## 🎯 Objective
Resolve Config-level Technical Debts to un-hardcode numbers and ensure all configuration bindings happen at runtime rather than import time.

## 🛠️ Target Tech Debts
1. **TD-CONF-GHOST-BIND (Medium)**: Modules bind config values at import time (`from config import X`).
    - **Symptom**: Runtime hot-swaps (e.g., God Mode tweaks) are ignored because variables are already cached by Python's module load.
    - **Goal**: Implement a `ConfigProxy` pattern or refactor imports so values are read at access time.
2. **TD-CONF-MAGIC-NUMBERS (Low)**: Hardcoded constants in `FinanceEngine` (Z-Score, Divisors).
    - **Symptom**: Logic like `if score < 1.5:` instead of `if score < config.FINANCE_Z_SCORE_THRESHOLD:`.
    - **Goal**: Move all magic numbers in financial logic to the central `config` or default settings module.

## 📜 Instructions for Gemini
1. **Analyze**: Search for `from config import` patterns that lead to module-level constants. Review `FinanceEngine` and related modules for hardcoded numeric literals.
2. **Plan**: Propose a `ConfigProxy` mechanism (or a function-based getter `get_config()`) to replace static imports. Document where magic numbers should be relocated.
3. **Spec Output**: Generate a Jules implementation spec detailing the necessary refactors and providing test verification strategies.
