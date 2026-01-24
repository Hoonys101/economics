# 🔍 Git Diff 리뷰 보고서: TD112 (Inheritance Integer Fix)

---

### 1. 🔍 Summary
부동소수점(float) 기반의 상속 자산 분배 로직을 정수(integer) 기반으로 전면 리팩토링한 변경 사항입니다. 이로 인해 분배 과정에서 발생하던 미세한 자산(dust)의 유실 및 오차 문제를 원천적으로 해결했습니다. 또한, 변경된 로직을 검증하기 위한 포괄적인 단위 테스트(`test_inheritance_manager.py`)가 추가되었습니다.

### 2. 🚨 Critical Issues
- **없음**: 이번 변경 사항에서 보안 취약점, 하드코딩된 비밀/경로, 또는 심각한 시스템 결함은 발견되지 않았습니다.

### 3. ⚠️ Logic & Spec Gaps
- **없음**: 로직이 매우 견고하게 개선되었습니다.
  - **Zero-Sum 준수**: 기존 로직에서는 반올림 오류로 남은 자산을 정부에 귀속시키는 별도의 처리가 필요했으나, 새 로직은 나머지 자산(cash의 penny, stock의 1주)을 상속자에게 정확히 분배하여 자산 총량 보존(Zero-Sum) 원칙을 완벽하게 준수합니다. 이는 시스템의 재정적 무결성을 크게 향상시킵니다.
  - **테스트 강화**: `tests/verification/verify_inheritance.py`에서 `settlement_system.transfer` 호출 시 실제 자산의 증감을 시뮬레이션하는 `side_effect`를 추가한 것은 매우 훌륭한 개선입니다. 이는 Mock 객체의 한계를 극복하고 테스트의 신뢰도를 높입니다.

### 4. 💡 Suggestions
- `simulation/systems/inheritance_manager.py`의 주식 잔여분 배분 로직에 주석을 추가하여 의도를 명확히 하면 유지보수에 도움이 될 것입니다.
  ```python
  # L307: simulation/systems/inheritance_manager.py

  # 3. Distribute remainder shares one-by-one to heirs until exhausted
  # Note: This ensures fairness and that all shares are distributed.
  for i in range(remainder_shares):
      heir = heirs[i]
      # ...
  ```

### 5. 🧠 Manual Update Proposal
이번 변경 사항은 시뮬레이션의 재정적 안정성을 위한 핵심 원칙을 보여줍니다. 기존 개발 지침에 이를 명문화할 것을 제안합니다.

- **Target File**: `design/개발지침.md`
- **Update Content**:
  ```markdown
  ## 4. 재무 계산 원칙 (Financial Calculation Principles)

  ### 4.1. 부동소수점(Float) 사용 금지 원칙
  - **규칙**: 시뮬레이션 내에서 화폐, 주식 등 분할될 수 있는 자산을 계산할 때는 절대로 `float` 자료형을 직접 사용하지 않는다.
  - **현상**: `float` 연산은 미세한 오차를 유발하며, 이는 시스템 전체적으로 자산이 미세하게 생성(creation)되거나 소멸(leak)되는 결과를 초래한다. (참조: WO-112)
  - **해결**:
    - **화폐(Cash)**: 항상 가장 작은 단위(예: penny)의 정수(integer)로 변환하여 모든 계산(덧셈, 뺄셈, 분배)을 수행한다. 최종 결과를 사용자에게 보여줄 때만 100으로 나누어 소수점 형태로 표현한다.
    - **주식(Stocks)**: 주식은 더 이상 쪼갤 수 없는 최소 단위(1주)이므로, 분배 시 정수 나눗셈(`//`)과 나머지 연산(`%`)을 사용하여 몫과 나머지 주식 수를 정확히 계산하고 분배한다.
  - **교훈**: 금융 시스템의 무결성은 정수 기반 계산에서 시작된다. 부동소수점 오차는 사소해 보이지만, 누적되면 시스템 전체의 신뢰도를 파괴할 수 있다.
  ```

### 6. ✅ Verdict
- **APPROVE**: 부동소수점 오류라는 근본적인 버그를 수정하고, 포괄적인 테스트를 추가하여 코드의 안정성과 신뢰성을 크게 향상시킨 훌륭한 변경입니다. 즉시 머지하는 것을 승인합니다.
