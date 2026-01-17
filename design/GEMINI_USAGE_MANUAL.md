# Gemini Usage Manual: The SCR Protocol
**Structured Command Registry (SCR) 가이드**

이 매뉴얼은 `design/command_registry.json`을 수정하여 Gemini, Jules, Git Reviewer 등 AI 도구를 제어하는 방법을 설명합니다.

---

## 🏗️ 기본 원칙 (The Core Principle)

우리는 더 이상 `.bat` 파일을 직접 수정하지 않습니다. 모든 명령은 **데이터(JSON)**로 정의되고, `launcher.py`가 이를 안전하게 실행합니다.

**Workflow:**
1.  **Load**: `command_registry.json`의 해당 섹션(`gemini` or `jules`)을 수정하여 명령을 장전합니다.
2.  **Fire**: `gemini-go.bat` 또는 `jules-go.bat`를 실행하여 장전된 명령을 발사합니다.

---

## 🤖 1. Gemini (기획/감사/명세)

Gemini는 프로젝트의 두뇌입니다. 코드를 분석하고, 명세서를 작성하며, 감사를 수행합니다.

### 문법 (Schema)
```json
  "gemini": {
    "worker": "audit | spec | verify | context",
    "instruction": "<구체적인 지시사항>",
    "context": [
      "분석할/참조할 파일 경로 1",
      "분석할/참조할 파일 경로 2"
    ],
    "output": "결과물 저장 경로 (선택사항, 기본값 자동 지정)",
    "audit": "참조할 감사 보고서 경로 (spec 모드에서 필수)",
    "model": "pro | flash (선택사항, 기본값: pro)"
  }
```

### 1.1 감사 (Audit) - `gemini-go.bat`
코드의 구조적 문제(God Class 확인, 순환 참조 등)나 레거시 로직을 분석할 때 사용합니다.
- **Worker**: `audit`
- **Context**: 분석 대상 파일들

### 1.2 명세 작성 (Spec) - `gemini-go.bat`
구현에 들어가기 전 상세 명세서를 작성합니다.
- **Worker**: `spec`
- **Context**: 관련 DTO, 인터페이스 파일 (계약서)
- **Audit**: (강력 권장) 1.1에서 생성한 감사 보고서 경로를 넣어주면, 더 안전한 명세가 나옵니다.

### 1.3 검증 (Verify) - `gemini-go.bat`
작성된 코드나 명세가 아키텍처 원칙(SoC)을 준수하는지 검증합니다.
- **Worker**: `verify`
- **Context**: 검증할 대상 파일 (코드 또는 명세서)

---

## 👩‍💻 2. Jules (구현/코딩)

Jules는 실제 코드를 작성하고 수정하는 엔지니어입니다.

### 문법 (Schema)
```json
  "jules": {
    "command": "create | send-message",
    "session_id": "활성 세션 ID (send-message 시 필수)",
    "title": "세션 제목 (create 시 필수)",
    "instruction": "<작업 지시사항 (Work Order 요약)>",
    "wait": true
  }
```

### 2.1 새 작업 시작 (Create) - `jules-go.bat`
새로운 기능 구현이나 리팩토링을 시작할 때 사용합니다.
- **Command**: `create`
- **Instruction**: "구현할 내용. TASKS: 1. A, 2. B... REFERENCE: work_order.md"

### 2.2 대화/수정 요청 (Send Message) - `jules-go.bat`
이미 진행 중인 작업에 피드백을 주거나, 질문에 답할 때 사용합니다.
- **Command**: `send-message` (또는 `msg`)
- **Session ID**: `design/SESSION_LEDGER.md`나 `team_assignments.json`에서 ID 확인 후 입력.
- **Instruction**: "테스트 실패 원인은 X이다. Y방식으로 수정하라."

---

## 🔍 3. Git Review (코드 리뷰)

PR이 올라왔을 때 AI에게 보안 및 아키텍처 리뷰를 요청합니다.

### 문법 (Schema)
```json
  "git_review": {
    "branch": "feature/branch-name",
    "instruction": "중점적으로 리뷰할 내용 (예: 보안 취약점, SoC 위반 여부)"
  }
```

**실행**: `git-go.bat <브랜치명>` (인자로 브랜치명을 주면 JSON을 무시하고 해당 브랜치를 리뷰하지만, JSON에 설정을 남기는 것을 권장합니다.)

---

## 🔗 Tips for Team Leader

1.  **Context is King**: Gemini에게 `dtos.py`나 `interfaces/` 파일을 주지 않고 명세를 짜라고 하면 환각(Hallucination)을 봅니다. 계약서(Contract)를 반드시 건네주세요.
2.  **Audit First**: 복잡한 리팩토링 전에는 반드시 `audit` 모드로 위험 요소를 먼저 파악하십시오.
3.  **One Shot, One Kill**: Jules에게 너무 긴 지시사항을 한 번에 주면 헷갈려합니다. Work Order 문서를 먼저 만들고, JSON에는 "WO-XXX를 참조하여 구현하라"고 적는 것이 가장 확실합니다.
