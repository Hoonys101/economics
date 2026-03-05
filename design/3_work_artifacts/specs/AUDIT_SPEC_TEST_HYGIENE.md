# AUDIT_SPEC_TEST_HYGIENE: Test Hygiene Audit (v1.0)

**목표**: 테스트 인프라의 품질과 신뢰성을 검증하여, Mock 드리프트·커버리지 사각지대·fixture 비대화 등이 프로덕션 코드의 안정성을 잠식하는 것을 방지한다.

**관심사 경계 (SoC Boundary)**:
> 이 감사는 오직 **"테스트가 신뢰할 수 있는가 (Test Trustworthiness)"**만을 다룬다.
> - ✅ Mock 품질 (bare mock, spec 미적용, stale attribute)
> - ✅ DTO 대체 Mock anti-pattern
> - ✅ 커버리지 사각지대 (테스트 디렉토리 부재)
> - ✅ Fixture 조직 (conftest 비대화)
> - ✅ Teardown 위생 (setUp 있으나 tearDown 없음)
> - ✅ 검증용 유틸리티의 동기화 상태
> - ❌ 프로덕션 코드의 구조 → `AUDIT_STRUCTURAL`
> - ❌ 화폐 계산 정확성 → `AUDIT_ECONOMIC`
> - ❌ 런타임 메모리 누수 → `AUDIT_MEMORY_LIFECYCLE`

## 1. 용어 정의 (Terminology)
- **Bare Mock**: `spec=` 인자 없이 생성된 `MagicMock()`. 모든 속성을 묵인(silently absorb)하여 Mock Drift를 유발.
- **Mock Drift**: 프로덕션 인터페이스가 변경되었으나 Mock이 구 인터페이스를 반영하여, 테스트가 통과하지만 프로덕션에서 실패하는 현상.
- **DTO Substitution Anti-Pattern**: 실제 DTO/dataclass 대신 `MagicMock`을 반환하여, 타입 검사 및 스키마 검증을 우회하는 fixture 패턴.
- **Stale Fixture**: 더 이상 사용되지 않거나 deprecated된 속성을 설정하는 fixture.

## 2. Severity Scoring Rubric

| Severity | 기준 | 예시 |
| :--- | :--- | :--- |
| **Critical** | 핵심 시스템의 테스트가 전무 | `modules/finance/` 에 대응하는 test 디렉토리 없음 |
| **High** | Bare Mock이 핵심 인터페이스에 사용됨 | `MagicMock()` for `ISettlementSystem` |
| **Medium** | DTO Substitution 또는 Stale Fixture | `fixture`가 deprecated `system_command_queue` 설정 |
| **Low** | conftest.py 비대화 (fixture > 30개) | 도메인별 분리 권고 |

## 3. 감사 범위 (Audit Scope)

### 3.1 Mock 품질 감사
- **탐지**: `grep -rn "MagicMock()" tests/` (spec= 미적용 Mock)
- **검증**: 각 Bare Mock의 target 인터페이스를 식별하고, `spec=<Interface>` 적용 권고.
- **Stale Attribute 탐지**: Mock에 설정된 속성명이 실제 Protocol/Interface에 존재하는지 교차 확인.

### 3.2 DTO Substitution 감사
- **탐지**: fixture가 `MagicMock`을 반환하는데, 해당 반환값이 DTO 타입으로 기대되는 곳에 사용되는 경우.
- **권고**: `@dataclass` 인스턴스 또는 `factory_boy` 패턴으로 전환.

### 3.3 커버리지 사각지대 감사
- **방법**: `modules/` 하위 모든 시스템 디렉토리를 열거하고, 대응하는 `tests/unit/` 디렉토리의 존재 여부를 확인.
- **보고**: 테스트 디렉토리가 없는 모듈을 "Coverage Blind Spot"으로 등재.

### 3.4 Fixture 조직 감사
- **conftest 비대화**: root `conftest.py`의 fixture 수가 30개를 초과하면, 도메인별 `conftest.py` 분리 권고.
- **Teardown 위생**: `setUp`/`setUpClass`가 있으나 `tearDown`/`addCleanup`이 없는 테스트 클래스를 탐지.

### 3.5 검증 유틸리티 동기화 감사
- **대상**: `verify_inheritance.py`, `scripts/iron_test.py` 등 검증용 모듈.
- **검증**: 이들이 프로덕션 코드의 최근 리팩토링을 반영하고 있는가?

## 4. Output Configuration
- **Output Location**: `reports/audit/`
- **Recommended Filename**: `AUDIT_REPORT_TEST_HYGIENE.md`
