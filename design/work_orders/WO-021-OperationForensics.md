# WO-021: Operation "Forensics" - 사망 원인 정밀 분석

## 1. Background
Operation Darwin (WO-020) 결과, **GDP=0**으로 경제가 정지했습니다.
파라미터 튜닝(초기 자금 증가 등)은 **"부자 아빠 효과"**일 뿐, 근본 해결이 아닙니다.

**목표**: "왜" 에이전트가 죽었는지 **법의학적 부검(Autopsy)**을 수행합니다.

---

## 2. 사망 유형 분류 (3 Types)

### Type A: 일자리가 없어서 죽음 (구조적 실업)
- **상황**: 가계가 일하고 싶어 함(Labor Offer > 0). 그러나 기업이 채용 안 함.
- **원인**: 기업 생태계 붕괴 or 기업에 임금 지불 능력 없음.
- **판독**: `Unemployment Rate 100%` + `Job Vacancy = 0`

### Type B: 일을 안 해서 죽음 (자발적 실업 / 매칭 실패)
- **상황**: 기업은 사람을 구함(Job Vacancy > 0). 그러나 가계가 지원 안 함.
- **원인**: 임금 불일치(Wage < Reservation Wage) or Q-Learning 실패.
- **판독**: 구직 시도(Labor Offer) 횟수 = 0 in 사망 직전 10틱

### Type C: 먹지 않아서 죽음 (구매력 부족 / AI 오류)
- **상황**: 시장에 빵 있음(Inventory > 0). 가계도 돈 있음(Cash > Price). 근데 안 먹음.
- **원인**: Q-Learning 실패 ("돈 쓰면 배고픔 줄어듦" 학습 실패)
- **판독**: `Cash at Death > Market Price` 인데도 사망

---

## 3. Task for Jules

### Task 1: 로그 강화 (Enhanced Death Logging)
**File**: `simulation/core_agents.py` (Household 클래스)

에이전트가 `die()` 또는 `is_active = False` 상태가 될 때, 다음 정보를 **반드시** 로그에 기록:

```python
logger.warning(
    f"AGENT_DEATH | ID: {self.id}",
    extra={
        "tick": current_tick,
        "agent_id": self.id,
        "cause": "starvation",  # or "bankruptcy" for firms
        "cash_at_death": self.assets,
        "food_inventory": self.inventory.get("basic_food", 0),
        "market_food_price": market_data.get("basic_food_price", None),
        "last_labor_offer_tick": self.last_labor_offer_tick,  # 새 속성 추가 필요
        "job_vacancies_available": market_data.get("job_vacancies", 0),
        "tags": ["death", "autopsy"]
    }
)
```

### Task 2: 사망자 추적 속성 추가
**File**: `simulation/core_agents.py`

Household에 다음 속성 추가:
- `self.last_labor_offer_tick = 0`: 마지막으로 Labor Sell Order를 낸 틱
- Labor Offer 생성 시마다 이 값을 `current_tick`으로 갱신

### Task 3: 분석 리포트 생성
**File**: `scripts/operation_forensics.py` (New)

100틱 시뮬레이션 후, 사망한 에이전트들을 전수 조사하여 리포트 생성:

```
=== FORENSIC REPORT ===
Total Deaths: 15
- Type A (No Jobs): 8 (53%)
- Type B (Won't Work): 3 (20%)
- Type C (Won't Eat): 4 (27%)

Sample Cases:
[Type A] Agent #5: Cash=0, Last Labor Offer=Tick 12, Job Vacancies at Death=0
[Type C] Agent #9: Cash=50, Food Price=10, Food Inventory=0 (HAD MONEY, DIDN'T BUY)
```

---

## 4. Verification
- [ ] 100틱 시뮬레이션 실행
- [ ] 사망 로그에 필요한 모든 필드가 포함되는지 확인
- [ ] `reports/forensic_report.txt` 생성 확인
- [ ] Type A/B/C 분류 비율 보고

## 5. Success Criteria
**"왜 죽었는지"에 대한 정량적 답변을 제공할 것.**
- Type A 비율이 높으면 → 기업 생태계 문제
- Type B 비율이 높으면 → 노동 시장 매칭 문제
- Type C 비율이 높으면 → AI 의사결정 버그
