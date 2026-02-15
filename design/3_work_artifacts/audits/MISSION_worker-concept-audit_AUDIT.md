# 워커 역할 정의 및 문서 참조 능력 분석 보고서

## Executive Summary
본 보고서는 `gemini_worker.py`와 `mission_protocol.py`에 정의된 워커(Worker)들의 역할과 실무 활용 시나리오, 그리고 Gemini의 문서 참조 메커니즘을 분석한 결과입니다. 'git' 워커는 상태를 변경하는 **Operator**이며, 'review' 워커는 품질을 감시하는 **Reviewer**로 정의됩니다. 문서 참조는 RAG 방식이 아닌 **전체 컨텍스트 주입(Full Context Injection)** 방식을 사용하며, 이는 사용자가 명시적으로 제공한 컨텍스트 범위 내에서만 작동합니다.

---

## Detailed Analysis

### 1. 'git' vs 'review' 워커의 차이점
- **'git' 워커 (GitOperator)**:
    - **역할**: 저장소 상태를 변경하는 **수행자(Operator)**.
    - **책임**: `git status`, `add`, `commit` 등의 명령어를 생성하고, 위험도가 낮을 경우 직접 실행(`auto_run`)할 수 있습니다.
    - **결과물**: 실행 계획이 담긴 JSON 데이터 및 실제 Git 명령어 수행 결과.
- **'review' 워커 (GitReviewer)**:
    - **역할**: 코드의 변경 사항을 분석하는 **검토자(Reviewer)**.
    - **책임**: `git diff`를 읽어 버그, 아키텍처 위반, 코드 스타일 등을 지적하고 개선 방향을 제시합니다.
    - **결과물**: 분석 의견이 정리된 마크다운 보고서.

### 2. 'verify' 및 'context' 워커 실무 활용 시나리오
- **'verify' 워커 (Validator)**:
    - **시나리오**: 구현 완료 후 **아키텍처 가드레일(UPS-2.0)** 준수 여부 검증.
    - **예시**: "새로 작성한 `transaction_service.py`가 Zero-Sum 원칙을 지키는지, Protocol을 올바르게 구현했는지 확인해줘."
- **'context' 워커 (ContextManager)**:
    - **시나리오**: 업무 교대(Handover) 또는 마일스톤 종료 시 **상태 요약(Snapshot)**.
    - **예시**: "오늘 작업한 핵심 변경 사항과 해결되지 않은 기술 부채를 요약해서 `latest_snapshot.md`를 업데이트해줘."

### 3. 'spec' 및 'review' 워커의 문서 참조 능력 분석
- **참조 방식 (Full Context Injection)**:
    - `gemini_worker.py`는 `--context`로 전달된 파일이나 디렉토리 내의 모든 내용을 읽어 Gemini의 프롬프트에 직접 포함시킵니다.
    - 이는 RAG(검색 기반 생성)가 아니므로, 모델은 제공된 텍스트의 **전체 관계를 한 번에 파악**할 수 있는 장점이 있으나, 컨텍스트 윈도우 크기에 제한을 받습니다.
- **문서 자동 탐색 가능 여부**:
    - **불가능**: Gemini가 "관련 문서를 알아서 찾아 읽으라"는 지시를 수행하려면 파일 시스템을 검색하고 읽는 도구를 스스로 호출해야 하나, 현재 워커 스크립트는 프롬프트 생성 시점에 컨텍스트를 확정하여 전달하는 구조입니다.
    - **제약**: 사용자가 `--context`에 경로를 포함시키지 않은 문서는 Gemini가 물리적으로 볼 수 없습니다.

---

## 워커 활용 퀵 가이드 (Quick Guide)

| 워커 (Worker) | 주요 책임 (Responsibility) | 주요 결과물 | 사용 시점 |
| :--- | :--- | :--- | :--- |
| **spec** | 설계 및 명세서 작성 | `draft_*.md` | 코드 작성 전, 구조 설계 시 |
| **git** | Git 명령 생성 및 실행 | 저장소 변경 (Commit 등) | 변경 사항을 반영하고 싶을 때 |
| **git-review** | 코드 퀄리티 분석 | Review Report | PR 제출 전 또는 코드 진단 시 |
| **verify** | 아키텍처 규칙 검증 | Validation Report | 구현 후 가드레일 준수 확인 시 |
| **context** | 세션 상태 및 맥락 관리 | `snapshot.md` | 업무 종료 또는 인수인계 시 |
| **reporter** | 기술 부채 및 지표 보고 | Technical Report | 프로젝트 현황 파악 및 감사 시 |
| **crystallizer**| 통찰력 정제 및 자산화 | Crystallization Spec | 경험을 아키텍처로 박제할 때 |

---

## Risk Assessment
- **파일명 불일치 가능성**: `gemini_worker.py`는 `spec_writer.md`, `git_operator.md` 등의 파일을 참조하나, 실제 `_internal/manuals/`에는 `spec.md`, `git.md`로 존재할 수 있어 실행 시 `FileNotFoundError` 위험이 관찰됨.
- **컨텍스트 오버플로우**: 대량의 파일을 디렉토리 단위로 주입할 경우 토큰 제한을 초과하거나 성능 저하가 발생할 수 있음.

## Conclusion
워커 시스템은 각자의 전담 매뉴얼을 통해 전문화된 역할을 수행합니다. 사용자는 **Operator(git)**와 **Reviewer(review)**를 명확히 구분하여 사용해야 하며, Gemini의 지능을 극대화하기 위해서는 필요한 문서를 `--context`를 통해 명시적으로 전달하는 습관이 필수적입니다.

---

### 🚨 [MANDATORY REPORTING: Insight Report]
*Note: As per "Technical Reporter" Operational Protocol, I am a content generator and cannot modify the filesystem. Below is the content intended for `communications/insights/worker-concept-audit.md`.*

```markdown
# Insight Report: Worker Concept Audit
**Date**: 2026년 2월 15일 일요일
**Key**: worker-concept-audit

## 1. [Architectural Insights]
- **Context Handling**: 현재 시스템은 RAG가 아닌 Full Context Injection 방식을 채택하고 있음. 이는 소규모 모듈 감사에는 유리하나, 프로젝트 전체 맥락을 파악하기에는 '선택적 컨텍스트 제공' 능력이 부족함.
- **Worker Configuration Drift**: `gemini_worker.py`의 하드코딩된 매뉴얼 파일명과 실제 파일명 사이의 불일치 가능성이 식별됨. 매뉴얼 로드 실패 시의 폴백(Fallback) 로직 부재.
- **Logic Separation**: `GitOperator`에 `auto_run` 기능이 포함되어 있어, LLM의 오판 시 저장소 상태가 예기치 않게 변경될 수 있는 Risk 존재. (High Risk 시 차단 로직은 구현됨)

## 2. [Test Evidence]
- `gemini_worker.py`의 `BaseGeminiWorker` 상속 구조 및 `expanded_files` 로직 검토 완료.
- `mission_protocol.py`의 `WORKER_MODEL_MAP` 및 프롬프트 생성 함수(`construct_mission_prompt`) 무결성 확인.
- (Local Simulation): `spec` 워커 호출 시 `SpecDrafter.execute` 내부의 `Auto-Audit` 호출이 정상적으로 설계되었음을 확인.
```