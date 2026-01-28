# 🔍 Git Diff Review: WO-053 Reactivation

## 1. 🔍 Summary

이번 변경은 시뮬레이션에 **규칙 기반(Rule-Based) 의사결정 엔진**을 도입하고, **시나리오 로더(Scenario Loader)**를 구현하여 설정 기반의 동적 시뮬레이션을 가능하게 합니다. "산업 혁명" 시나리오(`phase23_industrial_rev`)와 이를 검증하는 스크립트가 추가되었으며, 공급 과잉과 가격 붕괴를 시뮬레이션하기 위해 기존의 긴급 구매(Emergency Buy) 메커니즘을 우회하는 로직이 포함되었습니다.

## 2. 🚨 Critical Issues

- **없음**: 보안 취약점이나 치명적인 버그는 발견되지 않았습니다.

## 3. ⚠️ Logic & Spec Gaps

- **[MINOR] 퇴직금 계산 로직 부정확성**:
    - **파일**: `simulation/decisions/rule_based_firm_engine.py`
    - **내용**: 새로운 `_fire_excess_labor` 함수에서 퇴직금(`severance_pay`)을 계산할 때, 실제 해고되는 직원의 임금이 아닌 시장 최저 임금(`min_wage`)을 기준으로 일괄 계산합니다.
    - **영향**: 이는 이전에 주석 처리된 코드에서 직원의 실제 임금과 기술 수준을 사용하던 것과 비교해 **논리적 회귀(Logic Regression)**이며, 경제 전체의 자금 흐름에 미치는 영향이 의도와 다를 수 있습니다. 이 단순화가 의도된 것인지 확인이 필요합니다.

## 4. 💡 Suggestions

- **[HIGH] 아키텍처 위반: 시나리오 이름 하드코딩**:
    - **파일**: `simulation/orchestration/phases.py` (line ~409)
    - **내용**: `phase23_industrial_rev`라는 특정 시나리오 이름을 직접 확인하여 구매 가격을 강제로 낮추는 로직이 핵심 오케스트레이션 코드에 하드코딩되어 있습니다.
    - **문제점**: 이는 **관심사 분리(SoC) 원칙**을 심각하게 위반합니다. 오케스트레이션 로직은 특정 시나리오의 존재를 알아서는 안 됩니다. 이 구조는 새로운 시나리오가 추가될 때마다 코드를 수정해야 하는 기술 부채를 유발합니다.
    - **개선 제안**:
        - 시나리오 JSON 파일(`config/scenarios/phase23_industrial_rev.json`)에 `"BUY_PRICE_CAP_MULTIPLIER": 0.8` 와 같은 파라미터를 추가합니다.
        - `Phase1_Decision` 로직은 이 파라미터가 존재할 경우에만 동적으로 가격 상한을 적용하도록 리팩토링합니다. 이렇게 하면 핵심 로직의 재사용성이 높아지고 시나리오 확장이 용이해집니다.
        ```python
        # 제안 (phases.py)
        buy_price_cap = stress_config.get_param(f"{order.item_id}_buy_price_cap_multiplier")
        if buy_price_cap:
            order.price = min(order.price, max(0.1, current_price * buy_price_cap))
        ```

- **[LOW] Magic Number 사용**:
    - **파일**: `simulation/systems/commerce_system.py`
    - **내용**: 시스템 마켓 메이커 ID로 `999999`가 하드코딩되어 있습니다.
    - **개선 제안**: 이 ID는 `config.py`나 관련 상수 모듈에서 `SYSTEM_MARKET_MAKER_ID`와 같은 명명된 상수로 관리하는 것이 가독성과 유지보수성에 더 좋습니다.

## 5. 🧠 Manual Update Proposal

이번 변경 사항에서 중요한 설계 패턴이 도출되었습니다. 이를 프로젝트의 지식 자산으로 남기기 위해 다음 내용의 문서 업데이트를 제안합니다.

- **Target File**: `design/platform_architecture.md` (또는 `design/manuals/SIMULATION_PATTERNS.md`와 같은 설계 문서)
- **Update Content**:
    - **패턴 제목**: "현실적 충격 시뮬레이션을 위한 안전장치 비활성화 패턴 (Disabling Safeties for Realistic Shocks)"
    - **내용**:
        - **현상**: 비료 도입(산업 혁명)으로 인한 공급 충격이 발생해도, 기존의 `emergency_buy` 시스템 때문에 식량 가격이 충분히 하락하지 않는 문제가 있었다. `emergency_buy`는 사실상 무한한 공급과 가격 하한선으로 작용하여 시장 왜곡을 유발했다.
        - **해결**: `phase23_industrial_rev` 시나리오에서는 `emergency_buy`를 비활성화하고, 가계(Household)가 직접 시장(Order Book)에 구매 주문을 내도록 강제했다.
        - **교훈**: 시뮬레이션에서 특정 경제 충격(예: 공급 과잉, 디플레이션)의 효과를 온전히 관찰하려면, 평상시 시스템 안정을 위해 존재하는 **안전장치(예: 정부 개입, 긴급 구매)를 선택적으로 비활성화**해야만 현실적인 시장 가격 발견 메커니즘이 작동한다.

## 6. ✅ Verdict

- **REQUEST CHANGES**

**사유**: 아키텍처의 핵심 원칙을 위반하는 **시나리오 이름 하드코딩** 문제는 반드시 수정되어야 합니다. 이는 장기적인 유지보수성과 확장성에 큰 저해 요소입니다. 퇴직금 계산 로직 또한 의도를 명확히 하고 수정하는 것이 좋습니다.
