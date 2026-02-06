# 🔍 Git Diff Review: `watchtower-lock-and-socket`

## 1. 🔍 Summary

본 변경 사항은 `sqlite3.OperationalError: database is locked` 오류를 해결하고 서버 안정성을 대폭 향상시킵니다. 주요 내용은 파일 기반 잠금(lock)을 도입하여 서버 중복 실행을 방지하고, 데이터베이스 연결 설정을 최적화(WAL 모드)하며, 시그널 처리를 통해 우아한 종료(graceful shutdown)를 보장하는 것입니다.

## 2. 🚨 Critical Issues

- **없음.**
  - 보안 및 하드코딩 관련 위반 사항이 발견되지 않았습니다.
  - `server.py`에서 포트 번호를 `os.getenv`로 가져오도록 수정한 것은 좋은 사례입니다.
  - 시스템 절대 경로 또는 타사 레포지토리 정보가 하드코딩되지 않았습니다.

## 3. ⚠️ Logic & Spec Gaps

- **없음.**
  - 구현된 로직은 `communications/insights/watchtower_fix.md`에 기술된 문제의 근본 원인을 정확히 해결합니다.
  - `utils/simulation_builder.py`의 `fcntl`을 사용한 잠금 구현은 Unix 기반 시스템에서만 동작하지만, `ImportError`를 적절히 처리하고 Windows와 같은 미지원 플랫폼에 대해 경고 로그를 남기는 방식으로 처리되어, 합리적인 수준의 예외 처리를 보여줍니다.
  - `server.py`의 `lifespan` 관리자에서 초기화 실패 시 예외를 다시 발생시켜(re-raise), 서버가 비정상 상태로 실행되는 것을 막은 것은 올바른 설계입니다.

## 4. 💡 Suggestions

- **잠금 생명주기 관리**: `utils/simulation_builder.py`에서 잠금 파일 핸들(`lock_file`)을 시뮬레이션 객체(`sim._lock_file`)에 다소 비공식적으로 첨부하여 생명주기를 유지하고 있습니다. 이는 동작하지만, 향후 리팩토링 시 애플리케이션 생명주기를 관리하는 전용 컨텍스트 관리자(Context Manager)나 별도의 `LifecycleManager` 클래스를 도입하여 잠금과 해제를 더 명시적으로 관리하는 것을 고려할 수 있습니다. (이는 제출된 인사이트 리포트에서도 "leaky facade"로 언급된 부분과 일맥상통합니다.)

## 5. 🧠 Implementation Insight Evaluation

- **Original Insight**:
  ```markdown
  # Technical Insight Report: Watchtower Observability Recovery (TD-263)

  ## 1. Problem Phenomenon
  - Symptoms: `server.py` failed to restart with `sqlite3.OperationalError: database is locked`...

  ## 2. Root Cause Analysis
  - Zombie Processes: Previous server instances were not shutting down cleanly...
  - Race Condition in Initialization: `utils/simulation_builder.py` indiscriminately called `repository.clear_all_data()` (which performs a heavy `VACUUM` operation)...
  - Missing Application-Level Locking...

  ## 3. Solution Implementation Details
  - Process Isolation: Implemented a file-based lock (`simulation.lock`) using `fcntl`...
  - Database Hardening: Updated `simulation/db/database.py` to set `PRAGMA journal_mode=WAL`...
  - Graceful Shutdown: Added `signal` handlers (`SIGINT`, `SIGTERM`) in `server.py`...

  ## 4. Lessons Learned & Technical Debt
  - Lesson: SQLite `VACUUM` is a blocking operation and should be used with caution...
  - Lesson: For long-running async services, relying solely on `uvicorn`'s default signal handling might not be enough...
  - Technical Debt: The `Simulation` class "facade" pattern is slightly leaky...
  ```
- **Reviewer Evaluation**:
  - **정확성 및 깊이**: 작성된 인사이트는 발생한 현상, 근본 원인, 그리고 실제 코드 변경 사항을 매우 정확하고 깊이 있게 분석했습니다. 특히 좀비 프로세스와 `VACUUM` 동작으로 인한 초기화 시점의 경쟁 상태(Race Condition)를 정확히 지목한 점이 훌륭합니다.
  - **가치**: `fcntl`을 이용한 프로세스 단일 실행 보장, `WAL` 모드 적용, 우아한 종료(Graceful Shutdown) 구현 등 문제 해결을 위한 표준적이고 효과적인 접근법을 잘 정리했습니다.
  - **자기성찰**: 해결책을 구현하는 데 그치지 않고, `Simulation` 클래스의 설계가 갖는 한계(leaky facade)를 기술 부채로 명시한 점은 매우 긍정적이며, 프로젝트의 장기적인 아키텍처 개선에 기여할 수 있는 높은 수준의 통찰입니다.

## 6. 📚 Manual Update Proposal

- **Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md` (또는 유사한 기술 지식 베이스 파일)
- **Update Content**: 이번에 얻은 교훈을 일반화하여 중앙 지식 베이스에 추가할 것을 제안합니다.

  ```markdown
  ---
  
  ### ID: TD-263-Lesson
  - **Date**: 2026-02-06
  - **Author**: Jules
  - **Phenomenon**: `sqlite3.OperationalError: database is locked` 오류로 인해 서비스가 불안정해지고 재시작에 실패함.
  - **Root Cause**:
    1.  애플리케이션 레벨에서 단일 인스턴스 실행이 보장되지 않아 다수의 프로세스가 동일한 SQLite DB 파일에 동시 접근.
    2.  `uvicorn`과 같은 ASGI 서버의 기본 시그널 핸들러만으로는 무거운 백그라운드 작업의 완전한 정리를 보장할 수 없어 좀비 프로세스 발생.
    3.  시작 시점에 `VACUUM`과 같이 잠금을 유발하는 무거운 DB 작업을 무조건적으로 수행.
  - **Lesson Learned / Best Practice**:
    - **Single-Instance Guarantee**: 파일 잠금(`fcntl` on Unix, `msvcrt` on Windows) 등을 사용하여 여러 인스턴스가 동시에 실행되는 것을 방지해야 한다.
    - **Explicit Shutdown Logic**: `SIGINT`, `SIGTERM`에 대한 명시적인 시그널 핸들러를 등록하여, 진행 중인 작업을 안전하게 중단하고 리소스를 정리하는 우아한 종료(graceful shutdown) 로직을 반드시 구현해야 한다.
    - **Database Concurrency Mode**: 다중 접근이 예상되는 SQLite 데이터베이스는 `PRAGMA journal_mode=WAL` 설정을 연결 시점에 명시적으로 활성화하여 동시성을 향상시켜야 한다.
  
  ---
  ```

## 7. ✅ Verdict

**APPROVE**

- 심각한 안정성 문제를 해결하는 훌륭한 변경 사항입니다.
- 필수 요구사항인 `communications/insights/*.md` 보고서가 포함되었으며, 그 내용의 깊이와 정확성이 매우 뛰어납니다.
- 코드 변경 내용은 논리적으로 타당하며, 잠재적인 부작용을 고려한 방어적 코딩이 잘 적용되어 있습니다.
