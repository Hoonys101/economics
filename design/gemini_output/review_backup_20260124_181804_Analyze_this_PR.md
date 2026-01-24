# 🔍 Git Diff Review: TD-105 Fix Government Money Drift

## 🔍 Summary

이 변경 사항은 정부의 인프라 투자 로직에서 발생하던 심각한 '자산 증식(Money Creation)' 버그를 해결합니다. 자금 이체 시 수취인에게만 자산이 지급되고 송금인인 정부의 자산이 차감되지 않던 문제를, 명시적인 출금(debit) 로직을 추가하여 Zero-Sum 트랜잭션을 보장하도록 수정했습니다. 또한, 의도적으로 버그를 재현하는 Mock 객체를 사용한 탁월한 회귀 테스트를 추가하여 수정 사항을 검증하고 향후 유사한 문제의 재발을 방지합니다.

## 🚨 Critical Issues

- 발견되지 않았습니다.
- 이 PR은 하드코딩된 경로, API 키 등의 보안 문제를 포함하고 있지 않으며, 오히려 시스템의 치명적인 회계 정합성 버그를 수정합니다.

## ⚠️ Logic & Spec Gaps

- 발견되지 않았습니다.
- `test_government_fiscal_policy.py`의 기존 테스트를 수정하여, 자산 차감 로직이 더 이상 지연 실행되지 않고 즉시 동기적으로 처리됨을 명확히 반영한 점이 훌륭합니다. 이는 변경된 동작 사양을 테스트 코드에 정확히 명시한 좋은 사례입니다.

## 💡 Suggestions

- `tests/test_government_finance.py`에 추가된 `MockSettlementSystem`은 매우 훌륭한 테스트 패턴입니다. 불안정한 외부 시스템의 동작을 의도적으로 흉내 내어, 이를 호출하는 내부 로직의 방어적 구현을 강제하고 검증합니다. 이 패턴을 다른 모듈의 회계 관련 테스트 작성 시에도 적극적으로 활용하는 것을 권장합니다.

## 🧠 Manual Update Proposal

- **Target File**: `design/manuals/ECONOMIC_INSIGHTS.md`
- **Update Content**: 이 수정 사항은 시스템의 핵심 경제 원칙에 대한 중요한 교훈을 담고 있습니다. 아래 내용을 매뉴얼에 추가하여 지식을 축적해야 합니다.

  ```markdown
  ---
  ### 원칙: 호출자 측 검증 (Caller-Side Verification)
  
  - **현상 (Phenomenon)**
    - 시스템 전체의 총 자산이 이유 없이 증가하는 "자산 표류(Asset Drift)" 또는 "돈 복사(Money Creation)" 현상이 관찰됨.
  
  - **원인 (Cause)**
    - `Government.invest_infrastructure` 함수에서 `SettlementSystem`을 통해 자금을 이체할 때, `SettlementSystem`이 수취인에게 자산(Credit)을 지급했으나 송금인의 자산(Debit)은 차감하지 않았음. 이는 `SettlementSystem` 자체의 구현 결함이거나, 트랜잭션의 원자성을 보장하지 않는 아키텍처적 특징일 수 있음.
  
  - **해결 (Solution)**
    - 자금 이체를 요청하는 호출자(Government 에이전트)가 거래의 최종 정합성을 보장할 책임을 진다. `SettlementSystem.transfer`가 성공적으로 반환된 직후, `self.withdraw()`를 명시적으로 호출하여 자신의 계좌에서 자산을 직접 차감함으로써 Zero-Sum을 강제함.
  
  - **교훈 (Lesson Learned)**
    - 시스템의 핵심 서비스(예: `SettlementSystem`)가 항상 완벽하게 동작한다고 가정해서는 안 된다. 특히 자산의 이동과 같이 정합성이 중요한 로직에서는, 서비스를 호출한 주체가 최종 결과(자신의 자산 상태)를 직접 확인하고 보정하는 방어적 프로그래밍이 필수적이다.
  ```

## ✅ Verdict

**APPROVE**
