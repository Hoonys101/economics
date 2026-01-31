# Technical Debt Cleanup (Pure Refactoring)

**Date**: 2026-01-21
**Author**: Antigravity (Team Leader)
**Priority**: MEDIUM (Cleanup during Simulation Run)

---

## 🎯 Mission Objective

**목표:** Phase 23 통합 과정에서 발생한 잔여 기술부채(Code Smell & Hardcoding)를 제거하여 코드 품질을 강화합니다. 이는 로직 변경 없이 구조만 개선하는 **Pure Refactoring**입니다.

> "Clean code allows the engine to hum efficiently."

---

## 📋 작업 지시

### Task 1: [TD-077] Config 하드코딩 제거 (EconComponent)

**파일:** `modules/household/econ_component.py`

**문제:**
- `_price_history`의 `maxlen=10`이 하드코딩되어 있음.
- `market_wage_history`의 `maxlen=30`이 하드코딩되어 있음. (발견된 추가 부채)

**해결:**
1. `config.py`에 다음 상수 추가:
 ```python
 PRICE_MEMORY_LENGTH = 10
 WAGE_MEMORY_LENGTH = 30
 ```
2. `EconComponent.__init__`에서 위 Config 값을 참조하여 `deque` 초기화.
 ```python
 maxlen = getattr(config_module, 'PRICE_MEMORY_LENGTH', 10)
 ```

### Task 2: [TD-076] TFP 계산 중복 제거 (ProductionDepartment)

**파일:** `simulation/components/production_department.py`

**문제:**
- `produce` 메서드(Line 57~63)에서 `tech_multiplier` 변수가 중복 정의되고 재사용되어 혼란을 초래함.
- `tfp` 계산 흐름이 직관적이지 않음.

**해결:**
- 로직을 단순화하여 중복 변수 할당 제거.
- **AS-IS:**
 ```python
 tech_multiplier = 1.0
 tfp = self.firm.productivity_factor * tech_multiplier
 if technology_manager:
 tech_multiplier = technology_manager.get_productivity_multiplier(self.firm.id)
 tfp *= tech_multiplier
 ```
- **TO-BE (Equivalent but Cleaner):**
 ```python
 tfp = self.firm.productivity_factor
 if technology_manager:
 tfp *= technology_manager.get_productivity_multiplier(self.firm.id)
 ```

---

## 🔧 기술 참조

- `config.py`: 전역 설정 파일
- `modules/household/econ_component.py`
- `simulation/components/production_department.py`

---

## ✅ 완료 조건

1. [ ] `config.py`에 `PRICE_MEMORY_LENGTH`, `WAGE_MEMORY_LENGTH` 추가됨.
2. [ ] `EconComponent`가 하드코딩 대신 Config를 사용함.
3. [ ] `ProductionDepartment`의 `produce` 메서드가 깔끔해짐 (Logic Equivalent 유지).
4. [ ] 기존 테스트(`test_phase23_production` 등)가 여전히 통과해야 함 (Refactoring 검증).

---

**보고 종료.**
