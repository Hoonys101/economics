# Clarification Request: WO-054 Public Education System Details

**To:** Architect Prime (User)
**From:** Antigravity (Second Architect / Team Leader)
**Date:** 2026-01-12
**Subject:** Request for Detailed Technical Specification for WO-054

수석 아키텍트님, **WO-054: Public Education System**의 기본 기획안은 완벽하게 이해했습니다. Jules가 추가 질문 없이 즉시 코딩에 착수할 수 있도록(Zero-Question Test), 몇 가지 세부 로직에 대한 수석님의 가이드라인을 구체적으로 요청드리고자 합니다.

### 1. `Government.run_public_education()` 실행 시점
* **질문:** 공교육 집행은 시뮬레이션 틱의 어느 시점에 발생하는 것이 가장 적절할까요?
    * **옵션 A (Pre-Consumption):** 가계가 소비를 결정하기 전에 교육을 시켜서, 당장 다음 틱부터 지출 부담을 줄여주는 방식.
    * **옵션 B (Post-Transaction):** 모든 경제 활동이 끝나고 남은 예산으로 집행하는 방식.
    * **Antigravity 추천:** **옵션 A** (인적 자본 형성이 가계 경제의 기반이 되므로).

### 2. 장학금 대상자 선별 (`_is_scholarship_eligible`) 로직 구체화
* **질문:** "하위 20% 자산 + 높은 잠재력"을 판별할 때, 구체적인 기준이 필요합니다.
    * **자산 기준:** 현재 틱의 가계 전체 자산 순위(Percentile)를 매 틱 계산해야 할까요? 아니면 특정 주기로 업데이트할까요?
    * **잠재력 기준:** `Household.talent.potential` (가정) 값이 특정 임계치(예: 0.7)를 넘어야 하나요?
    * **Antigravity 추천:** 성능을 위해 **10틱마다 자산 순위를 계산**하고, 잠재력은 에이전트 생성 시 부여된 고정된 **Hidden Stat**을 활용.

### 3. 기술 확산 공식 (`effective_diffusion_rate`)의 상한선
* **질문:** 인적 자본에 의한 가속 효과에 상한(Cap)이 있어야 할까요?
    * 아니면 무제한으로 빨라질 수 있게 설계할까요?
    * **Antigravity 추천:** 확산 속도가 너무 빠르면 시장 충격이 클 수 있으므로, **Base Rate의 최대 2배** 수준으로 제한.

### 4. 시각화 및 지표 (UI/Dashboard)
* **질문:** `SocietyTab`이나 `GovernmentTab`에 추가로 노출해야 할 핵심 지표가 있을까요?
    * 예: "공교육 수혜자 수", "학력별 인구 분포", "재정 대비 교육비 비중" 등.

---
수석님의 지침이 하달되는 대로 즉시 상세 설계서(`*_spec.md`)를 완성하여 Jules에게 하달하겠습니다.

**Waiting for instructions...**
