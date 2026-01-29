# 🔍 Git Diff Review: WO-136 Tech & Market Dynamics

## 1. 🔍 Summary

이번 변경은 **WO-136**의 일환으로 두 가지 핵심적인 개선을 도입했습니다.
첫째, 시장(`OrderBookMarket`)에 가격 변동성에 기반한 **동적 서킷 브레이커**를 구현하여 비정상적인 가격 주문을 자동으로 거부합니다.
둘째, 기술 발전(`TechnologyManager`) 모델을 기존의 **시간 기반(tick-based) 해금 방식에서 R&D 투자 누적에 따른 확률적 해금 방식**으로 변경하고, 관련 로직을 NumPy를 사용하여 벡터화함으로써 대규모 에이전트 환경에서의 성능을 최적화했습니다.

## 2. 🚨 Critical Issues

- 발견되지 않았습니다. API 키, 시스템 절대 경로, 외부 레포지토리 URL 등의 심각한 보안 문제는 포함되지 않았습니다.

## 3. ⚠️ Logic & Spec Gaps

- 발견되지 않았습니다. 로직은 Spec의 의도(동적 서킷 브레이커, R&D 기반 기술 해금)와 일치하며, 자산의 부적절한 생성이나 소멸(Zero-Sum 위반)은 보이지 않습니다.

## 4. 💡 Suggestions

코드의 유연성과 유지보수성을 높이기 위해 일부 하드코딩된 파라미터를 설정 파일로 이전할 것을 권장합니다.

1.  **`simulation/markets/order_book_market.py`**
    - **[~L.56]** `get_dynamic_price_bounds` 함수 내의 `base_limit = 0.15`는 서킷 브레이커의 기본 범위를 결정하는 중요한 파라미터입니다. `config/economy_params.yaml` 등으로 옮겨 관리하는 것이 좋습니다.

2.  **`simulation/systems/technology_manager.py`**
    - **[~L.63]** `__post_init__`에서 설정된 기본값 `cost_threshold = 5000.0`은 기술 해금 비용의 기준점이므로 설정 파일에서 관리하는 것이 바람직합니다.
    - **[~L.106]** `_check_probabilistic_unlocks` 함수 내의 해금 확률 상한선 `prob = min(0.1, ratio ** 2)`에서 `0.1`은 핵심적인 게임 밸런스 수치입니다. 이 또한 설정 파일로 이전하여 쉽게 조정할 수 있도록 해야 합니다.

## 5. 🧠 Manual Update Proposal

이번 변경에서 R&D 투자 기반의 기술 해금 모델을 도입한 것은 중요한 경제학적 인사이트이므로, 관련 원칙을 문서화하여 팀 전체가 공유해야 합니다.

- **Target File**: `design/2_operations/ledgers/ECONOMIC_INSIGHTS.md` (해당 파일이 없다면 신규 생성 제안)
- **Update Content**:
    ```markdown
    ## [INSIGHT] R&D 투자와 내생적 기술 혁신 모델
    
    - **현상 (Phenomenon):**
      기존 기술 발전 모델은 `unlock_tick`이라는 고정된 시간(Time-based)에 의존하여, 기업의 노력과 무관하게 기술이 확정적으로 해금되었습니다. 이는 현실 경제의 불확실성과 동적인 혁신 과정을 반영하지 못했습니다.
    
    - **원인 (Cause):**
      시간 기반 모델은 기업의 핵심 활동인 R&D 투자를 기술 발전과 연계시키지 못하여, 시뮬레이션의 깊이를 제한하고 플레이어의 전략적 선택(투자)의 중요성을 반감시켰습니다.
    
    - **해결 (Solution):**
      `TechnologyManager`를 리팩토링하여, `cost_threshold`(기술 개발 비용)와 기업들의 누적 R&D 투자를 기반으로 한 **확률적 해금 모델** (`P = min(CAP, (Sector_R&D / Cost)^2)`)을 도입했습니다. (참조: `_check_probabilistic_unlocks`)
    
    - **교훈 (Lesson Learned):**
      시뮬레이션의 핵심 이벤트(기술 혁신 등)는 **내생적 변수(Endogenous Variable)**, 즉 에이전트들의 활동(예: R&D 투자)에 의해 결정되어야 합니다. 이는 시스템의 현실성을 높이고, 에이전트의 전략적 행동에 의미를 부여하며, 예측 불가능하고 역동적인 결과를 창출하는 기반이 됩니다.
    ```

## 6. ✅ Verdict

**REQUEST CHANGES**

> 전반적인 로직과 성능 개선은 매우 훌륭합니다. 다만, 제안된 하드코딩 파라미터들을 설정 파일로 리팩토링하여 코드의 유연성을 확보한 후 머지하는 것을 권장합니다. 또한, 인사이트 문서화를 진행하여 지식을 자산화해주십시오.
