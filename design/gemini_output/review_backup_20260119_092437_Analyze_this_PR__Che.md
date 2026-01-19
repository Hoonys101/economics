# 🔍 Code Review Report: Phase 28 - Stress Testing

## 🔍 Summary
이 변경 사항은 하이퍼인플레이션, 디플레이션, 공급 충격 등 경제 스트레스 시나리오를 시뮬레이션에 도입합니다. 가계(Household) 에이전트의 행동 로직(사재기, 패닉 셀링, 부채 회피)과 의사결정 엔진을 수정하고, 이에 대한 시나리오 트리거 및 기본 단위 테스트를 추가했습니다.

## 🚨 Critical Issues
- **[CRITICAL] 하드코딩된 자산 투매 가격**: `simulation/core_agents.py`의 `Household` 클래스 내 패닉 셀링 로직에서, 주식을 매도할 때 가격을 `0.1`로 하드코딩했습니다.
    ```python
    # simulation/core_agents.py
    stock_order = Order(
        # ...
        price=0.1, # Fire sale price
        market_id="stock_market"
    )
    ```
    이는 시장 가격 메커니즘을 무시하며, 자산 가치를 인위적으로 0에 가깝게 만들 수 있는 심각한 결함입니다. 시장가 주문(e.g., `price=0.0`)이나 마지막 체결가 기반의 동적 가격을 사용해야 합니다.

- **[CRITICAL] 다수의 하드코딩된 '매직 넘버'**: 스트레스 시나리오의 핵심 파라미터들이 코드 전반에 하드코딩되어 있습니다.
    - **패닉 셀링 자산 기준**: `core_agents.py`에서 자산 기준선(threshold)의 기본값이 `500.0`으로 하드코딩되어 있습니다.
    - **부채 상환 비율**: `ai_driven_household_engine.py`에서 부채 상환 시 자산의 `50%`(`* 0.5`), 비상 유동성 `10%`(`* 0.9`) 등 주요 비율이 하드코딩되어 있습니다.
    - **사재기 행동 지수**: `ai_driven_household_engine.py`에서 사재기 시 구매 수량과 지불 의향(WTP)을 증폭시키는 계수(`* 0.5`)가 하드코딩되어 있습니다.
    이러한 값들은 모두 설정 파일(`config.py`) 또는 `StressScenarioConfig` DTO를 통해 관리되어야 합니다.

## ⚠️ Logic & Spec Gaps
- **[MAJOR] 핵심 로직 테스트 부재**: 새로 추가된 `test_stress_scenarios.py`는 시나리오의 시작(현금 주입, 자산 충격 등)만 테스트하고 있습니다. 가장 복잡하고 중요한 에이전트 행동 변화(패닉 셀링, 사재기, 부채 회피)에 대한 단위 테스트가 **전혀 없습니다.** 이는 기능의 정확성을 보장할 수 없는 큰 틈입니다.
- **[MINOR] 사재기 대상 물품 불일치**: `ai_driven_household_engine.py`의 사재기 로직은 `["basic_food", "consumer_goods"]`를 대상으로 하지만, `config.py`에 새로 추가된 `HOUSEHOLD_CONSUMABLE_GOODS`는 `"luxury_food"`를 포함하고 `"consumer_goods"`는 빠져있어 정합성이 맞지 않습니다. 설정 파일을 일관되게 사용해야 합니다.
- **[MINOR] 하드코딩된 인플레이션 대체값**: `simulation/engine.py`에서 시장 데이터에 인플레이션 값을 주입할 때, 값이 없는 경우 `0.02`라는 특정 값으로 대체하고 있습니다. 이는 시뮬레이션 결과에 예상치 못한 편향을 줄 수 있습니다.

## 💡 Suggestions
- **설정 중앙화**: 위에서 지적된 모든 하드코딩된 숫자들을 `config.py` 또는 `StressScenarioConfig`로 옮겨서 시나리오의 강도를 쉽게 조절하고 코드를 명확하게 만드십시오.
- **테스트 커버리지 확대**: `Household` 에이전트와 `AIDrivenHouseholdDecisionEngine`의 `panic_selling`, `hoarding`, `debt_aversion` 로직을 검증하는 상세한 단위 테스트를 추가하십시오. (e.g., 특정 조건에서 적절한 매도/상환 주문이 생성되는지 확인)
- **디버그 코드 제거**: `simulation/engine.py`에 남아있는 `DEBUG_WO057` 관련 로그들을 제거하십시오.

## ✅ Verdict
**REQUEST CHANGES**

새로운 기능의 방향성은 훌륭하고 테스트 코드 추가를 시도한 점은 긍정적이나, 시장 경제의 근간을 흔들 수 있는 하드코딩된 투매 가격과 핵심 로직에 대한 테스트 부재는 매우 심각한 문제입니다. 위에 언급된 Critical 이슈와 테스트 커버리지 문제를 해결한 후 다시 리뷰를 요청하십시오.
