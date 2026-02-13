# 🔍 Git Diff Review: `fix-integrity-tests-stale-attributes`

---

### 1. 🔍 Summary

본 변경 사항은 `Government` 에이전트가 `IFinancialAgent` 프로토콜의 필수 메서드(`_deposit`, `_withdraw`)를 구현하지 않아 발생했던 재정 무결성 테스트 실패를 해결합니다. 또한, `isinstance` 프로토콜 검사를 통과하지 못하는 Mock 객체로 인해 발생한 `SettlementSystem` 관련 테스트 오류를 수정하고, 테스트의 단일 진실 공급원(SSoT) 원칙을 강화했습니다.

### 2. 🚨 Critical Issues

- **None.** 이 변경 사항은 오히려 기존에 존재하던 잠재적 자금 유실(leaked-write) 버그를 해결합니다. `SettlementSystem`이 송금을 기록했음에도 불구하고, `Government` 에이전트의 잔고는 변경되지 않던 심각한 정합성 문제를 수정했습니다.

### 3. ⚠️ Logic & Spec Gaps

- **None.** 변경 사항은 식별된 문제의 근본 원인을 정확히 해결합니다.
  - **`simulation/agents/government.py`**: `IFinancialAgent` 프로토콜의 명세를 완전히 준수하도록 `_deposit`, `_withdraw` 등의 메서드를 구현하여, 에이전트가 재정 시스템에 올바르게 참여할 수 있도록 수정했습니다.
  - **`tests/integration/test_fiscal_integrity.py`**: 테스트 단언(assertion)이 에이전트의 내부 상태(`gov.assets`)가 아닌, 시스템의 관점(`settlement_system.get_balance(gov.id)`)을 따르도록 변경하여 테스트의 신뢰도를 높였습니다. 이는 SSoT 원칙에 부합하는 올바른 수정입니다.

### 4. 💡 Suggestions

- **Test Registry Fixture**: `test_fiscal_integrity.py` 내에서 `settlement_system.agent_registry`를 설정하는 코드가 반복적으로 나타납니다. 이 Mock Registry 설정을 `conftest.py`의 중앙 픽스처(fixture)로 추출하여 테스트 코드의 중복을 제거하고 가독성을 높이는 것을 고려하십시오.

### 5. 🧠 Implementation Insight Evaluation

- **Original Insight**:
  > # Insight Report: Fix Integrity Tests (Stale Attributes)
  >
  > ## Executive Summary
  > This mission addressed failing integrity tests (`test_fiscal_integrity.py`) that were asserting against stale `gov.assets` attributes. The investigation revealed that the root cause was not just the test assertion method, but a defect in the `Government` agent implementation where it inherited the `IFinancialAgent` Protocol but failed to implement the required `_deposit` and `_withdraw` methods. This caused `SettlementSystem` transfers to execute strictly as no-ops (due to Protocol default behavior or silent failure patterns), leaving the agent's wallet unchanged.
  >
  > Additionally, `test_settlement_system_atomic.py` was found to be broken due to mock objects not satisfying `IFinancialAgent` protocol checks at runtime, causing cash balances to be ignored during settlement creation.
  >
  > ## Key Findings
  >
  > ### 1. Protocol Inheritance vs. Implementation
  > The `Government` class inherited `IFinancialAgent` in its definition... However, it did not implement `_deposit` or `_withdraw`. Since `IFinancialAgent` is a `Protocol` and not an `ABC`... When `SettlementSystem` called `gov._deposit()`, it executed the protocol's empty body (no-op)...
  >
  > ### 2. Single Source of Truth (SSoT) in Tests
  > The tests were asserting `gov.assets`... the instruction was to use `settlement_system.get_balance(gov.id)`. For `settlement_system.get_balance()` to work... `settlement_system.agent_registry` must be mocked...
  >
  > ### 3. Mocking Protocols
  > In `test_settlement_system_atomic.py`, the `deceased` agent was being mocked... `SettlementSystem` uses `isinstance(agent, IFinancialAgent)`... Standard mocks do not satisfy this check unless `spec` is provided...
  >
  > ## Technical Debt & Recommendations
  >
  > 1.  **Protocol Enforcement**: Consider using `ABC` or a custom metaclass...
  > 2.  **Test Fixtures**: The `golden_households` fixture seems to return objects that are not fully compliant...
  > 3.  **Registry in Tests**: `SettlementSystem` relies heavily on `agent_registry`. Test fixtures... should probably auto-configure a mock registry...

- **Reviewer Evaluation**:
  - **Exceptional.** 이 인사이트 보고서는 문제의 현상, 근본 원인, 해결책, 그리고 이로부터 파생된 교훈을 매우 명확하고 깊이 있게 기술했습니다.
  - 특히 Python의 `Protocol`이 컴파일 타임이나 인스턴스화 시점이 아닌 런타임에 구조적으로 검사된다는 특성과, 이로 인해 메서드 미구현이 어떻게 '조용한 실패(silent failure)'로 이어졌는지 정확히 분석한 점이 인상적입니다.
  - 테스트에서의 Mock 객체 `spec` 사용법과 `agent_registry`의 중요성을 지적한 것은 시스템의 테스트 전략에 대한 높은 이해도를 보여줍니다.
  - 제안된 기술 부채(Protocol 강제, Fixture 감사 등)는 매우 구체적이고 실용적이어서 프로젝트의 장기적인 안정성 향상에 크게 기여할 것입니다.

### 6. 📚 Manual Update Proposal

- **Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`
- **Update Content**: 다음 항목을 기술 부채 원장에 추가할 것을 제안합니다.

```markdown
---
- **ID**: TD-180
- **Type**: Architectural Weakness
- **Severity**: Medium
- **Description**: The project relies on `typing.Protocol` for agent interfaces like `IFinancialAgent`. However, `Protocol` does not enforce method implementation at class instantiation time, only at runtime via `isinstance` checks. This led to a bug where `Government` was a valid `IFinancialAgent` but its financial methods were no-ops, causing silent data integrity failures.
- **Recommendation**:
  1. For critical interfaces, consider replacing `Protocol` with `abc.ABC` and `@abstractmethod` to enforce implementation and fail fast during instantiation.
  2. Alternatively, create a validation step during system startup that programmatically checks if key agent types have implemented all methods of their advertised protocols.
- **Source Mission**: `fix-integrity-tests-stale-attributes`
---
- **ID**: TD-181
- **Type**: Test Infrastructure
- **Severity**: Low
- **Description**: Core test fixtures like `golden_households` may not be fully compliant with all required `Protocol` interfaces (e.g., `IFinancialAgent`, `IHeirProvider`). This forces individual tests to create complex, properly specified mocks, leading to code duplication and brittleness.
- **Recommendation**:
  1. Audit major fixtures (`golden_households`, etc.) and ensure they return objects that satisfy all common protocols required by the systems under test.
  2. Create a library of pre-configured, protocol-compliant mock agent factories for easier use in tests.
- **Source Mission**: `fix-integrity-tests-stale-attributes`
---
```

### 7. ✅ Verdict

**APPROVE**

이 PR은 단순한 버그 수정을 넘어, 문제의 근본 원인을 정확히 진단하고, 테스트 방법론을 개선했으며, 그 과정에서 발견한 시스템의 구조적 약점을 훌륭한 인사이트 보고서로 문서화했습니다. 모든 요구사항을 완벽하게 충족하는 모범적인 변경 사항입니다.