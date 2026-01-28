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

## 🔴 DLL 로딩 실패 (C++ Agent)

**증상**: `ImportError`, `OSError: [WinError 126]`, 또는 에이전트 실행 시 즉시 종료.

**해결**:
1. **Bitness 확인**: Python 인터프리터(64bit)와 DLL(32bit 또는 64bit)의 비트가 일치하는지 확인. (일반적으로 NH증권 API 등은 32bit 인터프리터 필요 케이스가 많음)
2. **VC++ Redistributable 설치**: 최신 [Microsoft Visual C++ 재배포 가능 패키지](https://aka.ms/vs/17/release/vc_redist.x64.exe) 설치.
3. **DLL 경로(Search Path) 추가**: `os.add_dll_directory()` (Python 3.8+) 또는 PATH 환경 변수에 DLL이 포함된 폴더 추가.
4. **의존성 확인**: `Dependencies` (GUI tool) 등을 사용하여 해당 DLL이 참조하는 다른 DLL이 누락되지 않았는지 확인.
5. **권한 확인**: DLL 파일에 대한 읽기/실행 권한이 있는지 확인.

---

---

## 🔴 제로섬/회계 버그 (Zero-Sum Drift)

**증상**: 시뮬레이션에서 지속적으로 원인 불명의 자금 증가(Positive Money Drift)가 발생. 특히 정부의 특정 활동(예: 사회기반시설 투자) 직후 발생함.

**원인**:
1. 시스템 내부 주체 간의 자금 이체(Internal Fiscal Transfer)를 일반 시장 거래와 동일한 `Transaction` 객체로 처리했기 때문.
2. 이로 인해 `TransactionProcessor`가 해당 이체를 일반 상거래로 오인하여 불필요한 세금 계산 등 의도치 않은 부수 효과를 일으켜 자금 복사 버그를 유발함.

**해결**:
1. `TransactionProcessor`를 우회하도록 수정.
2. `Transaction` 객체를 생성하는 대신, `SettlementSystem.transfer()`와 같은 원자적 이체 함수를 직접 호출하여 두 시스템 간에 자산을 직접 이체하도록 변경.

**교훈**:
- **"내부 이체와 시장 거래를 명확히 분리하라."** 시스템 내부의 자금 이체는 일반 거래 시스템(세금, 수수료 로직 포함)을 통과해서는 안 된다. 이는 예기치 않은 로직 적용으로 제로섬(Zero-Sum) 원칙을 훼손하는 주요 원인이 된다.

---

*문제가 해결되지 않으면 수석 아키텍트에게 보고하십시오.*
