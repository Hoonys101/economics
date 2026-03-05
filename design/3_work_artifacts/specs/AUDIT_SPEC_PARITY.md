# AUDIT_SPEC_PARITY: Design-Implementation Parity Audit (v3.0)

**목표**: `design/`의 설계 비전과 `simulation/`의 실제 구현 사이의 '기술적 정합성' 및 '진행 지표'가 일치하는지 심층 진단한다.

**관심사 경계 (SoC Boundary)**:
> 이 감사는 오직 **"약속(Promise) vs 현실(Reality)"**만을 다룬다.
> - ✅ 명세서에 적힌 것이 코드에 구현되었는가 (정합성)
> - ✅ PROJECT_STATUS의 주장이 사실인가 (진행 지표)
> - ✅ TECH_DEBT_LEDGER의 상태 표기가 정확한가 (레저 교차검증)
> - ❌ 코드 구조가 올바른가 → `AUDIT_STRUCTURAL`
> - ❌ 테스트/검증 스크립트의 품질 → `AUDIT_TEST_HYGIENE`
> - ❌ 설정 값이 하드코딩인가 → `AUDIT_CONFIG_COMPLIANCE`

## 1. 용어 정의 (Terminology)
- **Design Drift (설계 편차)**: 최초 `Work Order`나 `Spec`에 명시된 로직과 실제 코드에 구현된 로직이 점진적으로 멀어지는 현상.
- **Ghost Implementation (유령 구현)**: `project_status.md`에는 완료로 표시되었으나, 실제 소스코드 상에는 로직이 미비하거나 Placeholder(Pass) 상태인 경우.
- **Data Contract (데이터 계약)**: 명세서에 정의된 입출력 데이터 규격(Key, Type)이 실제 DTO나 JSON Fixture와 일치하는 상태.
- **Spec Rot (명세 부패)**: 구현이 완료된 후 명세서 자체가 미갱신되어, 명세와 코드가 모두 존재하지만 서로 불일치하는 상태.

## 2. Severity Scoring Rubric

| Severity | 기준 | 예시 |
| :--- | :--- | :--- |
| **Critical** | 핵심 경제 매커니즘의 Spec-Code 불일치 | TFP 배율이 Spec에는 3.0이나 코드에 1.2 |
| **High** | 완료 상태 표기가 사실과 불일치 | PROJECT_STATUS "완료"인데 코드가 `pass` |
| **Medium** | DTO 필드 누락 또는 타입 불일치 | Spec에 `income_growth: float`인데 DTO에 없음 |
| **Low** | 문서 표기 오류 (기능에 영향 없음) | 파일 경로가 리네임 후 미갱신 |

## 3. 감사 범위 (Audit Scope)

### 3.1 메인 구조 및 모듈 현황 감사
- **Base Components**: `EconComponent`, `BioComponent`, `HRDepartment` 등.
- **감사 방법**: 각 컴포넌트의 `__init__` 필드와 명세서의 `Attributes` 섹션을 대조한다.
- **모듈 현황**: `design/structure.md`에 기술된 파일 트리와 실제 경로의 일치 여부를 전수 확인한다.

### 3.2 입출력 데이터 정합성 (I/O Data Audit)
- **State DTOs**: `HouseholdStateDTO`, `FirmStateDTO`의 필드가 명세서에 정의된 '핵심 경제 지표'를 모두 누락 없이 포함하고 있는가?
- **Decision Context**: `DecisionEngine`으로 들어가는 `context` 데이터가 AI 모델링 단계에서 논의된 입력 데이터를 모두 제공하고 있는가?
- **Golden Samples**: `tests/goldens/` 폴더의 JSON 데이터 구조가 실제 에이전트의 `get_state()` 출력 데이터와 동일한 스키마를 따르는가?

### 3.3 TECH_DEBT_LEDGER 교차검증 (NEW)
- **RESOLVED 검증**: "RESOLVED"로 표기된 부채가 실제 코드에서 해결되었는지 코드 검색으로 확인.
- **중복 항목 탐지**: 동일 ID가 레저에 여러 번 등재된 경우 보고.
- **Status Freshness**: 레저의 상태 표기와 최근 커밋 히스토리의 정합성 확인.

## 4. 논리 전개 및 방법 예시
1. **Spec Reading**: `design/specs/` 내의 특정 기술 사양서(예: Phase 23)를 로드한다.
2. **Code Grepping**: 해당 사양서의 키워드(예: `Chemical Fertilizer`, `TFP x3.0`)를 시뮬레이션 코드에서 검색한다.
3. **Discrepancy Reporting**:
   - **예시**: 문서에는 "TFP 배율은 3.0이다"라고 적혀 있으나, 코드에는 `TFP = 1.2`로 하드코딩된 경우 'Critical Parity Error'로 보고.
   - **예시**: `project_status.md`에는 "Real Estate 완료"라고 되어 있으나, 에이전트의 `housing_planner`가 `None`인 경우 보고.

## 5. Output Configuration
- **Output Location**: `reports/audit/`
- **Recommended Filename**: `AUDIT_REPORT_PARITY.md`
