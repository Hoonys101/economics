# 🔍 PR Review: Fix `NotImplementedError` for `deposit` and enforce internal access

## 1. 🔍 Summary
본 변경은 `deposit` 및 `withdraw` 메서드를 내부용(`_`)으로 전환하여, 외부에서 직접 자산을 생성/파괴하는 것을 방지하고 정산 시스템을 통하도록 강제합니다. 또한, 테스트 코드 전반에 걸쳐 `MagicMock` 사용을 줄이고 실제 객체를 생성하여 테스트의 신뢰성과 정확성을 대폭 향상시켰습니다.

## 2. 🚨 Critical Issues
- 발견되지 않음.

## 3. ⚠️ Logic & Spec Gaps
- **[CRITICAL] 프로세스 위반**: `communications/insights/[Mission_Key].md` 파일이 PR에 포함되지 않았습니다. 모든 구현 변경, 특히 아키텍처에 영향을 미치는 변경은 발견된 문제와 해결 과정에 대한 인사이트를 문서화해야 합니다. 이는 프로젝트의 지식 축적 및 기술 부채 관리를 위한 **필수 요구사항**입니다.
- **테스트 증거 누락**: PR에 로컬 `pytest` 실행 결과가 포함되어 있지 않습니다. 모든 로직 변경은 테스트 통과 증거를 함께 제출해야 합니다.

## 4. 💡 Suggestions
- **테스트 리팩토링 확장**: `tests/system/test_engine.py`에서 `MagicMock`을 실제 `Household` 객체로 대체한 것은 매우 훌륭한 리팩토링입니다. 이 `_create_household` 도우미 함수와 같은 패턴을 프로젝트의 다른 테스트에도 점진적으로 적용하여, 깨지기 쉬운 Mock 의존성을 제거하고 통합 테스트의 품질을 높이는 것을 적극 권장합니다.

## 5. 🧠 Implementation Insight Evaluation
- **Original Insight**:
  > [PR Diff에 인사이트 보고서 파일(`communications/insights/*.md`)이 누락되어 인용할 수 없음.]

- **Reviewer Evaluation**:
  PR의 변경 사항으로 미루어 볼 때, 개발자는 테스트 코드나 시스템 초기화 로직(Bootstrapper)에서 `deposit` 메서드를 직접 호출하여 "마법처럼 돈을 생성하는(Magic Money Creation)" 문제를 발견한 것으로 보입니다. 이를 해결하기 위해 `deposit`/`withdraw`를 내부 메서드로 전환하고, 자금 주입이 `SettlementSystem`과 같은 공식적인 경로를 통해서만 이루어지도록 강제한 것은 시스템의 **재정적 무결성(Financial Integrity)**과 **Zero-Sum 원칙**을 강화하는 핵심적인 아키텍처 개선입니다.
  
  이는 매우 중요한 통찰이나, 이것이 공식적으로 문서화되지 않은 점은 매우 아쉽습니다.

## 6. 📚 Manual Update Proposal
- 누락된 인사이트 보고서 작성을 요청하며, 해당 보고서가 작성되면 아래 내용을 `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`에 추가할 것을 제안합니다.

- **Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`
- **Update Content**:
  ```markdown
  ---
  - date: '2026-02-12'
    type: 'Architectural Refinement'
    severity: 'Medium'
    author: 'Jules'
    status: 'Resolved'
    description: |
      **현상**: 테스트 코드 및 `Bootstrapper` 등 시스템의 여러 부분에서 `agent.deposit()`를 직접 호출하여 중앙 은행이나 거래 시스템을 거치지 않고 자산을 생성하는 "Magic Money" 문제가 발견되었습니다. 이는 Zero-Sum 원칙을 위반할 수 있는 잠재적 경로입니다.
      **원인**: `deposit`, `withdraw` 메서드가 public으로 노출되어 있어, 자산 변경의 출처와 흐름을 강제할 수 없었습니다.
      **해결**: `deposit`/`withdraw`를 내부 API(`_deposit`/`_withdraw`)로 변경하고, 모든 자산 이전은 `SettlementSystem.transfer`와 같은 공식적인 금융 트랜잭션 시스템을 통해서만 발생하도록 아키텍처를 수정했습니다. 테스트 코드도 이에 맞춰 리팩토링되었습니다.
      **교훈**: Agent의 상태를 직접 변경하는 API는 최소한으로 노출해야 한다. 모든 상태 변경, 특히 금융과 관련된 변경은 반드시 검증된 중앙 시스템(Engine, Orchestrator)을 통해 이루어져야 추적성과 무결성을 보장할 수 있다.
  ```

## 7. ✅ Verdict
- **REQUEST CHANGES (Hard-Fail)**
  - **사유**: 필수적인 **인사이트 보고서(`communications/insights/*.md`)가 누락**되었습니다. 이는 프로젝트의 핵심 개발 프로세스를 위반하는 사항으로, 반드시 수정되어야 합니다. 또한, 테스트 통과에 대한 증거가 제출되지 않았습니다. 인사이트 보고서 작성 및 테스트 통과 증거를 첨부하여 PR을 다시 제출해 주십시오.
