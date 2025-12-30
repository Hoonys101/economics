# W-1 Specification: Mitosis & Inheritance

**모듈**: Phase 2 - Agent Evolution  
**상태**: ✅ Approved (즉시 구현 가능)  
**대상 파일**: `simulation/core_agents.py`, `simulation/ai/ai_training_manager.py`, `simulation/engine.py`, `config.py`

---

## 1. 개요

가계(Household) 에이전트가 부를 축적하면 자아를 복제(Mitosis)하고, 자식에게 자산과 학습된 지능(Q-Table)을 물려주는 시스템.

---

## 1.5 FAQ (Jules 질문 답변)

### Q1: Config Constants 6개 목록?
**A**: 아래 6개 상수를 `config.py`에 추가:
```python
TARGET_POPULATION = 50                    # 목표 인구
MITOSIS_BASE_THRESHOLD = 5000.0           # 분열 자산 요건
MITOSIS_SENSITIVITY = 1.5                 # 인구 압박 민감도
MITOSIS_SURVIVAL_THRESHOLD = 20.0         # 배고픔 한계
MITOSIS_MUTATION_PROBABILITY = 0.2        # 성격 돌연변이 확률
MITOSIS_Q_TABLE_MUTATION_RATE = 0.05      # Q-table 노이즈 비율
```

### Q2: FIRE 조건은?
**A**: 자산 기반 조건. `is_employed OR (assets > mitosis_cost * 2.0)`. 패시브 인컴 계산 없음.

### Q3: 부모는 살아남는가?
**A**: **예**. 부모는 그대로 존속하고, 자식 1명이 새로 생성됨. 부모 사망 아님.

### Q4: 고용 상태는?
**A**: **부모**: 고용 상태 유지. **자식**: `is_employed = False`, `employer_id = None`으로 시작.

### Q5: 50/50 분할 대상은?
**A**: 
- **Cash**: 50/50 (float, 정확히 절반)
- **Inventory**: 분할 안 함 (부모가 전부 보유)
- **Shares**: 50/50, `qty // 2`로 분할 (홀수 시 부모가 +1)

### Q6: 성격 돌연변이 20%란?
**A**: **완전 랜덤 교체**. 20% 확률로 `random.choice(list(Personality))`로 새 성격 할당. 가중치 조정 아님.

### Q7: Q-table 복사 방식?
**A**: 기존 `_clone_and_mutate_q_table()` 메서드 사용. 정확한 복사 + `MITOSIS_Q_TABLE_MUTATION_RATE` 노이즈 적용.

### Q8: run_tick 내 위치?
**A**: **After** 소비 카운터 리셋, **Before** `_handle_agent_lifecycle()` 호출. (즉, 에이전트 사망 처리 전에 분열)

### Q9: 체크리스트?
**A**: 섹션 7에 8개 항목 정의됨. 그대로 사용
---

## 2. Config 추가 (`config.py`)

```python
# --- Mitosis Configuration ---
TARGET_POPULATION = 50
MITOSIS_BASE_THRESHOLD = 5000.0  # 기본 분열 자산 요건
MITOSIS_SENSITIVITY = 1.5       # 인구 압박 민감도
MITOSIS_SURVIVAL_THRESHOLD = 20.0  # 배고픔 한계
MITOSIS_MUTATION_PROBABILITY = 0.2  # 성격 돌연변이 확률
MITOSIS_Q_TABLE_MUTATION_RATE = 0.05  # Q-table 노이즈 비율
```

---

## 3. Household.check_mitosis() (`core_agents.py`)

### 3.1 시그니처
```python
def check_mitosis(
    self, 
    current_population: int, 
    target_population: int,
    new_id: int
) -> Optional["Household"]:
```

