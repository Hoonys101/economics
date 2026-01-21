# SCR Launcher & Command Registry 매뉴얼

이 문서는 `design/command_registry.json` (Structured Command Registry)을 올바르게 작성하여 팀장(Antigravity)이 도구를 "장전"하고 사용자가 실행할 수 있게 돕는 공식 가이드라인입니다.

---

## 🚀 1. 전체 구조

`command_registry.json`은 각 도구별 섹션으로 나뉩니다. `scripts/launcher.py`는 이 파일을 읽어 실제 명령줄 인자를 생성합니다.

```json
{
  "gemini": { ... },
  "jules": { ... },
  "git_review": { ... },
  "merge": { ... },
  "harvest": { ... }
}
```

## 🔒 1-1. 템플릿 상속 및 불변성 (Template Inheritance) [NEW]

안전한 명령 실행을 위해, `command_registry.json`을 직접 수정하는 대신 **템플릿을 복사하여 덮어쓰는(Copy-and-Override)** 방식을 사용해야 합니다.

1.  **템플릿 (`design/templates/command_registry_template.json`)**: 모든 필드의 기본값이 사전 정의된 불변의 참조 파일입니다. 절대 이 파일을 직접 실행 대상으로 삼지 마십시오.
2.  **레지스트리 (`design/command_registry.json`)**: 실제 실행되는 파일입니다. 팀장은 템플릿을 읽어온 뒤, 필요한 필드만 수정한 "완전한 JSON"을 이 파일에 덮어씌워야 합니다.

**Why?**
- JSON 문법 에러(Comma 누락 등) 방지.
- 이전 세션의 잔존 설정(Stale Config)으로 인한 컨텍스트 오염 방지.
- 새 세션에서도 항상 표준화된 설정 구조 유지.

---

## 🧠 2. Gemini 섹션 (Planning / Audit)

`.\gemini-go.bat` 실행 시 사용됩니다.

- **`worker`**: 실행할 워커 유형 (`"spec"`, `"audit"`, `"git-review"`, `"reporter"` 등)
- **`instruction`**: 워커에게 전달할 핵심 지시사항 (문자열)
- **`context`**: 참조할 파일 경로 리스트 (Array of strings)
- **`output`**: 산출물이 저장될 경로. 아래 **[표준 출력 버킷]** 가이드를 반드시 준수하십시오.
- **`audit`**: (선택) 사전 감사 보고서 경로 (문자열, `-a` 옵션)
- **`model`**: (선택) 사용할 모델 (`"pro"` 또는 `"flash"`)

---

## 📁 2-1. 표준 출력 버킷 (Standard Output Buckets) [NEW]

모든 도구의 `output` 경로는 성격에 따라 아래 폴더 중 하나를 선택해야 합니다. 루트(Root)나 임의의 폴더에 파일을 생성하지 마십시오.

| 종류 | 저장 위치 (Bucket) | 설명 |
| :--- | :--- | :--- |
| **상세 설계 (Spec)** | `design/specs/` | 기능 구현 전 상세 기술 명세서 |
| **작업명세 (WO)** | `design/work_orders/` | 구현 발주를 위한 Work Order 문서 |
| **AI 분석 (Audit/Review)** | `design/gemini_output/` | 리스크 분석, 코드 리뷰, 성능 리포트 등 |
| **임시 산출물 (Draft)** | `design/drafts/` | 확정되지 않은 초안 또는 임시 파일 |
| **세션 핸드오버** | `design/handovers/` | (신설) 세션 종료 시 작성하는 핸드오버 문서 |

---

## 🛠️ 3. Jules 섹션 (Implementation)

`.\jules-go.bat` 실행 시 사용됩니다. **`command` 필드에 따라 필수 항목이 달라집니다.**

