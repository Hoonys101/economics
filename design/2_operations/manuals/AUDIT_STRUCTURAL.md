# 🏛️ Worker Manual: Structural & Abstraction Audit [AUDIT-STRUCTURAL]

---

## 1. 감사 목적: 선행 리팩토링 정찰 (Refactoring Reconnaissance)
본 감사의 최우선 순위는 **업무 배분 시 발생할 수 있는 구조적 병목(Bottleneck)을 선제적으로 차단하는 것**입니다. 
클래스가 이미 포화 상태(God Class)라면 기능을 추가하기 전 반드시 '해체(Decomposition)' 미션을 선행 배치해야 함을 결정권자에게 보고합니다.

---

## 2. 참조 문서 (Must Read)
작업 시작 전 아래 문서를 반드시 숙지하십시오:
- **[ARCH_AGENTS.md](../../1_governance/architecture/ARCH_AGENTS.md)**: Purity Gate 및 Facade-Component 패턴.
- **[ARCH_SEQUENCING.md](../../1_governance/architecture/ARCH_SEQUENCING.md)**: Decisions -> Matching -> Transactions -> Lifecycle 표준 시퀀스.

---

## 3. 정찰 지표: 선행 리팩토링이 필요한 경우
아래 현상이 발견되면 즉시 "선행 리팩토링 우선 보고"를 수행하십시오.
1. **임계치 초과(Saturation)**: 핵심 클래스(Household, Firm 등)가 800라인을 초과하여 새로운 논리를 넣을 자리가 물리적으로 부족할 때.
2. **참조 엉킴(Dependency Hell)**: 추상화 누출로 인해 한 곳을 고치면 전혀 다른 도메인의 텍스트가 깨지는 '강한 결합'이 발견될 때.
3. **시퀀스 예외 처리 남발**: 표준 파이프라인(`tick_orchestrator.py`)을 우회하는 편법적인 호출이 많아, 새로운 페이즈 추가 시 예측 불가능한 결과가 우려될 때.

---

## 4. 정밀 타격 범위 및 검증 지점
- **대상**: `simulation/core_agents.py`, `simulation/orchestration/tick_orchestrator.py` 등.
- **검색**: `make_decision(self)` 등 Raw Agent 유입 탐지.

---

## 5. 운영 및 수확 규정 (Harvest Logic)
- **업무 브랜치명**: `audit-structural-[TaskID]`
- **결과물 저장 경로**: `design/3_work_artifacts/reports/audit_structural_[TaskID].md`
- **수확 절차**: `git push` 후 Antigravity가 `harvest-go.bat`을 실행하여 브랜치 삭제 및 보고서 수집.
