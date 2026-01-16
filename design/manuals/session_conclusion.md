# 🏁 세션 종료 및 클린업 매뉴얼 (Session Conclusion Manual)

> **Identity:** 본 매뉴얼은 세션을 안전하게 종료하고, 다음 세션을 위해 작업 환경을 정합성 있게 유지하기 위한 팀장(Antigravity)의 최종 체크리스트입니다.

---

## 1. 📁 문서별 관리 내용 (Registry Update)

모든 작업 종료 시 아래 문서들을 최신 상태로 업데이트해야 합니다.

### 1.1 `design/project_status.md` (필수)
- **내용**: 현재 Phase의 진행률, 완료된 WO 목록, 다음 단계 업데이트.
- **포함 항목**: 완료된 작업(✅), 중단된 작업(🛑), 진행 중인 작업(🏗️).

### 1.2 `design/SESSION_LEDGER.md` (필수)
- **내용**: 이번 세션에서 사용된 모든 Jules 세션 ID와 작업 요약 기록.
- **포함 항목**: Date, Session ID, Task, Status/Summary.

### 1.3 `design/TECH_DEBT_LEDGER.md` (필수)
- **내용**: 세션 중 발견되거나 수용한 모든 기술 부채 기록.
- **항목**: ID, Date, Description, Remediation Plan, Impact, Status.

### 1.4 `design/HANDOVER_YYYY-MM-DD.md` (필수)
- **내용**: 다음 팀장(AI)이 세션을 이어받을 때 즉시 인지해야 할 핵심 맥락과 Quick-Start 가이드.

---

## 2. 🤖 Jules 세션 ID 정리 (Agent Cleanup)

작업이 완료되었거나 취소된 Jules 세션은 반드시 `communications/team_assignments.json`에서 정리해야 합니다.

- **완료된 세션**: `active_sessions`에서 삭제하고 `completed_sessions`로 이동. (메인 브랜치 병합 확인 후)
- **취소된 세션**: 즉시 `active_sessions`에서 삭제하여 혼선을 방지.
- **동기화**: 웹 UI에서 더 이상 유효하지 않은 세션임을 인지할 수 있도록, 브릿지를 통해 `complete` 명령 전송 가능 시 전송.

---

## 3. 🌿 Git 형상 관리 정리 (Git Cleanup)

### 3.1 로컬(Local) 정리
- **작업 브랜치**: 병합이 완료된 브랜치는 `git branch -d <branch_name>`으로 삭제.
- **정상 상태 유지**: `main` 브랜치로 체크아웃하고, `git pull origin main`으로 최신 상태 유지.
- **취소 작업 폐기**: 신뢰할 수 없는 결과물이 커밋된 경우, `git reset --hard` 등을 통해 깨끗한 상태로 롤백.

### 3.2 리모트(Remote) 정리
- **원격 브랜치**: 병합 완료된 원격 브랜치 삭제 확인 (`git push origin --delete <branch_name>`).
- **Prune**: 오래된 원격 참조 정리 (`git fetch --prune`).

---

## 4. 🚀 최종 체크리스트
1. [ ] 모든 코드 수정 사항이 커밋 및 푸시되었는가?
2. [ ] `team_assignments.json`에 유효하지 않은 ID가 남아있지 않은가?
3. [ ] 핸드오버 문서에 '다음 세션 첫 번째 할 일'이 명확히 기재되었는가?
4. [ ] 인코딩 문제가 우려되는 배치(bat) 파일의 한글 주석을 정리했는가?

---

**Antigravity Out.**
