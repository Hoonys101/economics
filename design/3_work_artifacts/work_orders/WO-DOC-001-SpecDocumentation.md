# WO-DOC-001: Spec Documentation & Current Status Sync

## 1. 개요 (Overview)
현재 `design/specs/` 폴더 내의 주요 명세서들이 초기 템플릿 상태(`[TODO: Jules]`)로 남아있습니다.
`design/JULES_DOCUMENTATION_GUIDE.md`의 지침에 따라, **실제 코드베이스를 분석**하여 이 명세서들을 현행화(Synchronization)해야 합니다.
또한, 프로젝트의 현재 진행 상황을 파악하기 위해 `interim_report.md`와 `project_status.md`를 업데이트합니다.

## 2. 작업 상세 (Implementation Details)

### 2.1 문서화 대상 파일 및 지침
다음 파일들을 순차적으로 작업하십시오. 각 파일의 작성 가이드는 `design/JULES_DOCUMENTATION_GUIDE.md`의 해당 섹션을 **반드시** 따르십시오.

1.  **`design/specs/analysis_spec.md` (분석 명세)**
    *   분석 대상: `economic_tracker.py`, `inequality_tracker.py`, `viewmodels`
    *   목표: 거시 지표 계산 로직 및 데이터 흐름 기술
2.  **`design/specs/main_integration_spec.md` (통합 명세)**
    *   분석 대상: `app.py`, `api.js`
    *   목표: API 엔드포인트 및 프론트엔드 연동 구조 기술
3.  **`design/specs/reportAndVisualize.md` (시각화 명세)**
    *   분석 대상: `ui.js`, `index.html`
    *   목표: 대시보드 UI 컴포넌트 및 데이터 소스 기술
4.  **`design/interim_report.md` (중간 보고서)**
    *   분석 대상: `git log`, `pytest` 결과
    *   목표: 최근 변경 사항 요약 및 테스트 현황 보고
5.  **`design/project_status.md` (프로젝트 현황)**
    *   분석 대상: `roadmap.md`, `implementation_plan.md`
    *   목표: 로드맵 대비 진행률 업데이트

### 2.2 제약 사항
*   **추측 금지**: 코드로 확인되지 않은 내용은 절대 적지 마십시오.
*   **출처 명시**: 가능한 경우 정보의 출처 파일과 라인 번호를 명기하십시오. (예: `[engine.py:120]`)
*   **태그 제거**: 작업이 완료된 파일에서 `[TODO: Jules]` 태그 제거.

## 3. 검증 계획 (Verification Plan)
*   **Self-Check**: 작성된 명세서의 내용이 `design/JULES_DOCUMENTATION_GUIDE.md`의 "작업 완료 기준"을 충족하는지 확인하십시오.
*   **Link Check**: 언급된 파일 경로 및 함수명이 실제 코드와 일치하는지 확인하십시오.

## 4. 인사이트 보고 요청
*   코드 분석 중 **설계와 구현의 불일치**나 **잠재적 버그**가 발견되면 `design/interim_report.md`의 "Issues & Risks" 섹션에 기록하십시오.
