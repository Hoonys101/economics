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

## 7. 체크리스트

- [ ] `config.py`에 Maslow/Education 상수 추가
- [ ] `GOODS`에 `education_service` 추가
- [ ] `Household.__init__`에 `education_xp` 추가
- [ ] `Household.consume()`에 education 처리 로직
- [ ] `household_ai.py`에 Gating 로직 추가
- [ ] `inherit_brain()`에 학습률 보너스 로직
- [ ] DB 스키마 업데이트
- [ ] 검증 테스트 작성
