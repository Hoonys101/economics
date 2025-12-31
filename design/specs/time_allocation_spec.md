# W-1 Specification: Phase 5 - Time Allocation & Genealogy

**모듈**: Phase 5 - Hydraulic Time Model  
**상태**: 🟢 Approved by Architect Prime  
**작성자**: Antigravity (Team Leader)  
**전제**: Phase 4 (Fiscal Policy) 구현 완료  
**대상 파일**: `config.py`, `simulation/core_agents.py`, `simulation/ai/household_ai.py`

---

## 1. 개요 (Overview)

세금이 높을 때 에이전트가 **"일을 포기하고 여가를 선택"**하는 합리적 행동을 구현한다.
기존 AI 아키텍처(Continuous Q-Learning)를 유지하면서 **[유압 모델]**을 적용:
- **별도의 LEISURE 행동 없음**
- `work_aggressiveness`가 낮으면 자동으로 여가 시간 증가

---

## 2. Schema Update (Genealogy)

### 2.1 Household 클래스 확장

```python
class Household:
    def __init__(self, ...):
        self.parent_id: Optional[int] = None  # 부모 ID (분열 시 기록)
        self.children_ids: List[int] = []     # 자녀 ID 목록
        self.generation: int = 0              # 세대 (0, 1, 2...)
```

### 2.2 Mitosis 로직 수정 (`check_mitosis`)

분열 시 부모-자녀 관계 기록:
```python
# Parent
parent.children_ids.append(child.id)

# Child
child.parent_id = parent.id
child.generation = parent.generation + 1
```

---

## 3. Time Allocation Logic (Hydraulic Model)

### 3.1 Config 추가

```python
# --- Phase 5: Time Allocation ---
HOURS_PER_TICK = 24.0
WORK_HOURS_MAX = 10.0  # work_aggressiveness=1.0일 때 노동 시간

# Leisure Utility Weights
LEISURE_ALPHA = 0.5  # Current Happiness (Social Need)
LEISURE_BETA = 1.0   # Child Education Investment
```

### 3.2 시간 배분 공식

```
Work_Time = work_aggressiveness * WORK_HOURS_MAX
Leisure_Time = HOURS_PER_TICK - Work_Time - Shopping_Time (fixed ~2hrs)
```

### 3.3 Implicit Leisure Types (자동 분류)

| Type | 조건 | 효과 |
|------|------|------|
| **Parenting** | `children_ids` 존재 AND `education_service` 구매 | 자녀 XP 대폭 증가 |
| **Entertainment** | `luxury_food` or `clothing` 다량 구매 | Social Need 대폭 회복 |
| **Self-Dev** | 위 조건 불충족 (Default) | 본인 Productivity 소폭 증가 |

---

## 4. Reward Function Update

### 4.1 현재 보상 함수 (Before)

```
Reward = f(Asset_Change, Need_Satisfaction, ...)
```

### 4.2 수정된 보상 함수 (After)

```
Reward = (Income * (1 - Tax_Rate)) + Leisure_Utility

Leisure_Utility = α * Social_Need_Satisfaction + β * Child_XP_Gain
```

**목표**: 세율이 높아지면 `(Income * (1 - Tax))` 항목이 줄어들어, AI가 자연스럽게 `work_aggressiveness`를 낮추고 `Leisure_Utility`를 챙기도록 유도.

---

## 5. 구현 체크리스트

- [ ] **5.1 Schema Patch**: `Household`에 `parent_id`, `children_ids`, `generation` 추가
- [ ] **5.2 Mitosis Update**: 분열 시 ID 연결 로직 추가
- [ ] **5.3 Config Update**: `HOURS_PER_TICK`, `LEISURE_ALPHA`, `LEISURE_BETA` 추가
- [ ] **5.4 Reward Function**: `household_ai.py`에서 Leisure Utility 반영
- [ ] **5.5 Leisure Effect**: `decide_and_consume`에서 여가 유형별 효과 적용

---

## 6. 검증 계획

1. **래퍼 곡선 검증**: 세율 0% → 50% → 90% 시나리오에서 `work_aggressiveness` 변화 추적
2. **부모-자녀 XP 전달**: Parenting 여가 시 자녀 XP 증가 확인
3. **Gini 변화**: 고세율 시 불평등 감소 또는 증가 패턴 분석
