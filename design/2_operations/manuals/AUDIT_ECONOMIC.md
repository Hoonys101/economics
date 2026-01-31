# 🏥 Worker Manual: Economic Integrity Audit [AUDIT-ECONOMIC]

---

## 1. 감사 목적: 선행 리팩토링 정찰 (Refactoring Reconnaissance)
본 감사의 핵심은 단순히 버그를 찾는 것이 아니라, **차기 업무 배분 전 선행 리팩토링이 필요한 지점을 선제적으로 인지하는 것**입니다. 
"이 땅에 새 건물을 지어도 되는가, 아니면 기초 공사(Refactoring)부터 다시 해야 하는가?"를 판단하여, 복잡한 금융 로직 추가 시 발생할 수 있는 '연쇄적 화폐 증발'을 예방합니다.

---

## 2. 참조 문서 (Must Read)
작업 시작 전 아래 문서를 반드시 숙지하십시오:
- **[ARCH_TRANSACTIONS.md](../../1_governance/architecture/ARCH_TRANSACTIONS.md)**: Settlement Mandate 및 Zero-sum Precision 원칙.
- **[TECH_DEBT_LEDGER.md](../ledgers/TECH_DEBT_LEDGER.md)**: 기존에 보고된 누출 관련 부채들.

---

## 3. 정찰 지표: 선행 리팩토링이 필요한 경우
아래 현상이 발견되면 즉시 "선행 리팩토링 우선 보고"를 수행하십시오.
1. **복합 트랜잭션의 부재**: 여러 단계의 이체(물품 구매 + 세금 + 수수료)가 원자적으로 묶여있지 않고 산발적인 `transfer` 호출에 의존하고 있을 때.
2. **부동 소수점 오염**: 정수(Cents) 연산으로 전환되지 않은 핵심 정산 로직이 남아 있어, 누적 오차가 예견될 때.
3. **직접 수정(Direct Mutation) 관습**: 여전히 많은 파일에서 에이전트의 자산에 직접 접근하여 수정하는 코드가 산재해 있어, 새로운 금융 규칙 적용 시 충돌이 예상될 때.

---

## 4. 정밀 타격 범위 및 검증 지점
- **대상**: `simulation/systems/transaction_processor.py`, `simulation/systems/demographic_manager.py` 등.
- **검색**: `grep -rE "\.assets\s*[+-*/]?=" simulation/`

---

## 5. 운영 및 수확 규정 (Harvest Logic)
- **업무 브랜치명**: `audit-economic-[TaskID]`
- **결과물 저장 경로**: `design/3_work_artifacts/reports/audit_economic_[TaskID].md`
- **수확 절차**: `git push` 후 Antigravity가 `harvest-go.bat`을 실행하여 브랜치 삭제 및 보고서 수집.
