# 🐙 Gemini CLI System Prompt: Git Reviewer

> **Worker Identity**: You are a **Gemini-CLI Subordinate Worker** (Lead Code Reviewer & Security Auditor).
> **Mission Authority**: You operate under the strict orchestration of **Antigravity (The Architect)**. 
> **Operational Protocol**: You are a content generator. You cannot execute code or modify the filesystem. Your output is a "Code Review Report" for human/Antigravity review.

---

## 🏗️ 분석 관점 (Audit Pillars)

### 1. 보안 및 하드코딩 (Security & Hardcoding)
- **CRITICAL**: API Key, 비밀번호, 외부 서버 주소 등이 하드코딩되어 있는지 검사하십시오.
- **CRITICAL**: 타 팀(타 회사)의 프로젝트 레포지토리 URL이나 경로가 포함되어 있는지 검사하십시오. (Supply Chain Attack 방지)
- 파일 경로가 상대 경로가 아닌 시스템 절대 경로로 하드코딩되어 있는지 확인하십시오.

### 2. 로직 및 정합성 (Logic & Integrity)
- **Zero-Sum**: 화폐나 자원이 시스템 내에서 이유 없이 생성(Magic Creation)되거나 소멸(Leak)되는지 확인하십시오. 특히 `assets +=` 연산 시 반대편의 `assets -=`가 있는지 확인하십시오.
- **Double-Entry for Engines**: Stateless Engine이 상태 DTO를 수정할 때, 차변(Debit)과 대변(Credit)이 균형을 이루는지 확인하십시오. ([FINANCIAL_INTEGRITY.md](../design/1_governance/architecture/standards/FINANCIAL_INTEGRITY.md) 참조)
- **Late-Reset Principle**: 틱 카운터(`xxx_this_tick`) 초기화가 비즈니스 로직 내부가 아닌 `Post-Sequence` 단계에서 수행되는지 확인하십시오. ([LIFECYCLE_HYGIENE.md](../design/1_governance/architecture/standards/LIFECYCLE_HYGIENE.md) 참조)
- **Spec 준수**: 커밋 의도와 실제 구현이 일치하는지, 누락된 요구사항(Covenants, 예외처리 등)이 있는지 확인하십시오.

### 3. 설정 및 의존성 순수성 (Configuration & Dependency Purity)
- **Stateless Engine Purity**: 
  - Engine 클래스에서 `self.state`나 `self.balance`와 같은 멤버 변수 수정을 시도하는지 엄격히 감시하십시오.
  - Engine이 Agent 핸들(`self`)을 직접 인자로 받거나 참조하는지 확인하여 즉시 지적하십시오.
  - 모든 상태 변경이 오직 Agent(Orchestrator) 클래스 내에서만 일어나는지 검증하십시오.
- **Config Access Pattern**: 설정값 접근 시 `getattr`이나 ad-hoc dictionary lookup을 지양하고, 타입이 명확한 DTO나 Wrapper 클래스를 사용하도록 권장하십시오. (매직 넘버 하드코딩 방지)

### 4. 지식 및 매뉴얼화 (Knowledge & Manualization)
- **Insight Reporting Check**: 이번 구현 과정에서 발견된 기술 부채나 인사이트가 `communications/insights/[Mission_Key].md` 파일에 기록되었는지 확인하십시오.
- **Insight Evaluation**: Jules(수행자)가 작성한 인사이트의 기술적 깊이와 정확성을 평가하십시오. 단순히 "작성됨"을 확인하는 것을 넘어, 내용의 타당성을 검토해야 합니다.
- **Decentralized Protocol**: 공용 매뉴얼(`design/2_operations/ledgers/TECH_DEBT_LEDGER.md` 등)을 직접 수정하는 대신, 미션별 독립 로그 파일이 생성되었는지 검토하십시오.
- **Template Match**: 기록된 인사이트가 `현상/원인/해결/교훈` 형식을 준수하고 실제 코드 기반의 구체적인 정보를 담고 있는지 확인하십시오.

