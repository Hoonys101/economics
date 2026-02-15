# Code Review Report: Mission Registry Service

## 🔍 Summary
`command_manifest.py`를 대체하는 `MissionRegistryService`를 구현하고, 미션 관리의 무결성을 위한 `MissionLock` 및 프로토콜 주입 로직을 추가했습니다. 또한 `IHouseholdFactory` 누락 문제를 해결했습니다. 전반적인 구조는 견고하나, **Lock 구현에 치명적인 동시성 결함**이 발견되었습니다.

## 🚨 Critical Issues
### 1. 🔒 Broken Lock Implementation (Race Condition)
- **File**: `_internal/registry/service.py` (Line 22-36)
- **Problem**: `MissionLock`의 구현 방식이 원자적(Atomic)이지 않습니다.
  ```python
  while self.lock_file.exists():
      # ... wait ...
  self.lock_file.touch()  # <--- NOT ATOMIC
  ```
  `exists()` 확인과 `touch()` 실행 사이에 틈이 있습니다. 두 프로세스가 거의 동시에 `while` 루프를 통과하면, 둘 다 `touch()`를 성공적으로 실행(기본값 `exist_ok=True`)하고 락을 획득했다고 착각하게 됩니다.
- **Fix**: `open(..., 'x')` 또는 `path.touch(exist_ok=False)`를 사용하여 파일 생성의 원자성을 보장해야 합니다.
  ```python
  while True:
      try:
          self.lock_file.touch(exist_ok=False)
          break
      except FileExistsError:
          # ... timeout check & sleep ...
  ```

## ⚠️ Logic & Spec Gaps
### 1. Unsafe Migration Import
- **File**: `_internal/registry/service.py` (`migrate_from_legacy`)
- **Observation**: `importlib`을 사용하여 레거시 파일을 모듈로 로드하고 실행합니다. 만약 레거시 파일에 `if __name__ == "__main__":` 블록 없이 실행 코드가 있다면 사이드 이펙트가 발생할 수 있습니다.
- **Severity**: Low (로컬 마이그레이션 스크립트이므로), 하지만 데이터 파일이라면 `ast.literal_eval` 등을 고려하는 것이 더 안전합니다.

## 💡 Suggestions
- **Atomic File Creation**: 위 Critical Issue에 언급된 대로 `touch(exist_ok=False)`를 사용하십시오.
- **Type Safety**: `load_missions`에서 `MissionType` 변환 실패 시 경고 로그를 남기는 것이 디버깅에 유리합니다.

## 🧠 Implementation Insight Evaluation
- **Original Insight**: `TD-SYS-BATCH-FRAGILITY` 해결 및 `command_manifest.py` 제거, 프로토콜 주입 패턴 도입.
- **Reviewer Evaluation**: 
  - 기술 부채의 성격(Data as Code -> Managed Service)을 정확히 파악했습니다.
  - 마이그레이션 전략과 리스크 분석(One-Way Valve)이 타당합니다.
  - `IHouseholdFactory` 관련 수정 사항을 투명하게 보고한 점이 우수합니다.

## 📚 Manual Update Proposal (Draft)
**Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`

```markdown
### 2026-02-15: Mission Registry Service Migration
- **Status**: Resolved
- **Debt Type**: SYS-BATCH-FRAGILITY
- **Description**: Replaced fragile `command_manifest.py` with `MissionRegistryService` and JSON-based persistence (`mission_db.json`).
- **Solution**:
    - Implemented `MissionRegistryService` with file-based locking.
    - Added `scripts/mission_launcher.py` for CLI management.
    - Enforced `MissionDTO` and Protocol Injection for safety.
- **Lesson**: Infrastructure code (launchers/manifests) requires the same rigor (DTOs, Services, Tests) as core business logic to prevent environment drift.
```

## ✅ Verdict
**REQUEST CHANGES**

**Reason**: `MissionLock`의 Race Condition 문제는 파일 기반 DB(`mission_db.json`)의 무결성을 깨뜨릴 수 있는 치명적인 결함입니다. 원자적(Atomic) 파일 생성을 보장하도록 수정 후 다시 제출하십시오.