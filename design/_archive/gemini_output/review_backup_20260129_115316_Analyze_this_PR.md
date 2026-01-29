# 🔍 Git Diff 리뷰 보고서: WO-146 통화 정책 구현

---

### 1. 🔍 Summary

이번 변경 사항은 Taylor Rule에 기반한 동적 통화 정책 관리 모듈(`MonetaryPolicyManager`)을 도입하고, 이를 시뮬레이션의 `Phase0_PreSequence`에 통합하여 중앙은행의 기준 금리를 결정하도록 합니다. 또한, 기업의 대출 이자율이 하드코딩된 값 대신 시장 기준 금리를 따르도록 수정하여 시스템의 경제적 현실성을 높였습니다. 새로운 기능에 대한 단위 테스트가 함께 추가되었습니다.

### 2. 🚨 Critical Issues

**없음.** API 키, 비밀번호 등 민감 정보의 하드코딩이나 외부 레포지토리 경로 유출과 같은 심각한 보안 취약점은 발견되지 않았습니다.

### 3. ⚠️ Logic & Spec Gaps

*   **[의존성 높은 하드코딩]** `simulation/decisions/firm/finance_manager.py` (line 96)
    *   **문제점**: 시장에서 기준 금리(`interest_rate`)를 가져오지 못했을 때, `base_rate = 0.05`로 하드코딩된 값을 사용합니다. 이는 '하드코딩된 이자율 제거'라는 이번 작업의 핵심 목표와 상충됩니다.
    *   **영향**: 시장 데이터가 없는 초기 상태나 특정 시나리오에서 기업의 대출 이자율이 엉뚱한 값으로 고정되어 경제 왜곡을 유발할 수 있습니다.

*   **[잠재적 시스템 불안정성]** `simulation/orchestration/phases.py` (line 250-255)
    *   **문제점**: 코드 내 주석에서도 언급되었듯이, 통화 정책을 매 시뮬레이션 '틱'마다 결정하고 기준 금리를 덮어쓰는 것은 금리의 과도한 변동성을 초래하여 시스템 불안정성을 야기할 수 있습니다.
    *   **영향**: 단기적인 시장 지표 변화에 통화 정책이 과민 반응하여, 장기적으로 안정되어야 할 거시 경제 환경에 불필요한 노이즈를 증폭시킬 수 있습니다.

### 4. 💡 Suggestions

*   **[하드코딩 제거]** `finance_manager.py`의 `base_rate` 폴백 값을 `0.05` 대신, `MonetaryPolicyManager`가 사용하는 `self.neutral_rate`나 설정 파일(`config_module`)에서 관리되는 중앙 상수를 사용하도록 리팩토링하는 것을 제안합니다. 이는 시스템 전체의 일관성을 높이고 설정 변경을 용이하게 합니다.

    ```python
    # 제안 (finance_manager.py)
    # config에서 중립 금리나 기본 금리를 가져오는 로직 필요
    from some_config_path import NEUTRAL_RATE 
    ...
    base_rate = loan_market_data.get("interest_rate", NEUTRAL_RATE) 
    ```

*   **[테스트 강화]** `test_monetary_policy_manager.py`에서 `nominal_gdp` 또는 `potential_gdp`가 `0`이거나 음수인 경우에 대한 엣지 케이스 테스트를 추가하여 `math.log` 함수에서 발생할 수 있는 `ValueError`를 방어하는 로직이 올바르게 동작하는지 검증하는 것이 좋습니다.

### 5. 🧠 Manual Update Proposal

이번 변경 사항에서 발견된 "실시간 반응성과 시스템 안정성 간의 트레이드오프"는 중요한 기술적 교훈이므로, 별도의 인사이트 파일로 기록하여 추후 아키텍처 개선 시 참고 자료로 활용할 것을 제안합니다.

*   **Target File**: `communications/insights/WO-146-Monetary-Policy-Stability.md` (신규 생성)
*   **Update Content**:
    ```markdown
    # Insight Report: WO-146 Monetary Policy Stability Trade-off

    ## 현상
    중앙은행의 기준 금리가 시뮬레이션의 매 틱(tick)마다 재계산되어 적용됩니다. 이로 인해 단기 시장 지표의 미세한 변동에도 기준 금리가 민감하게 반응하여 잠재적인 변동성을 유발할 수 있습니다.

    ## 원인
    `simulation/orchestration/phases.py`의 `Phase0_PreSequence` 단계에서, 경제 상황 변화에 대한 통화 정책의 즉각적인 반응성을 확보하기 위해 `MonetaryPolicyManager`가 매 틱 호출되도록 구현되었습니다.

    ## 해결
    현재는 반응성을 우선하여 매 틱 업데이트 방식을 유지합니다. 하지만 이로 인한 불안정성이 관찰될 경우, 정책 결정 주기를 도입(예: 10틱마다 또는 특정 이벤트 발생 시에만 업데이트)하여 금리 변동을 완화하는 방안을 고려해야 합니다.

    ## 교훈
    거시 경제 정책(통화 정책 등)을 모델링할 때, 실시간 데이터 반응성과 시스템의 장기적 안정성 사이에는 명확한 트레이드오프 관계가 존재합니다. 정책 결정의 빈도가 너무 높으면 오히려 시장에 불필요한 노이즈를 주입하여 예측 불가능성을 높일 수 있습니다. 따라서 정책의 특성에 맞는 적절한 업데이트 주기(Update Frequency)를 설계하는 것이 중요합니다.
    ```

### 6. ✅ Verdict

**REQUEST CHANGES**

- 위 `Logic & Spec Gaps`에서 지적된 하드코딩 문제를 수정해야 합니다.
- `Manual Update Proposal`에 제안된 인사이트 기록을 반영하여, 이번 개발 과정에서 얻은 교훈을 자산화해주십시오.