### 3.2 로직 (Pseudo-code)
```python
def check_mitosis(self, current_population, target_population, new_id):
    # 1. 동적 임계값 계산
    pop_ratio = current_population / max(1, target_population)
    mitosis_cost = BASE_THRESHOLD * (pop_ratio ** SENSITIVITY)
    
    # 2. FIRE 조건 (Financial Independence, Retire Early)
    is_financially_stable = (
        self.is_employed or 
        self.assets > mitosis_cost * 2.0
    )
    
    # 3. 분열 가능 조건
    can_reproduce = (
        self.assets > mitosis_cost and
        is_financially_stable and
        self.needs["survival"] < SURVIVAL_THRESHOLD
    )
    
    if not can_reproduce:
        return None
    
    # 4. 자산 분할 (50/50)
    child_assets = self.assets / 2
    self.assets /= 2
    
    # 5. 주식 분할 (50/50, 소수점 버림은 부모가 보유)
    child_shares = {}
    for firm_id, qty in self.shares_owned.items():
        child_qty = qty // 2
        self.shares_owned[firm_id] -= child_qty
        if child_qty > 0:
            child_shares[firm_id] = child_qty
    
    # 6. 새 Household 인스턴스 생성 (새 DecisionEngine 포함)
    child = Household(
        id=new_id,
        talent=self.talent,
        goods_data=list(self.goods_info_map.values()),
        initial_assets=child_assets,
        initial_needs={},  # 리셋
        decision_engine=self._create_new_decision_engine(),  # 새 인스턴스!
        value_orientation=self.value_orientation,
        personality=self.personality,  # 일단 복사, inherit_brain에서 돌연변이
        config_module=self.config_module,
        loan_market=self.decision_engine.loan_market,
        logger=self.logger
    )
    child.shares_owned = child_shares
    child.is_employed = False
    child.employer_id = None
    child.needs["survival"] = random.uniform(0, 20)
    
    logger.info(f"MITOSIS | Parent {self.id} -> Child {child.id}")
    return child
```

> [!WARNING]
> **`_create_new_decision_engine()` 헬퍼 필요**: 기존 `clone()` 메서드는 Engine을 참조 복사함. 새 인스턴스 생성 로직 추가 필요.

---

## 4. AITrainingManager.inherit_brain() (`ai_training_manager.py`)

### 4.1 시그니처
```python
def inherit_brain(self, parent_agent: Household, child_agent: Household) -> None:
```

### 4.2 로직
```python
def inherit_brain(self, parent, child):
    # 1. 성격 상속 (80%) 또는 돌연변이 (20%)
    if random.random() < config.MITOSIS_MUTATION_PROBABILITY:
        child.personality = random.choice(list(Personality))
        logger.info(f"MUTATION | {child.id} mutated personality")
    else:
        child.personality = parent.personality
    
    # 2. Q-Table 복사 (기존 _clone_and_mutate_q_table 활용)
    self._clone_and_mutate_q_table(parent, child)
```

---

## 5. Engine 통합 (`engine.py`)

### 5.1 run_tick() 내 삽입 위치
- **After**: 소비 카운터 리셋
- **Before**: 틱 종료 로깅

### 5.2 로직
```python
# --- Mitosis Processing ---
new_children = []
current_pop = len([h for h in self.households if h.is_active])

for household in self.households:
    if not household.is_active:
        continue
    
    child = household.check_mitosis(
        current_population=current_pop,
        target_population=self.config_module.TARGET_POPULATION,
        new_id=self.next_agent_id
    )
    
    if child:
        self.next_agent_id += 1
        new_children.append((household, child))
        current_pop += 1

# 등록 및 뇌 이식
for parent, child in new_children:
    self.households.append(child)
    self.agents[child.id] = child
    child.decision_engine.markets = self.markets
    child.decision_engine.goods_data = self.goods_data
    self.ai_training_manager.agents.append(child)
    
    # 뇌 이식 (Q-Table + 성격)
    self.ai_training_manager.inherit_brain(parent, child)
    
    # 주식 시장 주주 명부 갱신
    if self.stock_market:
        for firm_id, qty in child.shares_owned.items():
            self.stock_market.update_shareholder(child.id, firm_id, qty)
```

> [!IMPORTANT]
> **StockMarket.update_shareholder()** 메서드가 없다면 추가 구현 필요.

---

