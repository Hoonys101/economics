---
description: How to author and register a new command in the SCR (Structured Command Registry)
---

# 📖 SCR Command Authoring Workflow

이 워크플로우는 팀장(Antigravity)이 `design/command_registry.json`을 작성할 때 파이썬 코드를 뒤져보지 않고도 즉시 명령을 구성할 수 있도록 설계되었습니다.

## 1. 📋 사전 체크리스트
- [ ] 작업을 수행할 도구가 무엇인가? (Gemini, Jules, Git-Review, Merge)
- [ ] 관련 템플릿이 `design/templates/command_registry_template.json` 에 정의되어 있는가?
- [ ] 입력할 `instruction`에 `|` (파이프)를 사용하여 단계별 구분을 명시했는가?

## 2. 🏗️ 도구별 JSON 구조 가이드

### 🧠 Gemini (Planning/Audit)
- **Key**: `gemini` (또는 커스텀 키)
- **Fields**:
  - `worker`: `spec`(명세), `audit`(감사), `verify`(검증), `reporter`(보고)
  - `instruction`: 수행할 작업의 세부 내용
  - `context`: [Array] 참조할 파일 경로 리스트
  - `output`: 결과 저장 경로 (`design/specs/` 또는 `design/gemini_output/`)
  - `audit`: (Spec 작성 시) 선행 감사 보고서 경로

### 🛠️ Jules (Implementation)
- **Key**: `jules` (또는 미션 제목)
- **Fields**:
  - `command`: `create` (새 세션), `send-message` (피드백)
  - `title`: 미션 제목 (예: `WO-112-Fix-Bug`)
  - `session_id`: (피드백 시 필수) 활성 세션 ID
  - `instruction`: 구현 상세 지침 + **실무자 보고서 요구 포함**
  - `wait`: `true` (기본값)

### 🐙 Git Review & Merge
- **Git Review**: `branch`, `instruction`
- **Merge**: `branch`

## 3. ⚡ 자동화 원칙 (Self-Correction)
- Antigravity(나)는 명령을 작성할 때 반드시 `design/manuals/scr_launcher.md`의 문법을 준수한다.
- JSON 작성 시 문법 오류를 방지하기 위해 `write_to_file` 도구를 사용하며, 기존 레지스트리를 덮어쓸지 추가할지 결정한다.
- **보고서 요구**: Jules 발항 시 반드시 "구현 과정의 기술적 한계 및 부채를 포함한 실무자 보고서를 제출하라"는 문구를 포함한다.

## 4. 🚀 실행 프로세스
1. `design/command_registry.json`에 데이터 작성 (장전).
2. 사용자에게 `.\gemini-go.bat` 또는 `.\jules-go.bat` 실행 요청.
3. 실행 결과(`design/gemini_output/` 또는 `communications/jules_logs/`) 확인.

---
**"데이터가 명령을 내리고, 코드는 실행할 뿐이다."**
