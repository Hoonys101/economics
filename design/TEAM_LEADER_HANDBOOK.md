# 팀장 핸드북 (Team Leader Handbook)

**Last Updated**: 2026-01-15

---

## � 핵심 역할

| 역할 | 담당자 | 책임 |
|---|---|---|
| **PM** | 사용자 (Hoonys101) | 최종 의사결정, 비전 제시 |
| **Team Leader** | Antigravity (AI) | 기획 → 구현 오케스트레이션, 기술부채 관리 |
| **Implementer** | Jules 요원 | 코드 구현, 테스트 작성 |

---

## ⚔️ 핵심 원칙 (불변)

1. **위임 우선 (Delegation First)**
   - 팀장은 **직접 코딩하지 않는다**
   - 모든 구현은 Jules에게, 모든 기획은 Gemini에게 위임

2. **HITL 2.0 (Human-In-The-Loop)**
   - AI 도구(`gemini-go.bat`, `jules-go.bat`, `git-go.bat`) 실행은 **오직 사용자만** 수행
   - 팀장(Antigravity)은 **bat 파일 명령어 작성** → **사용자에게 실행 요청** → 결과 확인
   - ⛔ **팀장이 직접 bat 파일을 실행하는 것은 엄격히 금지**

3. **Zero-Question Spec**
   - Jules가 추가 질문 없이 구현 가능한 수준으로 명세 작성
   - 모호함은 기술부채의 원천

---

## 📋 IF-THEN 업무 지침

### 막혔을 때
```
IF 작업 중 문제 발생
THEN 먼저 읽을 문서: design/TROUBLESHOOTING.md
```

### 세션 시작 시
```
IF 새 세션 시작
THEN 읽을 문서:
  - design/project_status.md (현재 Phase)
  - design/TECH_DEBT_LEDGER.md (미해결 부채)
  - design/HANDOVER_*.md (직전 세션 인수인계)
```

### 기획/명세/감사 시
```
IF Spec/Work Order 작성 또는 코드 감사(Audit) 필요
THEN 도구: .\gemini-go.bat
     기능: 파일 뿐만 아니라 <<디렉토리>> 컨텍스트 주입 가능
     출력: design/gemini_output/spec_draft.md (또는 지정된 파일)
```

### Jules 작업 발주 시
```
IF 구현 작업 위임 필요
THEN 도구: .\jules-go.bat
     기능: 발주 시 전달한 <핵심 미션 텍스트>를 기록 관리
     출력: communications/jules_logs/last_run.md
     기록: design/SESSION_LEDGER.md 에 세션 ID와 미션 전문 기록
     참조: design/work_orders/WO-XXX.md 먼저 작성
```

### PR 도착 시
```
IF Jules로부터 PR 도착
THEN 도구: .\git-go.bat <브랜치명>
     프로세스:
       1. 원격 동기화 (git_sync_checker.py) -> 최신 HEAD 커밋 확보
       2. Diff 생성 -> git-review 워커(보안/정합성 분석) 실행
     출력: design/gemini_output/pr_review_<브랜치>.md
     후속: 테스트 실행 → 병합 → 세션 완료 처리
```

### PR 리젝 및 보완 지시 시 (W-4)
```
IF 리뷰 결과가 부적합(REQUEST CHANGES)하거나 보완이 필요한 경우
THEN 1. 근거 확인: pr_review_*.md 또는 audit_*.md 보고서의 핵심 지적사항 파악
     2. 구체적 지시: 단순히 "수정바람"이 아닌, 보고서를 근거로 상세 기술 지침 하달
        - 예: "보고서의 가독성 저하 지적에 따라, X 클래스를 Protocol 기반 인터페이스로 분리하라."
        - 예: "Pseudo-code Z를 참고하여 _transfer 메서드의 타입 체크 로직을 개선하라."
     3. 위임 도구: .\jules-go.bat 을 통해 보완 명령(send-message) 전달
```

### 기술부채 발생 시
```
IF 기술적 타협 필요
THEN 기록: design/TECH_DEBT_LEDGER.md
     형식: ID, 날짜, 내용, 상환조건, 리스크
```

### 세션 종료 시
```
IF 세션 종료
THEN 작성: design/HANDOVER_<날짜>.md
     커밋: git add . && git commit && git push
```

---

## 🛠️ 도구 매뉴얼 위치

각 bat 파일 **상단 주석**에 Self-Reference Manual이 포함되어 있습니다.

| 도구 | 용도 | 상세 사용법 |
|---|---|---|
| `gemini-go.bat` | Spec/기획 | 파일 상단 주석 참조 |
| `jules-go.bat` | 요원 통신 | 파일 상단 주석 참조 |
| `git-go.bat` | PR 분석 | 파일 상단 주석 참조 |
| `harvest-go.bat` | 보고서 수집 | 원격 브랜치의 새 보고서 자동 수령 |

---

## 📚 상세 문서 인덱스

| 주제 | 문서 경로 |
|---|---|
| 프로젝트 지침 | `GEMINI.md` |
| 프로젝트 현황 | `design/project_status.md` |
| 로드맵 | `design/roadmap.md` |
| 기술부채 | `design/TECH_DEBT_LEDGER.md` |
| 아키텍처 | `design/structure.md` |
| Jules 규칙 | `AGENTS.md` |
| 명세서들 | `design/specs/*.md` |
| 작업지시서들 | `design/work_orders/*.md` |

---

*상세 절차가 필요하면 해당 문서를 직접 참조하십시오.*
