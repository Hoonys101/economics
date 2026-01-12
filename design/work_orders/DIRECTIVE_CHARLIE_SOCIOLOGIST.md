# 🎓 [Directive] Jules-Charlie: Sociologist

## 1. 🛑 Goal
교육의 수익률(ROI)을 실제 생산성 향상(Human Capital)과 학벌 효과(Signaling)로 구분하여 분석하고, 교육이 사회적 이동성에 기여하는지 판정하십시오.

## 2. 🧱 Technical Task (Zero-Question Spec)

### A. Dual ROI Definitions
- **Human_Capital_Gain (생산성 효과)**: 
    - 정의: 교육 이수 전후의 `agent.productivity_factor` 차이로 인해 발생하는 기업의 추가 수익.
    - 측정: `(Productivity_Post - Productivity_Pre) * Market_Price`.
- **Credential_Premium (신호 효과)**: 
    - 정의: 실제 생산성은 같으나, 학위(Education Level)가 높다는 이유만으로 지불받는 임금의 차액.
    - 측정: `Same_Productivity_Group` 내에서 `Degree_Holder_Wage - Non_Degree_Wage`.

### B. Implementation: Signaling Strategy
- **Target File**: `simulation/firms.py` (또는 HR 로직)
- **Action**: 기업의 채용 알고리즘에 `Halo_Effect` 변수(Config)를 도입하십시오.
    - **Logic**: `Expected_Productivity = Real_Productivity * (1 + Education_Level * Halo_Effect)`.
    - `Halo_Effect > 0`일 때, 기업은 실제 실력보다 학위를 더 신뢰하여 과잉 임금을 지불하게 됩니다.

### C. The Social Ladder Report
- **Goal**: 교육비 지불 능력이 부모의 자산에 의존할 때(Path Dependency), 교육이 계층 고착화를 심화시키는지(`Negative ROI` for poor) 분석하십시오.

## 3. ✅ Verification
- `reports/dynasty_report_v2.md` 업데이트.
- **Mincer Equation**: `log(Wage) = a + b*Education + c*Experience`. 여기서 `b`(교육 수익률)를 산출하고, 이 중 `Signaling`이 차지하는 비중을 %로 리포트하십시오.
