# 🏗️ [Directive] Phase 22.1: The Great Acceleration & Baselines

Jules, WO-052(Social Mobility Baseline)의 성공적인 구현을 확인했습니다. 'Lively God Mode' 전략은 아주 탁월한 선택이었습니다. 이제 우리는 시뮬레이션의 **연산 효율**을 극대화하고, **기술적 베이스라인(멜서스 트랩)**과 **현대적 성장(인적 자본)** 분석으로 나아가야 합니다.

본 지침에 따라 다음 업무를 순차적으로 수행하십시오.

---

## Task 1: Engine Booster (WO-051+ Speed-Up)
시뮬레이션 1,000틱 완주 시간을 단축하기 위한 최적화를 우선 적용합니다.

1. **DB I/O Batching**: 
    - `c:\coding\economics\simulation\engine.py`의 `BATCH_SAVE_INTERVAL`을 `50`으로 상향하여 DB 플래싱 부하를 1/50로 줄이십시오.
2. **Log Suppression**: 
    - 시뮬레이션 메인 루프에서 매 틱 발생하는 `INFO` 로그를 `WARNING` 수준으로 상향하거나 노이즈가 심한 로거(`government`, `central_bank`)를 Mute 처리하십시오.
3. **Vectorization Expansion**: 
    - `VectorizedHouseholdPlanner`를 확장하여 `decide_consumption` 로직을 배치 연산으로 전환하십시오.

---

## Task 2: Pre-Modern Baseline (WO-054 Malthusian Trap)
기술 발전이 없던 시절의 '멜서스 트랩'을 먼저 증명하여 현대적 성장의 대조군을 확보합니다.

1. **Fixed Land Setup**: 기업의 `capital_stock` 투자를 차단하고 토지 성격의 고정 자본으로 취급하십시오.
2. **System 1 Breeding**: 피임을 비활성화하고 본능적 번식 모드(`TECH_CONTRACEPTION_ENABLED = False`)를 가동하십시오.
3. **Iron Ceiling Report**: 인구가 특정 지점에서 꺾이며 기아가 발생하는 '멜서스의 재앙'을 시각화하십시오.

---

## Task 3: The Social Ladder (WO-053 Education ROI)
'Lively God Mode'와 앞서 설계한 'Mincer Link'를 결합하여 교육의 실제 수익률을 분석합니다.

1. **Skill-Based Wage**: 기업이 숙련도 핵심 성과 지표(Total Skill Units)를 기반으로 임금을 제시하게 하십시오.
2. **Dual ROI Analysis**: 실제 생산성 향상(Human Capital)과 단순 학벌 효과(Signaling)를 구분하여 리포트하십시오.

---

### [Jules: Reporting Protocol]
- 모든 작업이 완료되면 `reports/dynasty_report_20260112.md`를 업데이트하여 **[정체 사회] vs [멜서스 사회] vs [인적자본 사회]**의 IGE 지표를 대조하여 리포트하십시오.
- 최적화 적용 전후의 1,000틱 완주 시간을 명시하십시오.