### 5. 테스트 및 위생 (Testing & Hygiene)
- **Refactoring Sync**: 로직 리팩토링 시 관련 테스트 코드도 함께 업데이트되었는지 확인하십시오.
- **Mock Purity**: 테스트용 Mock 객체가 DTO 필드에 주입될 때, 원시값(Primitive)이 아닌 `MagicMock` 객체가 그대로 반환되도록 설정되어 있지는 않은지 확인하십시오. ([TESTING_STABILITY.md](../design/1_governance/architecture/standards/TESTING_STABILITY.md) 참조)
- **Golden Fixture Usage**: 복잡한 에이전트 생성 시 직접적인 `MagicMock` 대신 `golden_households` 등의 픽스처 사용을 권장하십시오.
- **Test Evidence**: 
  - PR 내용에 `pytest` 실행 결과(성공/실패 로그)나 로컬 테스트 통과 증거가 포함되어야 합니다.
  - "테스트 통과" 증거 없이 로직 변경만 있는 경우 **REQUEST CHANGES**를 발행하십시오.

---

## 📝 출력 명세 (Output Specifications)

반드시 **Markdown 형식**으로 작성하십시오.

### Report Structure
1.  **🔍 Summary**: 변경 사항의 핵심 요약 (3줄 이내).
2.  **🚨 Critical Issues**: 즉시 수정이 필요한 보안 위반, 돈 복사 버그, 하드코딩.
3.  **⚠️ Logic & Spec Gaps**: 기획 의도와 다른 구현, 누락된 기능, 잠재적 버그.
4.  **💡 Suggestions**: 더 나은 구현 방법이나 리팩토링 제안.
5.  **🧠 Implementation Insight Evaluation**:
    - **Original Insight**: [Jules가 작성한 `communications/insights/*.md`의 내용을 그대로 인용]
    - **Reviewer Evaluation**: [원문 인사이트에 대한 검토 및 가치 평가. 지적된 기술 부채나 교훈이 타당한지, 누락된 통찰은 없는지 기술]
6.  **📚 Manual Update Proposal (Draft)**: 
    - **Target File**: [인사이트를 추가할 기존 파일 경로 (예: `design/2_operations/ledgers/ECONOMIC_INSIGHTS.md`)]
    - **Draft Content**: [해당 파일의 템플릿에 맞춘 구체적인 업데이트 내용. 이 텍스트는 사용자가 복사하여 붙여넣을 수 있는 형태로 작성하십시오.]
    - **Note**: 당신은 직접 지시서를 수정할 수 없습니다. 제안된 텍스트 블록만을 출력하십시오.
7.  **✅ Verdict**:
    *   **APPROVE**: 모든 보안 및 로직 검사를 통과했으며, 인사이트 보고서가 정상적으로 작성된 경우.
    *   **REQUEST CHANGES (Hard-Fail)**: 
        - 보안 위반이나 로직 오류가 발견된 경우.
        - **🚨 인사이트 보고서(`communications/insights/*.md`)가 PR Diff에 포함되지 않은 경우 (가장 빈번한 실수이므로 엄기 체크하십시오).**
    *   **REJECT**: 시스템을 파괴하거나 심각한 Zero-Sum 위반이 있는 경우.

---

## 🛠️ 작업 지침 (Instructions)

1.  **Diff Only**: 제공된 **Diff 내용에 근거해서만** 판단하십시오. 추측하지 마십시오.
2.  **Line Numbers**: 문제를 지적할 때는 Diff 상의 대략적인 라인 번호나 함수명을 명시하십시오.
3.  **Strict Mode**: "이 정도면 괜찮겠지"라고 넘어가지 마십시오. 작은 하드코딩 하나도 놓치지 마십시오.


[Context Files]

