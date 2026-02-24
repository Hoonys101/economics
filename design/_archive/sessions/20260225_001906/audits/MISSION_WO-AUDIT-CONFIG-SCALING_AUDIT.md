# Audit Report: Hardcoded Constants for 100M Economy (WO-AUDIT-CONFIG-SCALING)

## Executive Summary
This audit confirms that while `INITIAL_MONEY_SUPPLY` has been scaled to 100M pennies, several critical thresholds in `defaults.py` and logic engines remain tuned for a 10M-15M economy or exhibit "Penny/Unit" dimensional mismatch. Specifically, household initial assets and startup costs are too high relative to the total supply, risking immediate liquidity traps or "Zero-Sum" violations at initialization.

## Detailed Analysis

### 1. `config/defaults.py` 전수조사 (Constants Audit)
The following constants were evaluated against a **100M Penny (1,000,000 Unit)** total money supply.

| 상수명 | 현재값 (Pennies) | 권장값 | 변경 사유 |
| :--- | :--- | :--- | :--- |
| `INITIAL_MONEY_SUPPLY` | 100,000,000 | 100,000,000 | 기준값 (100M Pennies) |
| `INITIAL_HOUSEHOLD_ASSETS_MEAN` | 1,000,000 | 200,000 | 50가구 기준 50M 소모. 공급량의 50%를 가계가 점유하여 기업 운영 자금 부족 초래. |
| `INITIAL_FIRM_CAPITAL_MEAN` | 10,000,000 | 5,000,000 | 10개 기업 기준 100M 소모. 가계 자산 합산 시 150M으로 초기 공급량(100M) 초과. |
| `STARTUP_COST` | 3,000,000 | 1,000,000 | 초기 가계 자산(1M) 대비 너무 높음. 창업 자체가 불가능한 진입 장벽 형성. |
| `WEALTH_TAX_THRESHOLD` | 50,000,000 | 10,000,000 | 전체 통화량의 50%를 보유해야 과세. 현실성 없는 높은 문턱. |
| `INFRASTRUCTURE_INVESTMENT_COST` | 500,000 | 2,000,000 | 정부 예산 대비 과소 책정. 인프라 구축이 너무 쉬움. |
| `FIRM_MAINTENANCE_FEE` | 5,000 | 10,000 | 기업 자본금(10M) 대비 유지비가 너무 낮아 좀비 기업 퇴출 지연. |
| `HOMELESS_PENALTY_PER_TICK` | 5,000 | 1,000 | 초기 생존 비용 대비 페널티가 과도하여 빈곤층 즉사 위험. |

### 2. 하드코딩 검출 (Hardcoded Logic Analysis)

#### **A. `modules/government/engines/fiscal_engine.py`**
- **Status**: ⚠️ Partial
- **Evidence**: `L82-83` (Tax clamping: `max(0.05, min(0.6, ...))`). 
- **Notes**: 하한(5%)과 상한(60%)이 경제 규모와 관계없이 고정되어 있음. 초고인플레이션 상황에서 대응력 제한 가능성. `base_income_tax` 등을 `defaults.py`에서 참조하도록 리팩토링 필요.

#### **B. `simulation/systems/central_bank_system.py`**
- **Status**: ✅ Implemented (Scaled)
- **Evidence**: `L14-18` (`BOND_PAR_VALUE_PENNIES = 10000`).
- **Notes**: 채권 액면가가 100.00 단위(10,000 Pennies)로 설정되어 있으며, OMO 매입/매도 한도가 ±10%로 유연하게 설정됨. 100M 경제에서도 채권 단위 거래는 적정함.

#### **C. `simulation/systems/lifecycle/aging_system.py`**
- **Status**: ⚠️ Partial
- **Evidence**: `L154` (`default_price_float = ... 10.0`).
- **Notes**: 시장 가격이 없을 때 사용하는 기본 가격이 10.0(1,000 Pennies)으로 고정됨. 100M 경제에서 물가가 상승할 경우 자산 가치 저평가 위험.

## Risk Assessment
- **Initialization Deficit**: 가계와 기업의 초기 자산 합계(150M)가 발행 총량(100M)을 초과하는 설정이 발견됨. 시뮬레이션 시작 즉시 통화 부족 현상 발생 가능.
- **Dimensional Dissonance**: 일부 페널티(5000)는 Penny 단위이나, 일부 계산식은 Float(10.0)를 혼용하고 있어 스케일링 시 100배 오차 발생 위험 상존.

## Conclusion
100M 경제 규모에 맞게 `defaults.py` 내의 초기 자산 분배 비율을 조정하고, `aging_system.py` 및 `fiscal_engine.py`의 매직 넘버를 `config` 참조 방식으로 전환할 것을 권장합니다.

---

# New Insight Report Content

```markdown
# [Architectural Insights] WO-AUDIT-CONFIG-SCALING

## 1. Summary of Findings
- **Monetary Imbalance**: `INITIAL_MONEY_SUPPLY` (100M) vs Initial Agent Assets (150M) discrepancy detected.
- **Startup Barrier**: `STARTUP_COST` is 300% of average household assets, preventing natural entrepreneurship.
- **Dimensional Inconsistency**: `aging_system.py` uses hardcoded 10.0 fallback prices while others use Pennies.

## 2. Technical Debt Identified
- **Magic Number Clamping**: `fiscal_engine.py` restricts tax rates to 5%-60% via literals rather than config-driven bounds.
- **Static Maintenance Fees**: `FIRM_MAINTENANCE_FEE` does not scale with firm assets or inflation, leading to "Zombie Firm" risks in high-money environments.

## 3. Recommended Architectural Adjustments
- Implement a `MarketSafetyBuffer` where `INITIAL_MONEY_SUPPLY` is always calculated as `(SUM(Initial Assets) * 1.2)` to ensure liquidity.
- Centralize all "Default Price" fallbacks into `defaults.py` to prevent logic drift in systems.

## 4. Regression Analysis
- **Current Status**: Audited only. No code changes applied yet.
- **Predicted Impact**: Adjusting `INITIAL_FIRM_CAPITAL_MEAN` will likely cause existing tests that assume a 10M runway to fail; mocks in `tests/firm_test.py` must be updated to use relative percentages.

## 5. Test Evidence
[Verification performed via manual inspection of code paths in Context Files]
- `grep "pennies" config/defaults.py` -> Validated 100M scale.
- `grep "min(" modules/government/engines/fiscal_engine.py` -> Identified hardcoded clamps.
```