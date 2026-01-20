# Gemini 프로젝트 지침 (Project Guide)

이 파일은 프로젝트의 핵심 설계 문서와 개발 지침을 안내하는 중앙 허브입니다.
새로운 개발을 시작하거나 기존 코드를 수정할 때, 아래 표를 참조하여 관련된 문서를 먼저 '임포트'(읽고 숙지)하여 프로젝트의 전체적인 아키텍처와 일관성을 유지해야 합니다.

---

## 1. 설계 문서 '임포트' 목록 (Design Document 'Import' List)

| 파일 경로 (File Path) | 주요 내용 (Purpose / Description) | 관련 개념 (Keywords) |
| :--- | :--- | :--- |
| `design/SYSTEM_DESIGN.md` | 프로젝트의 통합 시스템 설계 문서. 아키텍처, 데이터 흐름, 에이전트 모델, 시장 메커니즘 등 핵심 설계 내용을 담고 있습니다. | `아키텍처`, `데이터베이스`, `MVC`, `AI 모델`, `에이전트 설계`, `시장` |
| `design/project_management/PROJECT_STATUS.md` | 프로젝트의 현재 진행 상황, 다음 단계, 주요 이슈를 종합적으로 관리하는 상태 보고서입니다. | `프로젝트 관리`, `진행 상황`, `실행 계획`, `로드맵` |
| `design/개발지침.md` | 프로젝트의 전반적인 개발 규칙, 코딩 스타일, 사용할 도구(Git, Pytest) 등에 대한 지침입니다. | `PEP 8`, `Git`, `Pytest`, `코딩 스타일`, `개발 환경` |

---

## 3. 현재 상태 (2025년 11월 3일)

*   **자세한 프로젝트 상태:** `design/project_management/PROJECT_STATUS.md` 파일을 참조하십시오.

## 4. 디버깅 지침

디버깅 중 '어려움이 발생한 상황'으로 판단하고, 작업을 멈춘 뒤 설명을 요청할 기준은 다음과 같습니다.

1.  **반복적인 실패**: 동일한 버그에 대해 2~3번 이상 시도했음에도 해결되지 않고 같은 오류가 계속 발생할 때.
2.  **예상치 못한 부작용**: 하나의 버그를 수정했을 때, 관련 없어 보이는 다른 부분에서 새로운 버그가 연쇄적으로 발생할 때.
3.  **모호한 오류**: 에러 메시지가 명확하지 않거나, 문제의 근본 원인을 파악하기 어려운 코드를 가리킬 때.
4.  **광범위한 수정 필요**: 간단한 버그 수정인 줄 알았으나, 해결을 위해 핵심 로직이나 여러 모듈의 구조를 변경해야 할 것으로 판단될 때.
5.  **재현 불가능**: 버그가 일관되게 재현되지 않아 원인 추적이 어려울 때.

## 5. 문제 해결 프로토콜 (Problem Solving Protocol)

문제가 발생했을 때, 다음의 체계적인 절차를 따라 문제를 해결하고 문서화합니다.

**1. 문제 인식 및 정의 (Problem Recognition & Definition)**
    - **현상 기술:** 예상된 결과와 실제 발생한 현상을 명확히 구분하여 기술합니다.
    - **재현 경로 확인:** 어떤 조건과 순서로 문제를 재현할 수 있는지 확인합니다.
    - **최근 변경 사항 확인:** `git log`, `git status` 등을 통해 문제 발생 시점 전후의 코드 변경 사항을 파악합니다.

**2. 초기 조사 및 정보 수집 (Initial Investigation & Information Gathering)**
    - **로그 분석:** `app.log` 등 관련 로그 파일을 `read_file`을 사용하여 분석하고, 에러 메시지나 예외 발생 지점을 찾습니다.
    - **관련 코드 검색:** `search_file_content`를 사용해 에러 메시지, 관련 변수, 함수명 등을 검색하여 문제의 영향 범위를 파악합니다.
    - **컨텍스트 파악:** 관련된 모듈의 `api.py`, `README.md`, 설계 문서 등을 `read_many_files`로 확인하여 전체적인 구조를 이해합니다.

**3. 가설 수립 및 계획 (Hypothesis & Planning)**
    - **원인 추론:** 수집된 정보를 바탕으로 문제의 근본 원인에 대한 가설을 세웁니다.
    - **해결 계획 수립:**
        - 복잡한 문제의 경우, `/sg:troubleshoot` 또는 `/sg:analyze` 명령어 사용을 제안합니다.
        - 해결을 위한 구체적인 단계(수정할 파일, 함수, 테스트 방법 등)를 포함한 계획을 수립하고 사용자에게 승인을 요청합니다.
        - 계획은 `design/` 폴더 내에 마크다운 파일로 문서화하는 것을 원칙으로 합니다.

**4. 실행 및 검증 (Execution & Verification)**
    - **코드 수정:** `replace`, `edit_block`, `write_file` 등의 도구를 사용하여 계획에 따라 코드를 수정합니다.
    - **단위 테스트:** 수정된 부분과 관련된 테스트 코드를 실행하여(예: `pytest tests/test_engine.py`) 다른 기능에 영향을 주지 않는지 확인합니다.
    - **코드 품질 검사:** `ruff check .` 명령을 실행하여 코드 스타일 및 잠재적 오류를 점검합니다.

