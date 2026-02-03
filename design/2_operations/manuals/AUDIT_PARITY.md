# 🔍 Worker Manual: Product Parity Audit [AUDIT-PARITY]

---

## 1. 감사 목적: 선행 리팩토링 정찰 (Refactoring Reconnaissance)
본 감사의 핵심은 차기 고도화 작업을 배분하기 전, **기반 로직이 다음 기능을 견딜 수 있을 만큼 견고한지**를 정찰하는 것입니다. 
"부실 공사 위에 성을 쌓으려 하는가?"를 사전에 차단하며, 특히 '완료'된 기능이 다음 단계의 기술적 토대로 활용 가능한 품질인지 검증합니다.

---

## 2. 참조 문서 (Must Read)
작업 시작 전 아래 문서를 반드시 숙지하십시오:
- **[PROJECT_STATUS.md](../../../PROJECT_STATUS.md)**: 현재 완료된 것으로 주장되는 마일스톤 목록.
- **[ARCH_AGENTS.md](../../1_governance/architecture/ARCH_AGENTS.md)**: 'Born with Purpose', 'Demand Elasticity' 등 박제된 아키텍처 원칙.

---

## 3. 정찰 지표: 선행 리팩토링이 필요한 경우
아래 현상이 발견되면 즉시 "선행 리팩토링 우선 보고"를 수행하십시오.
1. **경직된 하드코딩**: 기능은 구현되었으나, 상수가 아닌 하드코딩된 로직이 많아 다음 단계의 '정책 가변성(Policy Flexibility)'을 수용할 수 없을 때.
2. **테스트 부재**: 기능은 작동하나 이를 검증하는 유닛 테스트가 없어, 고도화 작업 시 사이드 이펙트 감지가 불가능해 보일 때.
3. **아키텍처 미준수**: '완료' 상태이나 DTO 패턴이나 컴포넌트 구조를 따르지 않아, 확장 시 구조적 붕괴가 예상될 때.

---

## 4. 정밀 타격 범위 및 검증 지점
- **대상**: `PROJECT_STATUS.md` 내 완료(✅) 항목.
- **예시**: Chemical Fertilizer TFP x3.0, Newborn Needs Injection, Demand Elasticity Curve 등.

---

## 5. 운영 및 수확 규정 (Harvest Logic)
- **업무 브랜치명**: `audit-parity-[TaskID]`
- **결과물 저장 경로**: `design/3_work_artifacts/reports/audit_parity_[TaskID].md`
- **수확 절차**: `git push` 후 Antigravity가 `harvest-go.bat`을 실행하여 브랜치 삭제 및 보고서 수집.
