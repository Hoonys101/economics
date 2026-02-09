# Architecture: Maslow 5-Level Need Hierarchy

## 1. Vision
본 프로젝트의 핵심 철학은 **"에이전트는 하드코딩된 규칙이 아니라, 본질적인 욕구를 충족시키려는 동기에서 행동한다"**는 것입니다. 기존의 3단계 모델(금전, 신분, 학습)을 매슬로우의 5단계 욕구 위계로 확장하여, 복잡한 사회 현상(베블린재, 네트워크 효과 등)이 창발(Emergence)되도록 설계합니다.

---

## 2. The 5 Levels of Need

### 🔴 Level 1: 생리적 욕구 (Physiological Needs)
- **핵심 요소**: 식량(`FOOD`), 주거(`SHELTER`), 기본 의류.
- **경제적 발현**: 맬서스 함정. 식량 가격이 급등하거나 공급이 부족할 때 에이전트의 생존(Survival) 점수가 급격히 하락하며 아사(Starvation) 발생.
- **행동 변화**: 다른 모든 상위 욕구를 포기하고 최저가 식량 확보에 올인.

### 🟠 Level 2: 안전의 욕구 (Safety Needs)
- **핵심 요소**: 저축(`Savings`), 건강 보험, 고용 안정성, 주택 소유(`Mortgage`).
- **경제적 발현**: 저축 성향(Propensity to Save). 미래의 불확실성에 대비하여 현재 소비를 억제하고 자산을 축적.
- **행동 변화**: 고용 불안정 시 소비 위축 및 저축 증가.

### 🟡 Level 3: 소속 및 애정의 욕구 (Belonging Needs)
- **핵심 요소**: 가족 형성, 커뮤니티 가입, 브랜드 충성도, SNS/통신 네트워크.
- **경제적 발현**: **네트워크 효과 (Network Effects)**.
- **행동 변화**: 특정 네트워크(Messenger, Standard)에 소속되지 못했을 때 발생하는 **소외 비용(Alienation Cost)**이 효용을 갉아먹음. 이를 방지하기 위해 남들이 쓰는 상품을 구매(Conformity).

### 🟢 Level 4: 존경의 욕구 (Esteem Needs)
- **핵심 요소**: 사회적 지위(`social_rank`), 명성, 성취감.
- **경제적 발현**: **베블린재 (Veblen Good) & 과시 소비**.
- **행동 변화**: 단순히 비싼 물건이 아니라, 자신의 지위를 Signal(신호)할 수 있는 상품에 투자. 높은 `social_rank`는 금융 우대(대출 금리 인하)나 정치적 영향력이라는 실질적 이득으로 환산됨.

### 🔵 Level 5: 자아실현의 욕구 (Self-Actualization)
- **핵심 요소**: 기술 숙련도(`labor_skill`), 교육(`Education`), 창의적 활동.
- **경제적 발현**: 인적 자본 투자 및 기술 혁신.
- **행동 변화**: 경제적 보상뿐만 아니라 자신의 능력을 극한으로 끌어올리는 행위 자체에서 효용을 얻음.

---

## 3. Implementation Logic (NeedStructure)

### A. 하향식 제약 (Top-Down Constraints)
하위 욕구가 충족되지 않으면 상위 욕구의 가중치(`Weight`)가 0에 가깝게 수렴합니다.
$W_{L+1} = \max(0, \frac{Satisfaction_{L} - Threshold}{1 - Threshold})$

### B. 효용 발현 (Utility Emergence)
- **Veblen Consumption**: $U_{Esteem} = f(Price, Exclusivity) \times SocialRank$
- **Network Belonging**: $U_{Belonging} = BaseUtility - AlienationCost(1 - \frac{Users}{TotalAgents})$

---

## 4. Scenario Mapping
| 단계 | 시나리오 카드 | 검증 항목 |
| :--- | :--- | :--- |
| Level 1 | SC-003 | 맬서스 함정 및 식량 안보 |
| Level 3 | SC-006 | 네트워크 효과 및 소외 비용 |
| Level 4 | SC-005 | 베블린재 및 신분 경쟁 |

---

## 5. Next Steps
1. `modules/household/api.py` 내 `NeedStructure` 클래스 확장.
2. `HouseholdAI`의 `decide_consumption` 로직에 5단계 가중치 연동.
3. `SPVM_MATRIX.md`와 연계하여 단계별 실험 수행.