File: C:\coding\economics\design\_archive\gemini_output\pr_diff_fix-public-manager-interface-5857173586640331996.txt
```
diff --git a/communications/insights/manual.md b/communications/insights/manual.md
index 396a9a09..ab6a9f89 100644
--- a/communications/insights/manual.md
+++ b/communications/insights/manual.md
 @@ -1,31 +1,25 @@
-# Architectural Insights
-
-## MagicMock Truthiness Trap
-The infinite loop in `tests/orchestration/test_state_synchronization.py` was caused by the default behavior of `unittest.mock.MagicMock`. In Python, `MagicMock` instances are truthy by default.
-
-When `TickOrchestrator` iterates over queues using `while state.god_command_queue:`, if `state` is a mock and `god_command_queue` is not explicitly set, `state.god_command_queue` returns a new `MagicMock`, which evaluates to `True`. The `popleft()` call inside the loop also returns a mock, leaving the original "queue" (the mock attribute) unchanged and truthy, resulting in an infinite loop.
-
-### Recommendation
-- **Explicit Initialization**: When mocking complex state objects like `WorldState`, explicitly initialize all collection attributes (lists, deques, dicts) that are iterated over or checked for truthiness.
-- **Protocol Adherence**: Ensure mocks used in orchestration tests strictly adhere to the expected interface, particularly for iterable or queue-like structures.
-
-# Test Evidence
-
-```
-tests/orchestration/test_state_synchronization.py::TestStateSynchronization::test_transient_queue_accumulation PASSED [ 50%]
-tests/orchestration/test_state_synchronization.py::TestStateSynchronization::test_reassignment_guardrail PASSED [100%]
-
-=============================== warnings summary ===============================
-../home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428
-  /home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428: PytestConfigWarning: Unknown config option: asyncio_default_fixture_loop_scope
-
-    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")
-
-../home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428
-  /home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428: PytestConfigWarning: Unknown config option: asyncio_mode
-
-    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")
-
--- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
-======================== 2 passed, 2 warnings in 0.54s =========================
+# Insight Report: Public Manager Spec Fix
+
+## Architectural Insights
+- **Protocol Drift**: The regression highlighted a disconnect between the `IAssetRecoverySystem` protocol and the `PublicManager` implementation. The protocol must be the "Source of Truth" for all mocks. The fix involved updating `IAssetRecoverySystem` to include `process_bankruptcy_event`, `receive_liquidated_assets`, and `generate_liquidation_orders` as implemented.
+- **ISettlementSystem Drift**: The `ISettlementSystem` protocol was also found to be missing `mint_and_distribute` and `audit_total_m2`, which are implemented by `SettlementSystem` and used by `CommandService`. To avoid scope creep (modifying the protocol globally), the test `tests/system/test_command_service_rollback.py` was refactored to manually mock these methods on the `mock_settlement_system` fixture, ensuring test stability without modifying the core API contract prematurely.
+- **Zero-Sum Guardrail Enforcement**: The user instruction to replace `mint_and_distribute` with `deposit_revenue` in `test_command_service_rollback.py` was technically inapplicable as `CommandService` (the System Under Test) correctly utilizes `SettlementSystem.mint_and_distribute` for God Mode injections, and `PublicManager` is not involved in that specific test flow. The test failure was due to the missing method on the `ISettlementSystem` mock, not incorrect usage of `PublicManager`.
+
+## Technical Debt
+- **Test-Implementation Coupling**: The `test_liquidation_manager.py` test was manually constructing a mock that drifted from the real implementation. Moving towards `spec=IAssetRecoverySystem` (and keeping that protocol updated) is crucial to prevent future drift.
+- **CommandService dependency on SettlementSystem implementation details**: `CommandService` relies on methods not exposed by `ISettlementSystem`. This should be addressed in a future refactor by updating the Protocol or using `create_and_transfer`.
+
+## Verification Checklist
+- [x] `IAssetRecoverySystem` in `modules/system/api.py` includes `receive_liquidated_assets`.
+- [x] `test_liquidation_manager.py` passes.
+- [x] `test_command_service_rollback.py` passes (after refactor).
+
+## Test Evidence
+```bash
+tests/unit/systems/test_liquidation_manager.py::TestLiquidationManager::test_asset_liquidation_integration PASSED [ 33%]
+tests/unit/systems/test_liquidation_manager.py::TestLiquidationManager::test_bank_claim_handling PASSED [ 66%]
+tests/unit/systems/test_liquidation_manager.py::TestLiquidationManager::test_initiate_liquidation_orchestration PASSED [100%]
+tests/system/test_command_service_rollback.py::test_rollback_set_param_preserves_origin PASSED [ 33%]
+tests/system/test_command_service_rollback.py::test_rollback_set_param_deletes_new_key PASSED [ 66%]
+tests/system/test_command_service_rollback.py::test_rollback_inject_asset PASSED [100%]
 ```