## 6. W-5 검증 계획 (Verification Plan)

> **목표**: 세포 분열(Mitosis)과 사회적 유전(Inheritance)이 의도대로 작동하여, 인구 안정성과 부의 축적이 일어나는지 검증.

### ✅ Test Case 1: The "Rich Family" Check (분열 기능 검증)

**시나리오**: 초기 자산을 분열 임계값(5000)의 3배인 **15000**으로 설정한 "슈퍼 리치" 에이전트 1명을 투입.

**기대 결과**:
- 시뮬레이션 시작 후 몇 틱 이내에 **자식 에이전트 생성** 확인
- 부모의 자산이 **절반으로 감소**, 자식은 그 절반을 보유
- 총 인구수 증가 (Initial + 1)

**검증 코드 (Pseudo)**:
```python
def test_rich_family_mitosis():
    rich_household = create_household(initial_assets=15000)
    sim.run_tick()
    
    assert len(sim.households) > initial_count
    assert rich_household.assets == 7500  # 50% retained
    child = get_child_of(rich_household)
    assert child.assets == 7500  # 50% inherited
```

---

### ✅ Test Case 2: The "Legacy" Check (상속 검증)

**시나리오**: 부모가 특정 기업의 주식을 보유한 상태에서 분열.

**기대 결과**:

| 항목 | 검증 내용 | 허용 오차 |
|------|----------|---------|
| 자산(Cash) | 정확히 50% 분할 | ±1.0 |
| 주식(Stock) | 보유 수량의 절반이 자식에게 이체 (홀수: 부모 +1) | 0 |
| 지능(Brain) | 자식의 `q_table`이 비어있지 않고 부모와 유사 | N/A |

**검증 코드 (Pseudo)**:
```python
def test_legacy_inheritance():
    parent = create_household(assets=10000)
    parent.shares_owned = {firm_1: 10, firm_2: 7}
    
    child = parent.check_mitosis(new_id=99)
    
    # Cash
    assert abs(parent.assets - 5000) < 1.0
    assert abs(child.assets - 5000) < 1.0
    
    # Stock
    assert parent.shares_owned[firm_1] == 5
    assert child.shares_owned[firm_1] == 5
    assert parent.shares_owned[firm_2] == 4  # 7 // 2 = 3, parent keeps 4
    assert child.shares_owned[firm_2] == 3
    
    # Brain
    assert len(child.decision_engine.ai_engine.q_table_manager_strategy.q_table) > 0
```

> [!CAUTION]
> **주주 명부 갱신**: `StockMarket.update_shareholder()` 호출 누락 시 주식 총량 불일치(Conservation of Mass 위배) 발생.

---

### ✅ Test Case 3: Ecosystem Stability (장기 생존 검증)

**시나리오**: 일반 조건으로 **200 Tick 이상** 장기 실행.

**기대 결과**:

1. **인구 유지**: 초반 에이전트들이 파산해도, 부유한 생존자들이 분열하여 `TARGET_POPULATION` 근처를 유지
2. **부의 축적**: 2세대, 3세대 에이전트들이 1세대보다 더 빠르게 자산을 증식 (지식 상속 효과)

**검증 방법**:
```bash
# 1. 시뮬레이션 실행
python main.py  # 200 ticks

# 2. 로그 확인
grep "MITOSIS" logs/*.log | wc -l  # 분열 이벤트 수

# 3. 분석
python scripts/analyze_history.py  # 인구 그래프 확인
```

---

## 7. 체크리스트

- [ ] `config.py`에 상수 추가
- [ ] `Household._create_new_decision_engine()` 구현
- [ ] `Household.check_mitosis()` 구현
- [ ] `AITrainingManager.inherit_brain()` 구현/수정
- [ ] `StockMarket.update_shareholder()` 구현 (if needed)
- [ ] `engine.py` run_tick에 mitosis 루프 추가
- [ ] `verify_mitosis.py` 테스트 작성 (Test Case 1, 2)
- [ ] 200틱 장기 시뮬레이션 실행 및 검증 (Test Case 3)