### A. 세션 생성 (`"command": "create"`)
- **`title`**: 작업의 제목 (예: `"WO-080_Fix_Bugs"`)
- **`instruction`**: 요원에게 전달할 구현 상세 지시 (문자열)
- **`wait`**: (Boolean) 요원이 작업을 마칠 때까지 기다릴지 여부

### B. 메시지 전송 (`"command": "send-message"`)
- **`session_id`**: 메시지를 보낼 활성 세션 ID (필수)
- **`instruction`**: 추가 지시사항 또는 피드백
- **`file`**: (선택) 지시사항을 텍스트 파일로 전달할 경우 해당 파일 경로
- **`wait`**: (Boolean)

### C. 목록 조회/기타 (`"command": "list-sessions"`, `"complete"`, `"get-session"`)
- **`session_id`**: `"complete"`, `"get-session"` 시 필수.
- **`command`**: 수행할 동작 명시.

---

## 🔍 4. Git Review 섹션

`.\git-go.bat` 실행 시 사용됩니다.

- **`branch`**: 리뷰할 타겟 브랜치명 (예: `"feat/ui-update"`)
- **`instruction`**: 리뷰 시 집중해야 할 리스크나 검증 포인트 (문자열)

---

## 🤝 5. Merge 섹션

`.\merge-go.bat` 실행 시 사용됩니다.

- **`branch`**: `main` 브랜치에 병합하고 삭제할 브랜치명 (문자열)

---

## ⌨️ 6. 입력을 위한 문자열 규칙 (String Rules for Input) [NEW]

터미널 환경에서 줄바꿈 문자(`\n`)가 포함된 인자를 전달할 때 발생하는 잘림 현상을 방지하기 위해, 런처는 다음 규칙을 적용합니다.

- **줄바꿈 자동 치환 (`\n` -> `|`)**: 
  - JSON 파일(`command_registry.json`)의 `instruction` 필드에 작성된 줄바꿈(`\n`)은 실행 시점에 파이프(`|`) 문자로 자동 변환되어 Jules에게 전달됩니다.
  - Jules AI는 전달받은 `|` 문자를 문맥상의 문장 구분자로 인식하여 작업을 수행합니다.
  - 따라서, JSON 작성 시에는 가독성을 위해 자유롭게 줄바꿈을 사용하셔도 됩니다.

---

## 💡 7. 실무자 피드백 요구 (Technical Debt Reporting) [CRITICAL]

Jules에게 미션을 발주(`create`)하거나 보완 지시(`send-message`)를 내릴 때, 팀장(Antigravity)은 반드시 아래 내용을 **보고서(Audit) 형태**로 요구해야 합니다. 이는 기술부채 대장 업데이트의 핵심 근거가 됩니다.

### 필수 요청 항목:
1. **발견된 스파게티 코드**: 작업 중 발견한 기존 코드의 비상식적인 구조나 악취.
2. **구현의 병목**: "이 기능을 더 깔끔하게 짤 수 없었던 이유" (예: 레거시 의존성, 순환 참조 등).
3. **신규 부채**: 시간 관계상 또는 구조적 한계로 인해 이번에 추가한 임시방편(Dirty Hack).
4. **상환 권고**: "어떻게 고치는 것이 근본적인 해결책인가?"에 대한 실무자의 의견.

### 권장 문구:
> "작업 완료 후, 구현 과정에서 발견하거나 유발한 기술적 한계 및 부채를 상세히 기술한 '실무자 보고서'를 함께 제출하세요."

---

## 🚨 주의사항 (Anti-Patterns)

1. **`command` 누락**: Jules 섹션에서 `command`를 누락하면 기본값인 `list-sessions`가 실행되어 작업 발주가 실패합니다.
2. **`wait` 설정**: 장시간 걸리는 작업(구현)의 경우 `wait: true`를 설정해야 팀장이 결과를 기다리고 다음 단계로 넘어갈 수 있습니다.
3. **경로 정합성**: `context`나 `file`에 존재하지 않는 경로를 적으면 런처에서 에러가 발생합니다.
