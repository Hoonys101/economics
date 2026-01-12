# 🏛️ [Directive] Jules-Bravo: Archaeologist

## 1. 🛑 Goal
기술 발전이 정체된 '전근대 멜서스 트랩' 환경을 구축하고 베이스라인 데이터를 확보하십시오.

## 2. 🧱 Technical Task
1.  **Malthusian Config**:
    - `scripts/experiments/malthusian_trap_baseline.py`를 신규 생성하십시오.
    - `CAPITAL_DEPRECIATION_RATE = 0.0` (자본=토지)
    - `TECH_CONTRACEPTION_ENABLED = False` (본능적 번식)
    - `BIOLOGICAL_FERTILITY_RATE = 0.2`로 설정하십시오.
2.  **Iron Ceiling Verification**:
    - 인구가 지수적으로 증가하다가 식량 생산 한계(산술적 증가)에 부딪혀 사망률이 급증하는 구간을 포착하십시오.
3.  **Baseline Report**:
    - 인구와 실질 임금의 역상관 관계를 증명하는 리포트를 제출하십시오.

## 3. ✅ Verification
- `malthusian_trap_report.md` 생성 및 시각화 데이터 포함.
- 임금이 최저생계비(`Survival_Cost`) 밑으로 수렴하는지 확인하십시오.
