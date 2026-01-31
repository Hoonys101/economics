# 📜 Work Order: (Operation Laissez-Faire)

**수신**: Manager AI (Jules)
**참조**: All Modules
**목표**: "잉여 생산물에 의한 자본 축적과 자생적 시장 분화 가능성 검증"

## 1. 환경 설정 (Configuration)
"정부의 개입을 0으로, 민간의 효율을 2배로."

- **세금 폐지**:
 - `INCOME_TAX_RATE = 0.0`
 - `CORPORATE_TAX_RATE = 0.0`
 - `SALES_TAX_RATE = 0.0`
- **생산성 혁명**:
 - `FIRM_PRODUCTIVITY_FACTOR = 20.0` (기존 10.0 대비 2배)
- **규제 완화 (유지비 조정)**:
 - `FIRM_MAINTENANCE_FEE = 50.0` (기존 200.0 대비 1/4 축소, 현재 0.1에서 상향 조정하여 '적정 마찰력' 테스트)
- **초기 재고 제거 (Empty Warehouse 유지)**:
 - `INITIAL_FIRM_INVENTORY_MEAN = 0.0`
 - `HOUSEHOLD_MIN_FOOD_INVENTORY = 0.0`

## 2. 검증 시나리오 (Hypothesis Verification)
- **Step 1**: 초기 100틱 동안 기업들이 막대한 이익(Surplus)을 남기는지 확인.
- **Step 2**: 가계의 저축액(Savings)이 급증하여, 생존 비축량을 넘어서는지 확인.
- **Step 3 (핵심)**: "시장 진입(Startup)"의 패턴 변화. 신규 도전자들이 어떤 가격 전략으로 시장에 진입하는가?

## 3. 제출물 (Deliverables)
- `reports/LAISSEZ_FAIRE_REPORT.md`: 1000틱 완주 여부 및 최종 가계/기업 생존율.
- `reports/figures/surplus_accumulation.png`: 잉여 자본 축적 그래프.

---
**의도**: 잉여 생산물(Surplus)이 발생했을 때 경제가 단순 생존을 넘어 '축적'과 '성장'의 단계로 진입하는지 확인한다.
