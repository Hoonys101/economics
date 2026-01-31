# Tech Debt Liquidation (P-1)

**Date**: 2026-01-22
**Priority**: MEDIUM
**Status**: PENDING

---

## 🎯 Mission Objective

시뮬레이션 엔진의 안정성과 코드 순수성을 높이기 위해 남은 기술 부채 3종(TD-076, TD-077, TD-104)을 청산합니다.

---

## 📋 작업 세부 지침

### 1. [TD-104] Fixture Harvester 레거시 제거
**파일:** `scripts/fixture_harvester.py`
- `SimpleNamespace`를 사용하는 모든 폴백 로직을 제거합니다.
- `from tests.utils.golden_loader import GoldenLoader`를 사용하여 통합된 로더 기능을 활용하도록 수정합니다.
- `create_household_mocks`, `create_firm_mocks`, `create_config_mock` 메서드에서 `MagicMock`과 `GoldenLoader`의 기능을 사용하여 일관된 Mock 생성을 보장합니다.

### 2. [TD-077] EconComponent 설정 참조 최적화
**파일:** `modules/household/econ_component.py`
- `PRICE_MEMORY_LENGTH`와 `WAGE_MEMORY_LENGTH` 참조 시 중복된 타입 체크 및 `getattr` 폴백 로직을 제거하고, `self.config_module`에서 직접 또는 유틸리티 함수를 통해 깔끔하게 가져오도록 수정합니다.
- 하드코딩된 기본값(10, 30)을 제거하고 `config.py`의 값을 신뢰합니다.

### 3. [TD-076] Production TFP 계산 로컬라이징
**파일:** `simulation/components/production_department.py`
- `produce` 메서드에서 TFP 계산 시 `technology_manager`의 배율이 중복 적용될 여지가 있는지 다시 점검하고, 가장 명확한 단일 계산 지점을 확립합니다.
- 불필요한 중간 변수를 제거하여 가독성을 높입니다.

---

## ✅ 완료 조건

1. [ ] `fixture_harvester.py`에서 `SimpleNamespace` 임포트 및 사용이 완전히 제거됨.
2. [ ] `econ_component.py`의 설정 참조 로직이 1~2줄로 단순화됨.
3. [ ] 모든 기존 테스트(특히 `tests/test_corporate_manager.py`)가 통과함.
4. [ ] `TECH_DEBT_LEDGER.md`에서 해당 항목을 **RESOLVED**로 업데이트.

---

**Antigravity (Team Leader)**
