# WO-015: 3-Pillars 성향 모델 구현 (Organic Interest Sensitivity)

## 1. 개요
**목표**: 가계 에이전트의 의사결정에 **3가지 욕망(Desire)** 성향을 반영하여, 금리 변화에 대한 반응이 **작위적 규칙이 아닌 유기적 경쟁**을 통해 발현되도록 구현.

**핵심 개념**: 에이전트는 매 틱마다 "빵(소비)"과 "예금(저축)" 중 더 높은 효용을 주는 쪽을 선택한다.

## 2. 3 Pillars of Desire (성향의 3요소)

| 성향 | 속성명 | 설명 | 영향 |
|------|--------|------|------|
| 자산의 성장 | `preference_asset` | 미래의 부가 현재의 쾌락보다 중요 | 저축 효용(U_save) 가중치 |
| 사회적 영향력 | `preference_social` | 브랜드, 과시적 소비 중시 | 사치재 소비 효용 가중치 |
| 자신의 성장 | `preference_growth` | 생존, 기초 필수품 우선 | 필수재 소비 효용 가중치 |

## 3. 구현 상세

### 3.1 Household 클래스 수정
**파일**: `simulation/core_agents.py`

```python
class Household:
    def __init__(self, ...):
        # 기존 속성들...
        
        # NEW: 3-Pillars 성향 (0.5 ~ 1.5 범위, 합계 = 3.0)
        self.preference_asset = 1.0   # 자산 성장 욕구
        self.preference_social = 1.0  # 사회적 지위 욕구
        self.preference_growth = 1.0  # 생존/성장 욕구
```

### 3.2 Value Orientation과 성향 매핑
**파일**: `simulation/core_agents.py` 또는 `config.py`

```python
VALUE_ORIENTATION_MAPPING = {
    "WEALTH_AND_NEEDS": {
        "preference_asset": 1.3,
        "preference_social": 0.7,
        "preference_growth": 1.0
    },
    "NEEDS_AND_GROWTH": {
        "preference_asset": 0.8,
        "preference_social": 0.7,
        "preference_growth": 1.5
    },
    "NEEDS_AND_SOCIAL_STATUS": {
        "preference_asset": 0.7,
        "preference_social": 1.5,
        "preference_growth": 0.8
    }
}
```

### 3.3 의사결정 엔진 수정
**파일**: `simulation/decisions/ai_driven_household_engine.py`

```python
def make_decisions(self, household, markets, goods_data, market_data, current_time, government):
    # ... 기존 코드 ...
    
    # 1. 저축 효용 계산 (금리 민감도)
    real_rate = nominal_rate - avg_expected_inflation
    savings_roi = (1 + real_rate) * household.preference_asset
    
    # 2. 각 상품별 소비 효용 계산
    for item_id in goods_list:
        good_info = config.GOODS.get(item_id, {})
        is_luxury = good_info.get("is_luxury", False)
        
        if is_luxury:
            # 사치재: preference_social 적용
            consumption_roi = (need_value / price) * household.preference_social
        else:
            # 필수재: preference_growth 적용
            consumption_roi = (need_value / price) * household.preference_growth
        
        # 3. 효용 경쟁: 저축 vs 소비
        if savings_roi > consumption_roi:
            attenuation = consumption_roi / savings_roi
            agg_buy *= attenuation
```

## 4. 검증 계획

### 4.1 단위 테스트
- `tests/test_3_pillars.py` 생성
- 동일한 금리에서 `preference_asset`이 높은 에이전트가 더 빨리 저축으로 전환하는지 확인

### 4.2 통합 테스트
- `scripts/iron_test.py --num_ticks 100` 실행
- 금리 5% 시나리오에서:
  - `WEALTH_AND_NEEDS` 성향 가계: 사치재 소비 급감
  - `NEEDS_AND_SOCIAL_STATUS` 성향 가계: 사치재 소비 유지

## 5. 참고 문서
- `design/specs/phase4_5_interest_sensitivity_spec.md`
- 이전 논의: "3 Pillars of Desire" 개념 설계

## 6. 완료 조건
1. `Household` 클래스에 3가지 성향 속성 추가
2. `iron_test.py`에서 성향별 초기화 로직 반영
3. `ai_driven_household_engine.py`에서 ROI 계산에 성향 가중치 적용
4. 100틱 테스트에서 성향별 소비 패턴 차이 확인
