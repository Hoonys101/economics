# Code Review Report

## 🔍 Summary
This PR implements the atomic `FirmFactory` refactor (Mission `wo-firm-factory-core`), eliminating the `SimulationState` God Object dependency in favor of scoped protocols (`IBirthContext`, `IFinanceTickContext`). While the direction properly enforces Atomicity and Zero-Sum integrity, there is a critical domain logic error in the legacy fallback logic, a major spec gap in Firm Mitosis, and non-compliance with the required Insight reporting template.

## 🚨 Critical Issues
*   **Domain Classification Bug (Logic & Integrity)**: In `simulation/factories/firm_factory.py` (approx. line 74), the legacy fallback block appends the newly created `firm` to `birth_context.households` instead of `birth_context.firms`. This is a critical logic bug that breaches domain boundaries and will cause catastrophic type-mismatch crashes downstream when systems iterate over the `households` list.
    ```python
    if hasattr(birth_context, "agent_registry") and birth_context.agent_registry:
        birth_context.agent_registry.register(firm)
    else:
        # Fallback for mocked/legacy contexts without agent_registry
        birth_context.households.append(firm) # 🚨 CRITICAL: Should be birth_context.firms.append(firm)
    ```
*   **Hardcoded Magic String (Security & Hardcoding)**: `simulation/finance/api.py` introduces a hardcoded literal `currency: str = "USD"` in the `create_and_transfer` signature. This violates the configuration purity mandate and must use `currency: CurrencyCode = DEFAULT_CURRENCY` (imported from `modules.system.api`).

## ⚠️ Logic & Spec Gaps
*   **Ghost Firm Risk in Mitosis (Spec Gap)**: The `create_firm` method correctly executes global registration (`agent_registry.register(firm)`). However, `create_firm_mitosis` entirely lacks this step. When a firm splits, the newly spawned entity creates a bank account but is never added to the global `agent_registry`, resulting in the exact "Ghost Firm" vulnerability the mission aimed to fix.
*   **Insight Template Non-Compliance**: The insight document `communications/insights/wo-firm-factory-core.md` completely ignores the mandatory decentralized protocol format. It uses English headers (`Architectural Insights`, `Regression Analysis`) instead of the strictly required `현상/원인/해결/교훈` (Phenomenon/Cause/Solution/Lesson) structure.
*   **Bare Exceptions (Vibe Check)**: `simulation/ai/vectorized_planner.py` uses excessively broad bare `except:` blocks (e.g., `except: wages.append(0.0)`). While this carries over from legacy logic, they should be explicitly constrained to `except (AttributeError, TypeError, ValueError):` to prevent masking critical application-level crashes (e.g., `MemoryError` or `KeyboardInterrupt`).

## 💡 Suggestions
*   **Fix Fallback List**: Correct the fallback mechanism in `FirmFactory.create_firm` to `birth_context.firms.append(firm)`.
*   **Ensure Mitosis Registration**: Supply `birth_context` (or `agent_registry`) to `create_firm_mitosis` and ensure `agent_registry.register(new_firm)` is explicitly invoked.
*   **Rewrite Insight Report**: Reformat `wo-firm-factory-core.md` to conform to the standardized `현상/원인/해결/교훈` markdown structure.
*   **Clean Up Hardcoding**: Ensure `DEFAULT_CURRENCY` is properly imported and applied as the default kwarg in `simulation/finance/api.py`.

## 🧠 Implementation Insight Evaluation
*   **Original Insight**: 
    > "The prior FirmFactory and Bootstrapper implementations suffered from structural vulnerabilities regarding agent lifecycle management, specifically creating potential 'Ghost Firms'... Atomic Registration: Registration now guarantees a deterministic sequence. An agent is added to the global agent_registry and an account is created in the settlement_system. If account registration or liquidity injection fails, an atomic rollback immediately marks firm.is_active = False..."
*   **Reviewer Evaluation**: The technical evaluation of the `SimulationState` decoupling and the implementation of the explicit "Soft-Kill" atomic failure (`is_active = False`) is highly accurate. Identifying the root cause of ghost firm leakage is sound. However, the evaluation is **REJECTED** because it fundamentally fails the policy check: the document does not use the mandated `현상/원인/해결/교훈` template. Furthermore, the claim that "registration guarantees a deterministic sequence" is factually undermined by the omission of the registry addition in the `create_firm_mitosis` execution path.

## 📚 Manual Update Proposal (Draft)
*   **Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`
*   **Draft Content**:
```markdown
### [TD-LIFECYCLE-GHOST-FIRM] Atomic Agent Lifecycle Initialization
* **현상 (Phenomenon)**: 에이전트(Firm) 생성 중 시스템(Settlement, Liquidity) 초기화에 실패할 경우, 레지스트리에는 등록되어 있으나 금융 기능이 동작하지 않는 'Ghost Firm'이 잔존하는 문제 발생.
* **원인 (Cause)**: `FirmFactory`가 `SimulationState`라는 God Object에 강하게 결합되어 있었으며, 객체 생성과 환경 등록(Bank Account 개설, Initial Liquidity 주입)이 Transaction(Atomic) 단위로 묶여 있지 않았음.
* **해결 (Solution)**: 생성 시 주입되는 컨텍스트를 `IBirthContext`와 `IFinanceTickContext`로 엄격히 분리하여 의존성을 통제함. 초기화 과정 실패 시 즉시 `RuntimeError`를 발생시키고 `firm.is_active = False`로 처리(Soft-Kill)하여 롤백 보장.
* **교훈 (Lesson)**: 모든 Agent의 탄생(Birth)과 파생(Mitosis)은 부작용(Side-effect)을 동반하므로, 반드시 Atomic한 절차로 통제되어야 하며 God Object를 배제하고 명확한 Protocol Interface를 통해 Context를 주입받아야 함.
```

## ✅ Verdict
**REQUEST CHANGES (Hard-Fail)**