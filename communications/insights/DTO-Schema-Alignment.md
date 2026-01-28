# Insight Report: DTO Schema Alignment & API Centralization

## 현상 (Phenomenon)
- 이전에는 모듈의 공개 인터페이스(특히 DTO)가 `simulation/dtos/api.py`와 같이 하위 디렉토리에 분산되어 있었습니다.
- 이로 인해 외부 모듈이 `simulation` 패키지의 어떤 부분을 사용해야 하는지 파악하기 위해 여러 파일을 확인해야 하는 불편함이 있었습니다.

## 원인 (Cause)
- 초기 개발 과정에서 기능별로 파일을 구성했으나, 패키지 전체의 통합된 Public API 관점에서의 관리가 부족했습니다.
- 모듈의 "공식적인 계약"이 여러 곳에 흩어져 있어 API의 경계가 모호해졌습니다.

## 해결 (Solution)
- `HouseholdConfigDTO`, `FirmStateDTO`, `DecisionContext` 등 외부에서 사용되는 모든 DTO를 `simulation/api.py` 파일로 이전하고 통합했습니다.
- `__all__` 변수를 통해 패키지에서 명시적으로 노출하는 대상을 정확하게 관리하여, `simulation/api.py`가 이 모듈의 유일한 공식 진입점(Single Source of Truth)이 되도록 만들었습니다.

## 교훈 (Lesson Learned)
- **API-Driven Development**: 모듈의 Public API는 단일 `api.py` 파일에서 관리하는 것이 모듈의 경계를 명확히 하고, 유지보수성과 발견가능성을 크게 향상시킵니다.
- **중앙화된 계약**: 외부와 상호작용하는 모든 데이터 구조(DTOs)와 클래스를 `api.py`에 집중시키는 것은, 의존성 관리를 단순화하고 의도치 않은 내부 구현 접근을 방지하는 효과적인 아키텍처 패턴입니다.
