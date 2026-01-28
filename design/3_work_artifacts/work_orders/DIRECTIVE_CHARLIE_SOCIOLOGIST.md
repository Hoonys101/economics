# 🎓 [Directive] Jules-Charlie: Sociologist

## 1. 🛑 Goal
교육의 수익률(ROI)을 실제 생산성 향상(Human Capital)과 학벌 효과(Signaling)로 구분하여 분석하고, 교육이 사회적 이동성에 기여하는지 판정하십시오.

## 2. 🧱 Technical Task (Zero-Question Spec)

### A. Dual ROI Definitions & Ladder Intent
- **Human_Capital_Gain (생산성 효과)**: 
    - 정의: 교육 이수 전후의 `agent.productivity_factor` 차이로 인해 발생하는 기업의 추가 수익.
    - 측정: `(Productivity_Post - Productivity_Pre) * Market_Price`.
- **Credential_Premium (신호 효과)**: 
    - 정의: 실제 생산성은 같으나, 학위(Education Level)가 높다는 이유만으로 지불받는 임금의 차액.
    - 측정: `Same_Productivity_Group` 내에서 `Degree_Holder_Wage - Non_Degree_Wage`.
- **The Social Ladder**: 이번 실험의 '사다리'는 **세대 간 이동성(Generational Mobility)**에 초점을 맞춥니다. 
    - `education_level`은 출생 시 부모의 자산에 의해 결정되는 고정값(Fixed at Birth)으로 유지하십시오. (부모가 자식의 '시작선'을 결정하는 사다리 구조 증명)

### B. Implementation: Signaling Strategy
- **Target File**: `simulation/firms.py` (또는 HR/임금 지불 로직)
- **Action**: `Firm.update_needs` (또는 실제 임금 계산부)에서 `Halo_Effect`를 적용하십시오.
    - **Logic**: `wage = base_wage * actual_skill * (1 + education_level * HALO_EFFECT)`.
    - **Config**: `config.py`에 `HALO_EFFECT = 0.15`를 추가하십시오.
    - **Note**: 이 방식은 동일 숙련도(`actual_skill`) 대비 학위(`education_level`)에 따른 '과잉 지불'을 직접 구현하여 `Credential_Premium`을 생성합니다.

### C. The Social Ladder Report
- **Target**: `scripts/experiments/education_roi_analysis.py` (신규 생성)
- **Goal**: 교육비 지불 능력이 부모의 자산에 의존할 때, 교육이 계층 고착화를 심화시키는지 분석하여 `reports/dynasty_report_v2.md`에 반영하십시오.

## 3. ✅ Verification
- **Mincer Equation**: `log(Wage) = a + b*Education + c*Experience`. 여기서 `b`(교육 수익률)를 산출하고, 이 중 `Signaling`이 차지하는 비중을 %로 리포트하십시오.
- **Reporting**: 구현 과정에서 일정이나 기술적 제약으로 타협이 필요한 로직이 발생하면, 즉시 팀장에게 보고하여 기술부채 수용 여부를 컨펌받으십시오.