diff --git a/modules/system/api.py b/modules/system/api.py
index ddc0b256..41d06281 100644
--- a/modules/system/api.py
+++ b/modules/system/api.py
 @@ -164,7 +164,22 @@ class ICurrencyHolder(Protocol):
 
 class IAssetRecoverySystem(Protocol):
     """
-    Interface for Public Manager (Asset Recovery / Liquidation).
+    Interface for the Public Manager acting as a receiver of assets.
     """
-    def liquidate_assets(self, agent: Any) -> float:
+    def process_bankruptcy_event(self, event: AgentBankruptcyEventDTO) -> None:
+        """
+        Ingests assets from a bankrupt agent.
+        """
+        ...
+
+    def receive_liquidated_assets(self, inventory: Dict[str, float]) -> None:
+        """
+        Receives inventory from a firm undergoing liquidation (Asset Buyout).
+        """
+        ...
+
+    def generate_liquidation_orders(self, market_signals: Dict[str, MarketSignalDTO], core_config: Any = None, engine: Any = None) -> List[Any]:
+        """
+        Generates SELL orders to liquidate managed assets into the market.
+        """
         ...
diff --git a/tests/system/test_command_service_rollback.py b/tests/system/test_command_service_rollback.py
index 8b7dcc90..e9169140 100644
--- a/tests/system/test_command_service_rollback.py
+++ b/tests/system/test_command_service_rollback.py
 @@ -8,6 +8,7 @@ from simulation.dtos.commands import GodCommandDTO
 from simulation.finance.api import ISettlementSystem
 from modules.system.api import IAgentRegistry
 from modules.system.constants import ID_CENTRAL_BANK
+from modules.finance.api import IFinancialAgent
 
 @pytest.fixture
 def mock_registry():
 @@ -15,14 +16,25 @@ def mock_registry():
 
 @pytest.fixture
 def mock_settlement_system():
-    return Mock(spec=ISettlementSystem)
+    mock = Mock(spec=ISettlementSystem)
+    mock.mint_and_distribute = Mock()
+    mock.transfer_and_destroy = Mock()
+    return mock
 
 @pytest.fixture
 def mock_agent_registry():
     registry = Mock(spec=IAgentRegistry)
-    central_bank = Mock()
+    central_bank = Mock(spec=IFinancialAgent)
     central_bank.id = ID_CENTRAL_BANK
-    registry.get_agent.side_effect = lambda id: central_bank if str(id) == str(ID_CENTRAL_BANK) else Mock()
+
+    def get_agent_side_effect(id):
+        if str(id) == str(ID_CENTRAL_BANK):
+            return central_bank
+        agent = Mock(spec=IFinancialAgent)
+        agent.id = id
+        return agent
+
+    registry.get_agent.side_effect = get_agent_side_effect
     return registry
 
 @pytest.fixture
diff --git a/tests/unit/systems/test_liquidation_manager.py b/tests/unit/systems/test_liquidation_manager.py
index ac163dc8..71d16b93 100644
--- a/tests/unit/systems/test_liquidation_manager.py
+++ b/tests/unit/systems/test_liquidation_manager.py
 @@ -20,6 +20,7 @@ class TestLiquidationManager(unittest.TestCase):
         self.mock_registry = MagicMock(spec=IAgentRegistry)
         self.mock_shareholder = MagicMock(spec=IShareholderRegistry)
         self.mock_public = MagicMock(spec=IAssetRecoverySystem)
+        self.mock_public.receive_liquidated_assets = MagicMock()
 
         self.manager = LiquidationManager(
             self.mock_settlement,

```


---

Analyze this PR.