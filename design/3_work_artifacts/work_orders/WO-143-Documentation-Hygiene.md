# Work Order: WO-143 - Documentation Hygiene & Template Normalization

## 🎯 Objective
Resolve the technical debt of "Hardcoded Placeholders" (TD-143) across the project documentation. This involves identifying and replacing generic `WO-XXX` tags with specific Work Order identifiers or persistent documentation links.

---

## 🛠️ Tasks

### 1. Identify Placeholders
- Search for all occurrences of `WO-XXX`, `TD-XXX`, or similar placeholders in the following directories:
    - `design/1_governance/`
    - `design/2_operations/`
    - `design/3_work_artifacts/`
    - `design/manuals/`

### 2. Map to Reality
- Cross-reference the placeholders with:
    - `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`
    - `design/3_work_artifacts/work_orders/`
    - Git commit messages (using `git log`).

### 3. Replace and Update
- Replace generic tags with their correct IDs (e.g., `WO-136`).
- If a specific ID doesn't exist yet but the work is completed, create a logical placeholder that follows the project's sequence.

### 4. Verify Purity Gate Labels
- Ensure that the Linter/Purity Gate documentation correctly reflects the rule IDs as defined in `pyproject.toml` (part of WO-138 legacy cleanup).

---

## 🏗️ Technical Constraints
- Do not alter the content of the `_archive/` directory.
- Maintain the Markdown formatting and table structures.

---

## 🏁 Success Sign-off
- [ ] No occurrences of `WO-XXX` remain in active governance or operations documents.
- [ ] All cross-links between the Tech Debt Ledger and Work Orders are verified and functional.
- [ ] Session Ledger reflects the resolution of TD-143.
