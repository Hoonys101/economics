# 🐙 Gemini CLI System Prompt: Git Reviewer

## 🔍 Summary
This PR refactors the `Household` agent by extracting belief updates and panic selling logic into two new stateless engines: `BeliefEngine` and `CrisisEngine`. It introduces strict DTOs (`BeliefInputDTO`, `PanicSellingInputDTO`) to replace legacy dictionary passing and includes unit tests for the new engines. The logic preserves existing zero-sum integrity and handles legacy method delegation.

## 🚨 Critical Issues
*   None detected. Security and strict pathing look clean.

## ⚠️ Logic & Spec Gaps
*   **Side-Effect on Input DTO**: In `BeliefEngine.update_beliefs`, `input_dto.price_history` (a `Deque`) is modified in-place (`history.append(actual_price)`).
    *   *Context*: While this is performant (avoiding O(N) copying of history buffers), it technically deviates from a "Pure Function" stateless engine which typically returns all new state.
    *   *Impact*: Negligible for now, but callers must be aware that the `InputDTO` is not immutable regarding this field. The code comments acknowledge this ("Side-effect on Input DTO's referenced object").

## 💡 Suggestions
*   **Rename Insight File**: The file `communications/insights/manual.md` is too generic. Consider renaming it to `communications/insights/household_decomposition_refactor.md` for better searchability in the future.
*   **Explicit Return**: Even though `price_history` is updated by reference, considering adding it to `BeliefResultDTO` suggests to the reader that this state *is* part of the engine's output logic, reinforcing the data flow.

## 🧠 Implementation Insight Evaluation
*   **Original Insight**:
    > "DTO Purity: All data exchange between the agent and the new engines is strictly typed via DTOs... eliminating raw dictionary coupling for these flows."
*   **Reviewer Evaluation**:
    *   **Valid**. The move to DTOs significantly improves type safety over the previous `market_data` dictionary scraping within the agent methods.
    *   **Nuance Added**: The insight claims "Stateless engines", but `BeliefEngine` relies on the mutability of the input `deque`. This is a pragmatic compromise for performance but is a "Leaky Abstraction" in strict architectural terms.

## 📚 Manual Update Proposal (Draft)
*   **Target File**: `design/2_operations/architecture_standards.md` (or equivalent architecture documentation)
*   **Draft Content**:

```markdown
### Agent Architecture Updates (2026-02-14)
*   **Household Agent Refactoring**:
    *   **Decomposition**: `Household` now delegates price belief updates and crisis management to `BeliefEngine` and `CrisisEngine`.
    *   **Protocol**: Both engines adhere to `IBeliefEngine` and `ICrisisEngine` protocols.
    *   **Data Flow**: Interaction is strictly typed via `BeliefInputDTO`/`ResultDTO` and `PanicSellingInputDTO`/`ResultDTO`.
    *   **Note**: `BeliefEngine` modifies price history deques in-place for performance (O(1) append vs O(N) copy).
```

## ✅ Verdict
**APPROVE**

The PR successfully decomposes the agent logic with appropriate tests, type safety, and no detected security issues or zero-sum violations. The slight architectural impurity (in-place modification) is documented and acceptable for performance.