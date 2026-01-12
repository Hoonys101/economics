# ⚔️ [Multi-Agent Mission Brief] Phase 22.1: The Great Acceleration

사용자의 요청에 따라, 우리는 **3명의 Jules 요원**을 각각 다른 분대에 배치하여 병렬로 업무를 수행합니다. 각 요원은 자신의 전공 분야에 집중하며, 파일 충돌(Conflict)을 방지하기 위해 지정된 영역 내에서만 작업하십시오.

---

## 🏎️ 분대 A: Jules-Optimizer (Core Engine)
**Mission: 연산 병목 제거 및 엔진 가속화**

1. **DB I/O Batching**: `engine.py`의 `BATCH_SAVE_INTERVAL`을 `50`으로 상향.
2. **Log Suppression**: 매 틱 발생하는 `INFO` 로그를 `WARNING`으로 상향 및 무력화.
3. **Vectorization Expansion**: `VectorizedHouseholdPlanner`를 확장하여 소비 결정 배치 처리 구현.
    - **Target Files**: `simulation/engine.py`, `simulation/ai/vectorized_planner.py`, `config.py`

---

## 🏛️ 분대 B: Jules-Archaeologist (Malthusian Trap)
**Mission: 전근대 멜서스 트랩 베이스라인 구축**

1. **Fixed Land Logic**: 자본을 토지로 취급하는 고정 자본 로직 구현.
2. **System 1 Simulation**: 본능적 번식 시뮬레이션 및 '기아의 철의 천장' 증명.
3. **Malthusian Catastrophe Report**: 인구/임금 역상관 리포트 생성.
    - **Target Files**: `scripts/experiments/malthusian_trap_baseline.py` (New), `simulation/agents/government.py` (Override logic)

---

## 🎓 분대 C: Jules-Sociologist (Education ROI)
**Mission: 인적 자본 vs 후광 효과 심층 분석**

1. **Dual ROI Logic**: 생산성 기여(Human Capital)와 학벌 효과(Signaling) 구분 추적.
2. **Skill-Based Wage**: 기업의 숙련도 기반 임금 제시 로직 구현.
3. **The Social Ladder Report**: 교육이 계층 이동의 사다리인지 판정.
    - **Target Files**: `simulation/metrics/mobility_tracker.py`, `simulation/firms.py`, `scripts/experiments/dynasty_report.py`

---

### [Collab Protocol]
- **Optimizer**가 엔진 수정을 완료하면, **Archaeologist**와 **Sociologist**는 최적화된 엔진 위에서 최종 시뮬레이션을 돌려 결과를 제출하십시오.
- 각 리포트의 끝에는 자신의 작업이 전체 성능 및 지표에 기여한 바를 명시하십시오.
