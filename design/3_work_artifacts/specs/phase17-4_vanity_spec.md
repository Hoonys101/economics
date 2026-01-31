# Phase 17-4: The Society of Vanity (허영의 사회)
## W-1 상세 설계서

> ****: 상대적 박탈감(Relative Deprivation)과 베블런 효과(Veblen Effect) 구현

---

## 1. 핵심 결정 사항 (Decision Specs)

| 항목 | 결정 | 근거 |
|------|------|------|
| Reference Group | **상위 20%** | 중산층 붕괴 유도에 최적 |
| Conformity | **신규 독립 변수** | 야망(Ambition)과 분리 |
| Veblen Good | **명시적 태그 (`is_veblen`)** | 인플레이션 버그 방지 |

---

## 2. 데이터 & 인터페이스

### 2.1 신규 속성

#### `Household` 확장
```python
# simulation/core_agents.py
class Household:
 conformity: float # 0.0~1.0, 동조성 (Personality에서 초기화)
 social_rank: float # 0.0~1.0, 매 틱 갱신되는 백분위
```

#### `config.py` Feature Flags
```python
# --- Phase 17-4: Vanity System ---
ENABLE_VANITY_SYSTEM = True
VANITY_WEIGHT = 1.0 # 허영심 강도 (0=불교, 1=자본주의)
MIMICRY_FACTOR = 0.5 # 모방 소비 강도
REFERENCE_GROUP_PERCENTILE = 0.20 # 상위 20%

# --- Existing Toggles (확장) ---
ENABLE_PSYCHOLOGY = True
GOVERNMENT_MODE = "ACTIVE" # "ACTIVE" | "PASSIVE"
ENABLE_MORTGAGE = True
```

#### `GOODS` 확장
```python
GOODS = {
 "luxury_bag": {
 "production_cost": 500,
 "initial_price": 2000.0,
 "utility_effects": {"social": 50},
 "is_luxury": True,
 "is_veblen": True, # 가격↑ → 수요↑
 "sector": "LUXURY",
 },
 # 기존 goods에 is_veblen: False 추가
}
```

---

## 3. 로직 & 알고리즘

### 3.1 Social Rank 산정 (매 틱)

```python
def update_social_ranks(households: List[Household]):
 # 1. 점수 계산: 소비량 + 주거등급 가중합
 scores = []
 for h in households:
 consumption_score = h.current_consumption
 housing_score = get_housing_tier(h) * 1000 # Tier 3 = 3000
 total = consumption_score + housing_score
 scores.append((h.id, total))

 # 2. 정렬 후 백분위 할당
 sorted_scores = sorted(scores, key=lambda x: x[1], reverse=True)
 n = len(sorted_scores)
 for rank, (hid, _) in enumerate(sorted_scores):
 household = get_household(hid)
 household.social_rank = 1.0 - (rank / n) # 1위=1.0, 꼴찌=0.0
```

### 3.2 Reference Standard 계산

```python
def calculate_reference_standard(households: List[Household]) -> dict:
 # 상위 20% 추출
 top_20_count = max(1, int(len(households) * 0.20))
 sorted_hh = sorted(households, key=lambda h: h.social_rank, reverse=True)
 top_20 = sorted_hh[:top_20_count]

 return {
 "avg_consumption": mean([h.current_consumption for h in top_20]),
 "avg_housing_tier": mean([get_housing_tier(h) for h in top_20]),
 }
```

### 3.3 유틸리티 함수 개편

```python
def calculate_total_utility(household, config) -> float:
 # 기존 내재적 효용
 U_intrinsic = household.calculate_intrinsic_utility()

 if not config.ENABLE_VANITY_SYSTEM:
 return U_intrinsic

 # 사회적 요소
 ref_rank = config.REFERENCE_GROUP_PERCENTILE # 0.80 (상위 20%의 최하위)
 my_rank = household.social_rank
 social_component = my_rank - ref_rank # 음수면 불행

 # 동조성 가중
 vanity_effect = household.conformity * social_component * config.VANITY_WEIGHT

 return U_intrinsic + (vanity_effect * 100) # 스케일 조정
```

### 3.4 베블런재 수요 함수

```python
def calculate_veblen_demand(good_id, price, household, config) -> float:
 good = config.GOODS[good_id]

 if not good.get("is_veblen", False):
 return normal_demand(price, household)

 # 가격이 높을수록 과시 가치 증가
 prestige_value = price * 0.1 * household.conformity
 adjusted_utility = good["utility_effects"]["social"] + prestige_value

 # 수요 = 효용 / 가격 (but 가격↑ → 효용↑ 더 빠르게)
 return adjusted_utility / (price ** 0.5) # 제곱근으로 둔화
```

### 3.5 모방 소비 AI (HousingManager 확장)

```python
def decide_mimicry_purchase(household, reference_standard, config):
 if not config.ENABLE_VANITY_SYSTEM:
 return None

 gap = reference_standard["avg_housing_tier"] - get_housing_tier(household)

 if gap <= 0:
 return None # 이미 상위권

 # 따라잡기 욕구 = 동조성 × 격차 × 모방 팩터
 urgency = household.conformity * gap * config.MIMICRY_FACTOR

 if urgency > 0.5: # 임계값
 # YOLO 모드: 저축 포기, 레버리지 극대화
 return PurchaseIntent(
 target="housing_tier_3",
 max_ltv=0.95, # 5% 다운페이먼트
 priority="URGENT"
 )
 return None
```

---

## 4. 예외 처리

| 상황 | 대응 |
|------|------|
| 가계 수 < 5 | Reference Group = 전체 |
| 소비/주거 데이터 없음 | Rank = 0.5 (중간값) |
| Conformity 미설정 | 기본값 0.5 |

---

## 5. 검증 계획

### 5.1 Unit Tests
- `test_social_rank_calculation`: 랭킹 정렬 정확성
- `test_veblen_demand`: 가격↑ → 수요↑
- `test_mimicry_trigger`: 격차 임계값 동작

### 5.2 Integration Test (`verify_vanity_society.py`)
```python
def test_rat_race_scenario():
 # 100틱 시뮬레이션 후:
 # 1. 중산층(40~60%) 저축률 < 0%
 # 2. Tier 3 주택 가격 > 초기값 * 2
 # 3. social_rank < 0.5인 에이전트 중 50% 이상이 "불행" (U_total < 0)
```

---

## 6. 파일 변경 목록

| 파일 | 변경 유형 | 내용 |
|------|----------|------|
| `config.py` | MODIFY | Feature Flags, GOODS 확장 |
| `simulation/core_agents.py` | MODIFY | `conformity`, `social_rank` 추가 |
| `simulation/engine.py` | MODIFY | `update_social_ranks()` 호출 |
| `simulation/decisions/housing_manager.py` | MODIFY | 모방 소비 로직 |
| `simulation/ai/household_ai.py` | MODIFY | 유틸리티 함수 개편 |
| `tests/verify_vanity_society.py` | NEW | 통합 검증 테스트 |
