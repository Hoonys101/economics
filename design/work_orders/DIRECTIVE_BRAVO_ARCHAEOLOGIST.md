# 🏛️ [Directive] Jules-Bravo: Archaeologist

## 1. 🛑 Goal
기술 발전이 정체된 '전근대 멜서스 트랩'을 시뮬레이션으로 구현하고, 인구 증가가 생존 임계점에 부딪히는 '철의 천장' 데이터를 확보하십시오.

## 2. 🧱 Technical Task (Zero-Question Spec)

### A. Experiment Script: `c:\coding\economics\scripts\experiments\malthusian_trap_baseline.py`
이 파일은 단순 Config 모음이 아니라, 시뮬레이션을 제어하고 데이터를 수집하는 **실행 스크립트**입니다.
- **Overrides**:
    - `CAPITAL_DEPRECIATION_RATE = 0.0` (자본의 소멸을 막아 토지와 같은 고정 자산으로 취급)
    - `INITIAL_FIRM_CAPITAL_MEAN = 50.0` (확장 불가능한 고정 자본량 설정)
    - `FIRM_PRODUCTIVITY_FACTOR = 1.0` (기술 정체 고정)
- **Breeding Logic**:
    - `agent.decision_engine.reproduction_mode = 'SYSTEM1'` (본능 모드 강제)
    - `BIOLOGICAL_FERTILITY_RATE = 0.2` (인구의 기하급수적 증가 유도)

### B. Iron Ceiling Verification (The Capture)
- **Mechanism**: 임금이 최저생계비(`Survival_Cost`) 미만으로 떨어지는 순간의 `Agent Death Rate`를 트래킹하십시오.
- **Implementation**: 
    1. 매 틱 `mean_wage`와 `survival_cost`를 비교.
    2. `wage < survival_cost` 구간에서 발생하는 아사자(Starvation) 수 기록.
    3. `Population` 그래프가 특정 상한선(`Iron Ceiling`)에서 진동하거나 급락(Catastrophe)하는 지점을 리포트에 명시.

## 3. ✅ Verification
- `c:\coding\economics\reports\malthusian_trap_report.md` 생성.
- **Metric**: "인구가 2배 늘어날 때 실질 임금이 몇 % 하락하는가?" (역상관 계수)를 산출하여 리포트하십시오.
