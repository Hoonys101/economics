# 트러블슈팅 가이드 (Troubleshooting Guide)

**Last Updated**: 2026-01-15

막혔을 때 이 문서를 먼저 확인하십시오.

---

## 🔴 Jules가 응답하지 않음

**증상**: 메시지를 보냈는데 반응이 없음

**해결**:
1. `.\jules-go.bat` 실행하여 세션 상태 확인
2. 세션이 `COMPLETED`면 새 세션 생성 필요
3. 세션이 `IN_PROGRESS`면 5분 대기 후 재확인

---

## 🔴 테스트가 실패함

**증상**: pytest 실행 시 AssertionError

**해결**:
1. 오류 메시지의 **Delta 값** 확인 (예상값 vs 실제값)
2. Delta가 미세하면 (< 0.001) → 반올림 오류, `math.isclose()` 사용
3. Delta가 크면 (> 1.0) → 로직 오류, 해당 함수 점검

---

## 🔴 Import Error 발생

**증상**: `ModuleNotFoundError` 또는 `ImportError`

**해결**:
1. **순환 참조** 의심 → `TYPE_CHECKING` 블록 사용
2. 인터페이스 정의가 필요하면 `simulation/interfaces/`에 분리

---

## 🔴 Git 충돌 발생

**증상**: merge conflict

**해결**:
1. `git status`로 충돌 파일 확인
2. `git checkout --theirs <파일>` (상대방 버전 채택) 또는
3. `git checkout --ours <파일>` (내 버전 유지)
4. `git add . && git commit`

---

## 🔴 Gemini가 할루시네이션함

**증상**: 존재하지 않는 함수/클래스 언급

**해결**:
1. `-c` 옵션으로 **DTO/Interface 파일**을 컨텍스트에 포함했는지 확인
2. 예: `python scripts/gemini_worker.py spec "..." -c simulation/dtos.py`

---

## 🔴 시뮬레이션이 멈춤

**증상**: 무한 루프 또는 진행 없음

**해결**:
1. `Ctrl+C`로 중단
2. 마지막 성공 Tick 로그 확인
3. 해당 Tick의 에이전트 상태 점검 (assets < 0, 재고 = 0 등)

---

## 📝 새로운 문제 발견 시

이 문서에 추가하십시오:
```markdown
## 🔴 [증상 제목]

**증상**: [구체적 현상]

**해결**:
1. [단계 1]
2. [단계 2]
```

---

*문제가 해결되지 않으면 수석 아키텍트에게 보고하십시오.*
