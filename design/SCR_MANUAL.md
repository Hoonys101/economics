# 📜 Structured Command Registry (SCR) Manual

**"스크립트 수정 없이, JSON만으로 모든 AI Agent를 지휘한다."**

이 매뉴얼은 `design/command_registry.json` 파일의 작성법을 다룹니다. 이 파일은 프로젝트의 모든 자동화 도구(Gemini, Jules, Git Reviewer)의 **관제탑** 역할을 합니다.

---

## 1. 파일 구조 (Structure)

`command_registry.json`은 도구 이름을 키(Key)로 하는 최상위 객체로 구성됩니다.

```json
{
  "gemini": { ... },
  "jules": { ... },
  "git_review": { ... },
  "merge": { ... },
  "harvest": { ... }
}
```

---

## 2. Gemini (기획, 감사, 검증)

Gemini는 코드를 읽고, 분석하고, 문서를 작성하는 역할을 합니다.

### 2.1 스키마
```json
"gemini": {
  "worker": "audit | spec | verify | context",
  "instruction": "Gemini에게 시킬 구체적인 작업 지시사항",
  "context": [
    "참조할 파일 경로 1 (프로젝트 루트 기준)",
    "참조할 폴더 경로 2 (재귀적으로 포함됨)"
  ],
  "output": "design/specs/my_spec.md (결과물 저장 경로)",
  "audit": "reports/temp/audit_report.md (Spec 모드에서 참조할 감사 리포트)",
  "model": "pro | flash (사용할 모델, 기본값: pro)"
}
```

### 2.2 모드별 사용법
| Worker | 용도 | 필수 항목 |
| :--- | :--- | :--- |
| **audit** | 기존 코드의 문제점 분석 | `context` (분석 대상 코드) |
| **spec** | 구현 전 상세 설계서 작성 | `output` (저장 경로), `audit` (권장) |
| **verify** | 구현된 코드가 설계와 일치하는지 검증 | `context` (코드 + 설계서) |
| **context** | 현재 상태 요약 (Snapshot) | `output` |

---

## 3. Jules (구현, 코딩)

Jules는 실제로 Git 브랜치를 따고, 코드를 수정하고, PR을 올리는 엔지니어입니다.

### 3.1 스키마
```json
"jules": {
  "command": "create | send-message",
  "session_id": "활성 세션 ID (send-message 시 필수)",
  "title": "작업 제목 (create 시 필수, PR 제목이 됨)",
  "instruction": "작업 지시사항 (Work Order 내용 요약)",
  "file": "지시사항이 담긴 파일 경로 (instruction 대신 사용 가능)",
  "wait": true (응답을 기다릴지 여부, 기본값: false)
}
```

### 3.2 명령어별 사용법

#### A. 새 작업 시작 (`create`)
```json
"jules": {
  "command": "create",
  "title": "WO-101_Fix_Login_Bug",
  "instruction": "로그인 시 500 에러를 수정하라. REFERENCE: design/specs/login_fix.md",
  "wait": true
}
```

#### B. 피드백 주기 (`send-message`)
진행 중인 세션에 추가 지시를 내리거나 질문에 답합니다.
```json
"jules": {
  "command": "send-message",
  "session_id": "123456789...",
  "instruction": "테스트가 실패했다. api.py의 50번째 줄을 확인해라.",
  "wait": true
}
```

---

## 4. Git Review & Merge (형상 관리)

### 4.1 Git Review
PR이 올라왔을 때 AI 리뷰를 수행합니다.
```json
"git_review": {
  "branch": "feature/login-fix",
  "instruction": "보안 취약점 위주로 리뷰하라."
}
```

### 4.2 Merge
PR을 머지하고 브랜치를 정리합니다.
```json
"merge": {
  "branch": "feature/login-fix"
}
```

---

## 5. 실행 방법 (Excution)

JSON을 수정한 후, 아래 **배치 파일**을 실행하면 됩니다.

1.  `gemini-go.bat`: `gemini` 섹션의 설정을 실행.
2.  `jules-go.bat`: `jules` 섹션의 설정을 실행.
3.  `git-go.bat`: `git_review` 섹션의 설정을 실행.
4.  `merge-go.bat`: `merge` 섹션의 설정을 실행.

> **Tip**: 모든 배치 파일은 내부적으로 `scripts/launcher.py`를 호출합니다.
