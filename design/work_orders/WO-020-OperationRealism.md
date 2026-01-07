# WO-020: Operation "Darwin" - Survival of the Fittest

## 1. Background
1000틱 시뮬레이션 결과, 경제가 **정체(Stagnation)** 상태에 빠졌습니다.

**근본 원인**: "복지(Welfare)"라는 진통제가 **자연적 순환 메커니즘(Mitosis/Death)**을 마비시켰습니다.
- 죽어야 할 좀비(가계/기업)가 살아남아 자원을 독점.
- 쪼개져야 할 비만 세포(부자 가계)가 쪼개지지 않아 돈이 한 곳에 정체.

**설계 철학 복원**: "인위적 평등"이 아니라 **"생물학적 분산(Mitosis)"**이 자본 독점을 막는 자연법칙이다.

---

## 2. Objectives (3가지만)

### ✅ Task 1: Fix Leak (Money Integrity)
**File**: `simulation/agents/government.py`

**변경 사항**:
- `provide_subsidy()`, `invest_infrastructure()` 등 모든 지출 메서드에:
  ```python
  if self.assets < amount:
      logger.warning(f"SPENDING_REJECTED | Insufficient funds: {self.assets:.2f} < {amount:.2f}")
      return 0.0  # Hard Stop - 허공에서 돈 창조 금지
  ```
- **Success Criteria**: `Engine Delta = 0.0000` (단 1원의 오차도 허용 안 함)

---

### ✅ Task 2: Stop Feeding (No Welfare)
**File**: `config.py`

**변경 사항**:
```python
# 기존
UNEMPLOYMENT_BENEFIT_RATIO = 0.8  # 실업급여 = 생존비용의 80%

# 수정
UNEMPLOYMENT_BENEFIT_RATIO = 0.0  # 실업급여 = 0 (일하지 않으면 굶는다)
```
- 정부는 국방/치안(시스템 유지) 외에는 돈을 쓰지 않는다.
- **Philosophy**: "No Free Lunch. Work or Die."

---

### ✅ Task 3: Verify Mitosis & Death Mechanics
**Files**: `simulation/core_agents.py`, `simulation/engine.py`

**검증 항목**:
1. **Mitosis (세포 분열)**:
   - `MITOSIS_THRESHOLD`를 초과한 가계가 실제로 분열하는지 로그 확인.
   - 분열 시 자산이 정확히 반으로 나뉘는지 확인.
2. **Death (기아사)**:
   - `assets == 0 AND inventory["basic_food"] == 0` 상태가 N틱 지속되면 사망하는지 확인.
   - 사망 시 자산이 상속 또는 정부 귀속되는지 확인 (Escheat).
3. **Liquidation (기업 청산)**:
   - 파산 기업의 자산이 주주(가계)에게 정확히 돌아가는지 확인.

---

## 3. Verification
- [ ] 100틱 Short Test: `Engine Delta = 0.0000` 확인.
- [ ] 1000틱 Full Test 실행.
- [ ] **GDP > 0** at Tick 1000 (경제가 죽지 않음).
- [ ] **Survival Rate < 100%** (자연 도태 발생).
- [ ] **Mitosis Count > 0** (부자 가계 분열 발생).

## 4. Expected Outcome
- 복지가 사라지면 **약자는 죽고, 강자는 살아남아 분열**합니다.
- 이 과정에서 자산이 강제로 재분배되며, **돈맥경화**가 해소됩니다.
- 경제는 "정지" 대신 **"변동성 있는 균형"** 상태를 유지합니다.
