# W-1 Specification: Maslow's Hierarchy & Education

**모듈**: Task #6 - Desire Hierarchy  
**상태**: ✅ Approved (구현 가능)  
**전제**: Phase 2 (Mitosis) 완료 필수  
**대상 파일**: `config.py`, `simulation/ai/household_ai.py`, `simulation/core_agents.py`, `simulation/db/schema.py`

---

## 1. 개요

에이전트에게 **욕구 우선순위(Maslow Gating)**를 부여하고, 교육(Education) 투자가 자녀의 학습 능력을 향상시키는 시스템.

---

## 2. Config 추가 (`config.py`)

```python
# --- Maslow Hierarchy ---
MASLOW_SURVIVAL_THRESHOLD = 50.0  # 이 값 초과 시 상위 욕구 비활성화

# --- Education Service ---
EDUCATION_SENSITIVITY = 0.1       # 교육 효과 민감도
BASE_LEARNING_RATE = 0.1          # 기본 학습률
MAX_LEARNING_RATE = 0.5           # 최대 학습률
LEARNING_EFFICIENCY = 1.0         # XP 획득 효율
```

---

## 3. Maslow Gating Logic (`household_ai.py`)

### 3.1 수정 위치
`decide_action_vector()` 또는 utility 계산 로직

### 3.2 로직 (Pseudo-code)
```python
def calculate_masked_utility(item, needs, config):
    IS_STARVING = needs.get('survival', 0) > config.MASLOW_SURVIVAL_THRESHOLD
    
    # 생존 효용은 항상 계산
    utility = item.effects.get('survival', 0) * needs.get('survival', 0)
    
    # [Gating] 배고프지 않을 때만 상위 욕구 활성화
    if not IS_STARVING:
        utility += item.effects.get('social', 0) * needs.get('social', 0)
        utility += item.effects.get('improvement', 0) * needs.get('improvement', 0)
    
    return utility
```

---

## 4. Education Service

### 4.1 상품 정의 (`config.py` GOODS에 추가)
```python
"education_service": {
    "production_cost": 20,
    "initial_price": 50.0,
    "utility_effects": {"improvement": 15},
    "is_service": True  # 재고 미적용
}
```

### 4.2 Household 속성 추가 (`core_agents.py`)
```python
# __init__에 추가
self.education_xp: float = 0.0
```

### 4.3 소비 시 XP 적립 (`Household.consume()`)
```python
if item_id == "education_service":
    self.education_xp += quantity * config.LEARNING_EFFICIENCY
    # 서비스는 재고에 추가하지 않음
    return
```

---

## 5. Mitosis 연동 (자녀 학습률 보너스)

### 5.1 수정 위치
`Household.check_mitosis()` 또는 `AITrainingManager.inherit_brain()`

### 5.2 로직 (Pseudo-code)
```python
import math

# 부모의 교육 XP에 비례하여 자녀 학습률 향상
xp_bonus = math.log1p(parent.education_xp) * config.EDUCATION_SENSITIVITY
child_ai = child.decision_engine.ai_engine

child_ai.base_alpha = min(
    config.MAX_LEARNING_RATE,
    config.BASE_LEARNING_RATE + xp_bonus
)
```

---

## 6. DB 스키마 (`schema.py` / Alembic)

```sql
ALTER TABLE agent_states ADD COLUMN education_xp REAL DEFAULT 0.0;
```

---

## 7. Architectural Decisions (V2 Engine Compatibility)

본 시뮬레이션의 V2 AI 구조(다채널 적극성 벡터)와의 정합성을 위해 다음과 같이 구현을 확정함.

### 7.1 Maslow Gating in Multi-Channel AI
- **위치**: `household_ai.py` -> `decide_action_vector()`
- **정책 (Action Masking)**:
    - 가계의 `survival` 욕구가 `MASLOW_SURVIVAL_THRESHOLD`를 초과할 경우:
        - `survival` 효용이 없는 모든 품목(`luxury_food`, `clothing`, `education_service` 등)의 적극성을 **0.0**으로 강제 고정.
        - `investment_aggressiveness`를 **0.0**으로 강제 고정.
- **보상 보정**: `_calculate_reward`에서 `IS_STARVING` 상태일 때 상위 욕구 해소로 인한 보상을 0으로 처리하거나 대폭 삭감.

### 7.2 Service Consumption Logic
- **정의**: `is_service: True`인 품목은 실물 재고가 없으며 구매 즉시 효용을 발생시킴.
- **위치**: `engine.py` -> `match_orders` 이후 `process_transactions` 루프
- **정책**:
    - 거래 성공 시, 해당 품목이 `is_service`라면 `buyer.consume()`을 즉시 호출.
    - `Household.consume()`은 해당 품목이 서비스인 경우 인벤토리 체크를 생략하고 `xp` 또는 `utility`만 즉시 반영하고 종료.

---

## 8. 체크리스트


- [ ] `config.py`에 Maslow/Education 상수 추가
- [ ] `GOODS`에 `education_service` 추가
- [ ] `Household.__init__`에 `education_xp` 추가
- [ ] `Household.consume()`에 education 처리 로직
- [ ] `household_ai.py`에 Gating 로직 추가
- [ ] `inherit_brain()`에 학습률 보너스 로직
- [ ] DB 스키마 업데이트
- [ ] 검증 테스트 작성
