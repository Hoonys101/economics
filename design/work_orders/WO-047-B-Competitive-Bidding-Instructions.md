# Jules 작업 지시서: WO-047-B Competitive Bidding

**Phase:** 21.7
**Priority:** HIGH
**Date:** 2026-01-11
**Assignee:** Jules (All 3 Workers)

---

## 1. 작업 목표

**구인난 발생 시 기업이 임금을 인상하는 로직 구현**

현재 노동자만 임금을 깎는 로직(Wage Decay)이 있고, 기업이 임금을 올리는 로직이 없음.
이를 구현하여 노동 시장의 양방향 균형을 달성.

---

## 2. 구현 파일

**`simulation/decisions/corporate_manager.py`**

---

## 3. 구현 로직

### 3.1 위치
`CorporateManager` 클래스 내에서 `offer_wage` 계산 로직 부분 (현재 line 473 근처)

### 3.2 핵심 코드

```python
def _adjust_wage_for_vacancies(self, firm, market_data: dict) -> float:
    """
    구인난 발생 시 임금 인상 로직.
    
    ⚠️ CRITICAL CONSTRAINT (Architect Prime):
    재무 건전성(Solvency)이 1.5 이상일 때만 임금 인상 허용.
    그렇지 않으면 '승자의 저주'로 파산 위험.
    """
    # 1. 재무 건전성 체크 (필수!)
    solvency = firm.assets / max(1.0, firm.total_liabilities) if hasattr(firm, 'total_liabilities') else firm.assets / max(1.0, firm.wage_bill * 10)
    
    if solvency < 1.5:
        return firm.offered_wage  # 재무 건전성 부족: 인상 불가
    
    # 2. 미충원 인원 확인
    current_employees = len([e for e in firm.employees if e.is_active]) if hasattr(firm, 'employees') else firm.labor_count
    target_employees = getattr(firm, 'target_labor', current_employees + 1)
    unfilled_vacancies = max(0, target_employees - current_employees)
    
    # 3. 임금 인상 (구인난 심각도에 비례, 최대 5%)
    if unfilled_vacancies > 0:
        adjustment_rate = min(0.05, 0.01 * unfilled_vacancies)
        new_wage = firm.offered_wage * (1.0 + adjustment_rate)
        return new_wage
    
    return firm.offered_wage
```

### 3.3 통합 방법

기존 `_calculate_offer_wage()` 또는 고용 결정 로직에서:

```python
# 기존: offer_wage = market_wage * (1.0 + adjustment)
# 변경: 구인난 반영
offer_wage = market_wage * (1.0 + adjustment)
offer_wage = self._adjust_wage_for_vacancies(firm, market_data)  # 추가
offer_wage = max(self.config_module.LABOR_MARKET_MIN_WAGE, offer_wage)
```

---

## 4. ⚠️ CRITICAL CONSTRAINTS (수석 아키텍트 지시)

1. **Solvency Check 필수**: `firm.assets / liabilities >= 1.5` 일 때만 인상
2. **인상 상한**: 최대 5%/틱 (무한 경쟁 방지)
3. **최저임금 준수**: `LABOR_MARKET_MIN_WAGE` 이상 유지

---

## 5. 테스트 케이스

```python
# tests/test_competitive_bidding.py
def test_wage_increase_on_vacancy():
    """구인난 시 임금 인상 확인"""
    firm = Firm(assets=100000, offered_wage=100)
    firm.target_labor = 10
    firm.labor_count = 5  # 5명 미충원
    
    new_wage = manager._adjust_wage_for_vacancies(firm, {})
    assert new_wage > 100  # 인상되어야 함

def test_no_increase_when_insolvent():
    """재무 불건전 시 인상 불가"""
    firm = Firm(assets=1000, total_liabilities=2000)  # Solvency < 1.5
    firm.target_labor = 10
    firm.labor_count = 5
    
    new_wage = manager._adjust_wage_for_vacancies(firm, {})
    assert new_wage == firm.offered_wage  # 인상 없어야 함
```

---

## 6. 완료 기준

- [ ] `_adjust_wage_for_vacancies()` 메서드 구현
- [ ] 기존 로직에 통합
- [ ] 단위 테스트 통과
- [ ] Mypy/Ruff 에러 없음

---

## 7. 참조 문서

- `design/work_orders/WO-045-Revision-Adaptive-Equilibrium.md`
- `config.py` (line 16-24: Phase 21.6 파라미터)