**5. 해결 및 문서화 (Resolution & Documentation)**
    - **해결 확인**: 시뮬레이션을 다시 실행하거나 테스트를 통해 문제가 완전히 해결되었는지 최종 확인합니다.
    - **루틴 동기화 (Automated)**: `python scripts/checkpoint.py`를 실행하여 인사이트 보고, 기술 부채 기록, 그리고 프로젝트 문서 동기화를 자동으로 수행합니다.
    - **사후 검토**: 다음 세션을 위한 Warm Boot 프롬프트를 확인합니다 (`design/snapshots/latest_snapshot.md`).

---

## W-3.5 Architecture Hygiene (Post-PR SoC Review)

Jules의 PR을 머지한 후, 코드가 "동작은 하지만 구조적으로 비대하거나 SoC 위반이 의심될 때" 실행하는 리팩토링 프로세스입니다.

### Trigger
- 머지된 코드가 단일 파일/클래스에 과도한 책임을 부여함
- 중복 로직 또는 순환 의존성 발견
- 모듈 간 결합도가 과도하게 높아짐

### Procedure

1.  **Antigravity (Team Leader)** 가 머지된 코드의 SoC 위반 여부를 평가.
2.  리팩토링이 필요하면, **`[Refactor Request]`** 형식의 새로운 지침서를 작성:
    - 분리할 클래스/함수의 **새 시그니처(API)**
    - 이동할 로직의 **책임 경계(DTO/Interface)**
    - 테스트 전략 (기존 테스트가 통과해야 함)
3.  이 지침서를 **프롬프트로 Jules에게 전달** (파일 Push 후 참조 링크 제공).
4.  Jules가 리팩토링 완료 후 **W-3 리뷰 재진행**.

### Refactor Request Template

```markdown
# [Refactor Request] <대상 모듈/파일명>

## 1. 분리 대상 (What to Extract)
- `ClassA.method_x()` → 새 클래스 `ServiceX`로 이동

## 2. 새 API 시그니처 (New Signature)
- class ServiceX:
    def execute(self, dto: InputDTO) -> OutputDTO

## 3. 테스트 요구사항
- 기존 테스트 `test_class_a.py` 통과 필수
- 새 테스트 `test_service_x.py` 추가

## 4. 참조 파일
- [원본 파일](file:///path/to/original.py)
- [관련 DTO](file:///path/to/dtos.py)
```


## 6. 기획 → 실행 계획 변환 프로세스 (Planning to Execution Process)

수석 아키텍트(Architect Prime)의 기획을 받아 실행 가능한 Work Order로 변환하는 표준 프로세스입니다.

### 6.2 Gemini CLI (Administrative Assistant) 활용
`gemini-cli`는 단순 반복 및 루틴 작업을 전담합니다.

**핵심 명령어:**
1. **`python scripts/gemini_worker.py audit "<타겟 분석>"`**: [NEW] 리팩토링/대규모 수정 전 **선행 감사(Pre-flight Audit)** 수행. 구조적 결함 식별 용도.
2. **`python scripts/gemini_worker.py spec "<기획안>"`**: 상세 명세(Spec) 및 API 초안 자동 작성. (Audit 결과 반영)
3. **`python scripts/gemini_worker.py verify -c <파일>`**: 아키텍처 및 SOC 위반 자동 검증.
4. **`python scripts/check_point.py`**: 세션 종료 전 모든 문서(Status, Tech Debt, Snapshot) 자동 동기화.

**제공되는 Worker Type:**
1. **`spec`**: 기획안 → 상세 명세 변환.
2. **`verify`**: SoC & DTO 프로토콜 검증.
3. **`context`**: 세션 압축 및 Warm Boot 프롬프트 생성.
4. **`git`**: Git 작업 자동화.
5. **`reporter`**: 코드 분석 및 대량 데이터 리포트 생성.

**✅ Best Practice: Contract Context**
- 함수나 클래스 명세를 작성할 때(`spec`), 대상 파일만 주면 존재하지 않는 타입이나 메서드를 창조(Hallucination)할 위험이 있습니다.
- 반드시 `simulation/dtos.py`나 `simulation/interfaces/`와 같은 **계약(Contract)** 파일을 함께 제공하십시오.
- 예: `python scripts/gemini_worker.py spec "..." -c simulation/target.py simulation/dtos.py`


### 6.3 ROI 분석 매트릭스 (예시)

| 기준 | 옵션 A | 옵션 B | 옵션 C |
|---|---|---|---|
| 구현 복잡도 | 낮음 | 중간 | 높음 |
| 테스트 용이성 | 높음 | 중간 | 낮음 |
| 효과 가시성 | 즉시 | 누적 | 장기 |
| 의존성 | 독립 | 독립 | A, B 필요 |
| **우선순위** | **1st** | 2nd | 3rd |

### 6.3 Work Order 구조

```markdown
# Work Order: WO-[ID] - [제목]

**Phase:** [Phase 번호]
**Priority:** [HIGH/MEDIUM/LOW]
**Prerequisite:** [선행 WO 또는 None]

## 1. Problem Statement
[핵심 문제 정의]

## 2. Objective
[목표 1줄 요약]

## 3. Target Metrics
| Metric | Current | Target |
|---|---|---|

## 4. Implementation Plan
### Track A: [Task 1]
### Track B: [Task 2]
### Track C: [Task 3]

## 5. Verification
[테스트 명령어 및 성공 기준]

## 6. Jules Assignment
| Track | Task | 파일 |
```

### 6.4 핵심 원칙

1. **Rule-Based → Adaptive AI**: 하드코딩 규칙보다 시장 메커니즘 우선
2. **커브 피팅 금지**: 결과를 억지로 맞추지 않고 원인을 규명
3. **최소 변경 원칙**: 가장 적은 코드로 최대 효과
4. **가설 검증**: 모든 변경은 측정 가능한 가설로 시작
