# WO-016: 금본위 모드 (Full Reserve Banking) 구현

## 1. 개요
**목표**: 은행의 신용 창출을 제거하고, 정부만 화폐를 발행/소각할 수 있도록 시스템 변경.

**핵심 원칙**: 
- `Money_Total = Initial_Money + Σ(Govt_Spending - Govt_Tax)`
- 은행은 단순 중개자 (지급준비율 100%)

## 2. 구현 상세

### 2.1 config.py
```python
# 금본위 모드 설정
GOLD_STANDARD_MODE = True  # True: 금본위, False: 현대 금융
INITIAL_MONEY_SUPPLY = 100_000.0  # 초기 화폐 총량
```

### 2.2 simulation/bank.py
**대출 함수 수정**:
```python
def issue_loan(self, borrower, amount, ...):
    if getattr(config, 'GOLD_STANDARD_MODE', False):
        # 금본위: reserves에서만 대출
        if self.reserves >= amount:
            self.reserves -= amount
            borrower.assets += amount
            # 화폐 총량 불변
        else:
            self.logger.warning(f"LOAN_REJECTED | Insufficient reserves. Requested: {amount}, Available: {self.reserves}")
            return False
    else:
        # 현대 금융: 신용 창출 (기존 로직 유지)
        borrower.assets += amount
        borrower.debt += amount
```

### 2.3 simulation/agents/government.py
**화폐 발행/소각 추적 로직 추가**:
```python
class Government:
    def __init__(self, ...):
        self.total_money_issued = 0.0  # 누적 발행량
        self.total_money_destroyed = 0.0  # 누적 소각량 (세금)
    
    def provide_subsidy(self, amount, ...):
        # 기존 로직 + 추적
        self.total_money_issued += amount
    
    def collect_tax(self, amount, ...):
        # 기존 로직 + 추적
        self.total_money_destroyed += amount
    
    def get_net_money_supply_change(self):
        return self.total_money_issued - self.total_money_destroyed
```

## 3. 검증 계획

### 3.1 화폐 총량 보존 테스트
```python
# 매 틱 종료 시 검증
total_household_assets = sum(h.assets for h in households)
total_firm_assets = sum(f.assets for f in firms)
total_bank_assets = bank.reserves + bank.loans_outstanding
total_gov_assets = government.assets

calculated_total = total_household + total_firm + total_bank + total_gov
expected_total = INITIAL_MONEY_SUPPLY + government.get_net_money_supply_change()

assert abs(calculated_total - expected_total) < 0.01, "Money leak detected!"
```

### 3.2 Iron Test 수정
- `iron_test.py`에 화폐 총량 로깅 추가
- 50틱 테스트로 보존 법칙 검증

## 4. 인사이트 보고 요청
구현 완료 후 다음 사항을 `reports/GOLD_STANDARD_REPORT.md`에 기록:
1. 금본위 모드에서 대출 거절 빈도
2. 화폐 순환 속도 변화
3. 가격 안정성 비교 (현대 금융 vs 금본위)

## 5. 참고 문서
- Phase 8-B: Reflux System Spec
- `design/ECONOMIC_INSIGHTS.md`
