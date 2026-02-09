# 🧪 Social Phenomena Verification Matrix (SPVM)
**Version**: 1.1 (Philosophy: Maslow's 5-Level Integration)
**Goal**: 역사적 경제 변화 요인 검증을 위한 시뮬레이션 능력 분류

---

## 🟢 Tier 1: 즉시 검증 가능 (Ready to Run)

| 현상 | 메커니즘 (코드 위치) | 시나리오 세팅 |
| :--- | :--- | :--- |
| **📉 뱅크런** | `Bank.trust`, `SettlementSystem` | 지급준비율 5% + 대형 대출 강제 부도 |
| **🫧 자산 버블 & 붕괴** | `HousingSystem`, `LoanMarket` | LTV 90% + 저금리 → 금리 급등 |
| **🧺 기본 생존 (Physiological)** | `survival_need`, `FOOD` market | 식량 부족 시 아사 및 사회 불안 발생 |
| **👩‍💼 여성 사회참여** | `decide_time_allocation` | 분유(Technology)에 의한 생물학적 제약 해소 |
| **💎 베블린재 (Esteem)** | `social_rank` 기반 존경 욕구 충족 | 가격 상승 시 신분 상승 욕구 자극 |
| **📉 출산율 감소** | `decide_reproduction` | 양육비/기회비용 대비 차사멸(NPV) |

---

## 🟡 Tier 2: 로직 튜닝 필요 (Logic Tuning Required)

| 현상 | 필요 작업 | 난이도 |
| :--- | :--- | :--- |
| **💀 멜서스 함정** | `ProductionEngine`에 고정 토지(Land) 요소 도입 | 중 |
| **🍞 기펜재** | 열등재/우등재 교차 탄력성 수식 정교화 | 중 |
| **🦌 스태그플레이션** | 외부 원자재 가격 충격 주입 이벤트 시스템 | 하 |
| **🤝 소속감 (Belonging)** | 네트워크 효과와 연동된 소외 비용 모델 구현 | 중 |

---

## 🔴 Tier 3: 아키텍처 확장 필요 (Architecture Required)

| 현상 | 결핍 요소 | 확장 방안 |
| :--- | :--- | :--- |
| **🌐 네트워크 효과** | 소속(Belonging) 욕구와 사용자 수의 상관관계 | `Connectivity_Utility` 및 `Alienation_Penalty` |
| **🧠 매슬로우 5단계 개편** | 3단계(Wealth, Rank, Skill) → 5단계 완전체 | `NeedStructure` 클래스 전면 개편 |
| **🌟 자아실현 (Self-Actualization)** | 경제적 동기가 아닌 창의/예술/사회기여 동기 | `Intrinsic_Reward` 엔진 도입 |

---

## 🏗️ Scenario Runner 기획 (Updated)

1. **지수적 발현(Emergence)**: 효용 함수를 강제로 주입하되, 각 단계의 **본질적인 욕구**가 결핍되었을 때 발생하는 '비용(Cost)'에서 행동이 유발되도록 설계.
2. **신분과 이득의 결합**: `social_rank`(존경의 욕구)는 단순 숫자가 아닌, 사회적 자본(신용도, 정보 접근)으로의 전환을 목표로 함.
