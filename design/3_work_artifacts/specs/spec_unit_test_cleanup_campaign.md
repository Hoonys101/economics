# Spec: Unit Test Cleanup & Hardcoded Constant Campaign

## 1. Overview
모듈별 Unit Test 정비 및 시스템 상수 하드코딩(TD-INT-CONST) 해소를 병렬로 수행합니다.

## 2. Reference Documents (MUST READ)
- **[ARCH_TESTS.md](../../1_governance/architecture/ARCH_TESTS.md)**: 테스트 모듈 매핑, 커버리지 갭, 구조 개선안
- **[TECH_DEBT_LEDGER.md](../../2_operations/ledgers/TECH_DEBT_LEDGER.md)**: 활성 부채 목록

## 3. Campaign Goals (Per Module)

### Goal A: Fix Broken Unit Tests
- 해당 모듈의 유닛 테스트를 실행합니다.
- **깨진 테스트**: 원인을 파악하고 수정합니다.
  - 타 모듈 의존성이 원인인 경우 → 수정하지 말고 `communications/insights/` 에 기술 부채로 기록.
  - Mock/Import 오류가 원인인 경우 → 즉시 수정.
- **통과하는 테스트**: 이상 없음을 기록.
- **누락된 테스트**: ARCH_TESTS.md의 Coverage Gaps 참조. 핵심 로직에 대한 테스트가 없는 경우 기록.

### Goal B: Replace Hardcoded Constants (TD-INT-CONST)
해당 모듈 소스 코드 및 테스트 코드에서 다음 하드코딩 패턴을 검색하고 시스템 상수로 교체합니다:

| 하드코딩 패턴 | 교체 대상 (Import) |
| :--- | :--- |
| `"USD"` (문자열 리터럴) | `from modules.system.api import DEFAULT_CURRENCY` |
| `"KRW"` (문자열 리터럴) | `from modules.system.api import CurrencyCode` |
| Magic numbers (5.0, 100.0 등) | 적절한 `config` 속성 또는 모듈 상수 |

### Goal C: Report Technical Debt Discovered
작업 중 발견된 기술 부채(타 모듈 결합, 프로토콜 위반, 레거시 패턴)를 기록합니다:
- 파일: `communications/insights/{module-key}.md`
- 형식: TD-ID | 위치 | 설명 | 영향도

## 4. Scope Assignment (Module Keys)

| Module Key | Source Path | Test Path | Priority |
| :--- | :--- | :--- | :--- |
| `mod-finance` | `modules/finance/` | `tests/unit/finance/`, `tests/unit/modules/finance/` | High |
| `mod-government` | `modules/government/` | `tests/unit/governance/`, `tests/unit/modules/government/` | High |
| `mod-household` | `modules/household/` | `tests/unit/household/`, `tests/unit/modules/household/` | High |
| `mod-market` | `simulation/markets/`, `modules/market/` | `tests/unit/markets/` | High |
| `mod-systems` | `simulation/systems/` | `tests/unit/systems/` | Med |
| `mod-agents` | `simulation/core_agents.py`, `simulation/firms.py` | `tests/unit/test_firms.py`, `tests/unit/test_household_*.py` | Med |
| `mod-decisions` | `simulation/decisions/` | `tests/unit/decisions/`, `tests/unit/corporate/` | Med |
| `mod-bank` | `simulation/bank.py` | `tests/unit/test_bank*.py` | Low |

## 5. Definition of Done (Per Module)
- [ ] `pytest tests/unit/{module_path} -v` 실행 결과 **ALL PASSED** 또는 **실패 원인 기록 완료**
- [ ] 하드코딩된 `"USD"` 리터럴 → `DEFAULT_CURRENCY` 교체 완료
- [ ] 발견된 기술 부채 → `communications/insights/{module-key}.md` 기록 완료
- [ ] 깨진 테스트 중 타 모듈 의존성 건은 insight 파일에 TD 후보로 기록

## 6. Verification Command
```bash
# 모듈별 테스트 실행
pytest tests/unit/{module_path} -v --tb=short

# 하드코딩 잔여 검색
grep -rn "'USD'" {source_path} {test_path}
```

## 7. Architectural Guardrails
- **Zero-Sum Integrity**: 테스트 수정 시 금전 흐름 로직 변경 금지.
- **Protocol Purity**: `hasattr()` → `isinstance()` 교체 우선.
- **DTO Purity**: raw dict 사용 발견 시 insight에 기록.
- **테스트 격리**: 유닛 테스트는 해당 모듈만 테스트. 타 모듈 Mock 사용 필수.
