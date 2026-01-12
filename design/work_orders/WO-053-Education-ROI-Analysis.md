# Work Order: WO-053 - Education ROI & Social Mobility Ladder

**Phase:** Phase 22 - The Awakening (Adaptive AI)
**Priority:** MEDIUM
**Prerequisite:** WO-052 (The Dynasty Report)

## 1. Problem Statement
WO-052 measures "Inherited Wealth" (Intergenerational Elasticity - IGE). 그러나 자본의 대물림만으로는 사회의 역동성을 온전히 설명할 수 없습니다. "교육"이라는 사다리가 실제로 계층 이동에 기여하고 있는지 정량적으로 분석해야 합니다.

**[Architectural Constraint - The Mincer Link]**
현재 시뮬레이션은 교육 지출(XP)이 생산성(Skill)으로 이어지지만, '교육 수준(Level)'이 고착화되어 있고 기업의 구인 로직이 숙련도를 충분히 반영하지 못하고 있습니다. 이를 해결하지 않으면 교육 ROI는 매몰 비용으로 처리되어 -100%가 나오게 됩니다.

**[Advanced Hypothesis: Signaling vs. Human Capital]**
현대 경제학의 **신호 이론(Signaling Theory)**에 따라, 교육이 실제 숙련도를 높이는지(인적 자본), 아니면 단지 '후광 효과(Signal)'로서 고소득 직종에 진입하는 입장권 역할만 하는지 구분하여 분석합니다.
- **Human Capital Weight**: 교육이 실제 생산량($Y$)에 기여하는 정도.
- **Signaling Weight**: 교육이 숙련도와 상관없이 임금($W$)에만 기여하는 정도.

## 2. Objective
가계의 교육 투자 지출 대비 평생 소득 상승분(ROI)을 계산하고, 교육 수준이 높을수록 부모 자산과의 상관관계(IGE)가 낮아지는지(즉, 개천에서 용이 날 수 있는지) 검증합니다.

## 3. Target Metrics
| Metric | Definition | Success Criteria |
|---|---|---|
| **Education ROI** | (자녀 근로 소득 총합 - 부모 지원금) / 누적 교육비 | NPV > 0 (투자의 합리성 확인) |
| **Mincer Coefficient** | Ln(Wage) ~ Education Years (XP) 회귀계수 | 학력이 높을수록 소득이 증가해야 함 |
| **Wage Premium** | (고졸 대비 대졸 소득 배수) / (교육비 지출 비율) | 프리미엄이 교육비용을 상회해야 함 |
| **Ladder Factor** | Low Education IGE vs. High Education IGE | High Edu IGE가 유의미하게 낮아야 함 |

## 4. Implementation Plan

### Track A: Tracker Extension (`mobility_tracker.py`)
- [ ] **Data Capture**: `MobilityRecord`에 `total_edu_spending`, `max_edu_level`, `cumulative_wage_income` 필드 추가.
- [ ] **API Update**: 
    - `register_edu_expense(agent_id, amount)`: 가계가 'education' 재화를 소비할 때마다 호출.
    - `register_wage_income(agent_id, amount)`: 틱당 지급받는 순임금을 누적.
- [ ] **ROI Logic**: 가계 사망 시 `(cumulative_wage_income) / total_edu_spending` 산출 로직 추가 (상속 자산 제외).

### Track B: Engine & Architecture Hardening (The Mincer Link)
- [ ] **Graduation Logic**: `core_agents.py`의 `_update_skill`에서 XP 임계값 도달 시 `education_level`을 자동으로 상승시키는 로직 추가.
- [ ] **Skill-Based Hiring**: `corporate_manager.py`의 `_manage_hiring`에서 기업이 구인 시 목표 노동력을 '머릿수'가 아닌 **'총 숙련도(Total Skill Units)'**로 계산하도록 수정.
- [ ] **Wage Offer**: 기업이 새로운 직원을 채용할 때 `Base_Wage * Candidate_Skill`로 임금을 제시하도록 하여, 고숙련자가 즉시 높은 임금을 받도록 보장.

### Track D: Signaling Experiment (Theory Testing)
- [ ] **Dual ROI Tracking**:
    - **Production ROI**: 교육이 실제 기업의 총 생산량($Y$) 증대에 기여한 순가치.
    - **Credential ROI**: 실제 생산량 증가 없이 '학위(Level)'만으로 얻어낸 추가 임금.
- [ ] **Sensitivity Analysis**: `EDUCATION_EFECT_ON_PRODUCTIVITY` 상수를 0~1 사이로 조절하며, '학위뿐인 사회'와 '숙련 위주 사회'의 경제 성장률 차이 비교.

### Track C: Analytics Update (`dynasty_report.py`)
- [ ] **Report Section**: `reports/dynasty_report_YYYYMMDD.md`에 "The Social Ladder: Education ROI" 섹션 추가.
- [ ] **Visualization**: 교육 수준(0~5)별 평균 소득 및 자산 상승분 히스토그램(ASCII) 추가.
- [ ] **Verdict**: 교육이 계층 이동의 사다리 역할을 하는지(Ladder working) 아니면 계급 고착의 도구인지(Glass ceiling) 판정.

## 5. Verification
- **Unit Test**: `tests/test_wo053_education_roi.py`를 생성하여 인위적인 교육 투자 시나리오에서 ROI가 모델링대로 계산되는지 확인.
- **Report Audit**: 1,000틱 시뮬레이션 결과 파일에서 교육 수준과 자산 상승률의 양(+)의 상관관계 확인.

## 6. Jules Assignment
| Track | Task | Target File |
|---|---|---|
| A | MobilityTracker 확장 및 ROI 로직 | `simulation/metrics/mobility_tracker.py` |
| B | 교육 지출 트래킹 훅 추가 | `simulation/core_agents.py` |
| C | 보고서 섹션 추가 및 판정 로직 | `scripts/experiments/dynasty_report.py` |
