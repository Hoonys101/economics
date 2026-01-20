# 📖 SIMULATION PLAYBOOK

> **Purpose**: "검증된 수치와 전술은 자산이다." 이 문서는 시뮬레이션 튜닝 과정에서 발견된 최적의 상수값, 디버깅 전술, 경제적 균형점을 기록하여 지식의 휘발을 방지합니다.

---

## 1. ⚖️ 검증된 경제적 상수 (Proven Constants)

| 변수 | 값 | 검증 단계 | 비고 |
| :--- | :--- | :--- | :--- |
| `STARTUP_COST` | 30,000 | Phase 1 Stabilization | 좀비 기업 난립 방지 최소 비용 |
| `CORPORATE_TAX_RATE` | 0.2 (20%) | Phase 1 Stabilization | 재정 건전성 유지의 마지노선 |
| `REFERENCE_GROUP_PERCENTILE` | 0.2 (Top 20%) | Phase 17-4 Vanity | 상대적 박탈감 유발 임계치 |

---

## 2. 🛡️ 디버깅 및 시뮬레이션 전술 (Tactics)

### 2.1 Money Conservation Check
- **현상**: 시스템 내 총 통화량이 갑자기 급증하거나 급감함.
- **전술**: `liquidate_assets` 로직에서 구매자 없는 자산의 통화화 여부 확인. `Double-Entry` 원칙 준수 여부 체크.

### 2.2 Rat Race Mitigation
- **현상**: 저출산으로 인한 인구 소멸.
- **전술**: `CHILDCARE_TIME_REQUIRED` 하향 조정 또는 `EDUCATION_COST_MULTIPLIERS` 완화를 통한 기대 임금 격차 해소. (Phase 19 검증 완료)

---

## 3. 🧪 실험실 환경 (Laboratory Settings)

### 3.1 The Iron Test (1000 Ticks)
- **목표**: 장기 생존성 및 인플레이션 안정성 확인.
- **기준**: 인플레이션율 < 5%, 실업률 < 10%, 정부 부채 < GDP 200%.

---

**"플레이북은 Jules의 보고서와 수석의 통찰이 만나는 지점이다."**
