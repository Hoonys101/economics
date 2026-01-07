# 📜 Work Order: WO-023 (Industry Differentiation & Entrepreneurship)

**수신**: Manager AI (Jules)  
**참조**: All Modules  
**목표**: "산업 분화 및 기업가 정신(Visionary) 구현을 통한 경제 고도화"

## 1. 배경 (The Problem)
- **현재 상황**: 단일 산업(Food) 경제. 기술 발전으로 잉여 생산물이 넘쳐나면 가격 폭락과 고용 중단으로 심정지 발생.
- **해결책**: 남아도는 빵을 먹고 배가 부른 사람들이 찾을 **'제2의 욕구(Consumer Goods)'**를 만들고, 자본과 노동을 그쪽으로 이동시켜야 함.

## 2. 구현 명세 (Technical Specifications)

### A. 욕구의 위계화 (Needs Hierarchy)
- **위치**: `simulation/core_agents.py` (Household)
- **Logic**: [Maslow’s Hierarchy]
  1.  **1순위 (생존)**: Food (매일 1.0 unit 필수, 기존 동일).
  2.  **2순위 (삶의 질)**: Consumer_Goods (공산품/옷/가전).
      - **조건**: Food 재고가 안전 수준(3일 치 이상) 확보되었고, 잉여 현금(Cash)이 존재할 때만 구매 시도.
- **Effect**: 잉여 생산물이 생겨야만 활성화되는 '선진국형 시장' 형성.

### B. 산업의 분화 (Sector Implementation)
- **위치**: `simulation/market.py` 및 `firms.py`
- **Industry Types**:
  - `FOOD`: 필수재. 가격 비탄력적(생존 필수). 기술 장벽 낮음.
  - `GOODS`: 사치재. 가격 탄력적(비싸면 안 삼). 마진율 높음.
- **구현**: `GenericFirm` 클래스에 `sector` 속성 추가 및 `produce` 메소드 내 로직 분기.

### C. 야생의 본능: 기업가 정신 (The Visionary Logic)
- **위치**: `simulation/engine.py` 또는 `ActionProposalEngine` 창업 로직
- **Logic**: [Blue Ocean Strategy]
  - 기존의 "평균 수익률 추종(Copycat)" 방식에서 탈피.
  - 창업 시도 시 확률적(Mutation Rate 5%)으로 **'비전가(Visionary)'** 성향 에이전트 등장.
  - **Visionary Behavior**:
    - "경쟁자가 없는 시장(Zero Competitors)"을 우선적으로 선택.
    - 초기 적자(Death Valley)를 감수하고 진입.

## 3. 검증 시나리오 (Expected Behavior)
WO-022(배당)가 적용된 상태에서 본 기능 투입 시:
1.  **Phase 1 (농업 시대)**: 모두가 식량 생산에 매달림. Goods 시장 0.
2.  **Phase 2 (잉여 축적)**: 생산성 향상 -> 식량 가격 폭락 -> 가계 실질 소득 증가.
3.  **Phase 3 (산업 혁명)**: '비전가'가 Goods 공장 설립. 실직 농부들이 공장 노동자로 전환.
4.  **Phase 4 (고도화)**: 식량 가격 안정화 + Goods 시장 폭발적 성장 -> GDP 퀀텀 점프.

## 4. 제언 (Execution Strategy)
본 WO-023은 **WO-022(주주 배당)** 시스템이 안정적으로 정착되어 가계/기업의 현금 흐름이 원활해진 후(Serial Execution) 투입해야 효과를 명확히 검증할 수 있습니다.
