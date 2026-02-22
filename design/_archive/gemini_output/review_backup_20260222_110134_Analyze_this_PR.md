# 🐙 Gemini CLI System Prompt: Git Reviewer

## 📝 Code Review Report

### 1. 🔍 Summary
This PR implements a specialized `LaborMarket` system to replace the generic order book for labor. It introduces "Major-Based Matching" (e.g., TECH, FOOD) to align worker specialization with firm needs. Key changes include DTO extensions for `major`, a new `HIRE` transaction type (state-only transition), and logic for applying productivity modifiers based on mismatch severity.

### 2. 🚨 Critical Issues
*   None found.

### 3. ⚠️ Logic & Spec Gaps
*   **None**. The logic appears consistent. The `HIRE` transaction correctly bypasses immediate financial settlement (cost=0) while still carrying the agreed wage (`total_pennies`) for the HR contract, ensuring `hr_engine.hire` records the correct salary.

### 4. 💡 Suggestions
*   **Scalability**: The `MAJORS` list is currently hardcoded in `modules/labor/constants.py`. As the simulation grows, consider moving this to `economy_params.yaml` or a similar config file to allow for dynamic sector definitions without code changes.

### 5. 🧠 Implementation Insight Evaluation

*   **Original Insight**:
    > We have transitioned from a generic `OrderBookMarket` for labor to a specialized `LaborMarket` system implementing `ILaborMarket`. This enables bipartite matching based on Major Compatibility, Education Level, and Wage. [...] A new transaction type `HIRE` was introduced.

*   **Reviewer Evaluation**:
    *   **Accurate Reflection**: The insight correctly identifies the architectural shift from a generic matching engine to a domain-specific one.
    *   **Technical Depth**: It accurately describes the Adapter pattern used to maintain `IMarket` compatibility (`place_order` -> `JobOfferDTO`), which is a crucial detail for future maintainers.
    *   **Risk Assessment**: The regression risks regarding legacy tests are well-identified and were proactively addressed in the PR.

### 6. 📚 Manual Update Proposal (Draft)

*   **Target File**: `design/2_operations/ledgers/ECONOMIC_INSIGHTS.md`
*   **Draft Content**:
    ```markdown
    ### [2026-02-22] Labor Market Specialization (Major-Matching)
    - **Context**: Replaced generic `OrderBookMarket` for labor with specialized `LaborMarket`.
    - **Mechanism**: Bipartite matching prioritizing **Major Compatibility** (e.g., TECH firm + TECH major) -> **Education** -> **Wage**.
    - **Economic Impact**: Introduced `HIRE` transaction type which is a non-monetary state transition. Mismatched hires (e.g., FOOD major in TECH firm) now incur a `productivity_modifier` penalty (0.8x - 0.9x), simulating training costs/inefficiency.
    - **Technical Note**: `LaborMarket` acts as an adapter, converting legacy `CanonicalOrderDTO`s into domain-specific `JobOffer`/`JobSeeker` objects.
    ```

### 7. ✅ Verdict
**APPROVE**

The implementation is robust, strictly typed, and includes comprehensive tests. The separation of `HIRE` (contract) from `WAGE` (payment) is a significant architectural improvement.