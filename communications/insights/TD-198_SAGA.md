# Insight: Multi-Tick Housing Saga & Lien System (TD-198, TD-195, TD-199)

- **Date**: 2026-02-03
- **Status**: FIXED
- **Mission**: Operation Atomic Time

## 1. 현상 (Phenomenon)
- 주택 거래가 틱 간 상태를 유지하지 못해 파산이나 데이터 불일치에 취약했음.
- `MortgageApplicationDTO` 필드 불일치(TD-198)와 Loan ID 타입 혼선(TD-195)으로 인한 기동성 저하.
- `SettlementSystem` 테스트 시 `MagicMock`이 `hasattr` 체크를 방해하여 거짓 양성(False Positive) 발생(TD-199).

## 2. 원인 (Cause)
- 초기 설계의 단순성 지향이 복잡한 다자간 거래(사가) 환경에서 한계에 도달함.
- 파편화된 API 개발로 DTO 명세가 중앙에서 관리되지 않음.

## 3. 해결 (Solution)
- **5단계 상태 머신**: INITIATED부터 TRANSFER_TITLE까지의 명시적 상태 전이 로직 구현.
- **Lien 시스템**: `RealEstateUnit`에 `liens: List[LienDTO]`를 도입하여 다중 담보 지원 및 하위 호환성 확보.
- **DTO 중앙화**: `modules/market/housing_planner_api.py`를 정본으로 하여 `MortgageApplicationDTO` 통일.
- **Mocking 정교화**: `spec` 인자를 사용하여 `MagicMock`의 속성 노출을 제한하여 `hasattr` 호환성 확보.

## 4. 교훈 (Lesson Learned)
- 복잡한 도메인(부동산 금융)은 초기부터 사가 패턴과 같은 분산 트랜잭션 설계를 고려해야 함.
- 데이터 모델과 서비스 인터페이스 간의 경계를 명확히 하고, DTO는 일관된 소스에서 관리되어야 함.

## 5. 추가 조치 (Test Coverage Expansion)
- **일자**: 2026-02-04
- **작업**: `tests/unit/systems/test_settlement_system.py` 전면 리팩토링 및 커버리지 확대.
    - **Saga Logic**: `submit_saga`, `process_sagas` (Liveness Check), `find_and_compensate_by_agent` (Compensation) 테스트 추가.
    - **Financial Logic**: `Seamless Payment` (Bank 연동), `Multiparty Settlement`, `Atomic Settlement` 테스트 추가.
    - **Inheritance**: `Portfolio` 자산의 상속(Heir) 및 국고 귀속(Escheatment) 시나리오 검증 완료.
- **발견된 기술 부채**:
    - `PortfolioAsset` 생성자 파라미터 불일치(`symbol` vs `asset_id`) 수정됨.
    - `tests/conftest.py`가 `simulation.agents.central_bank`를 임포트하며 `numpy` 의존성을 강제함. 이는 단위 테스트 환경 구성의 복잡도를 높임. 향후 Mock 객체로 대체하여 의존성을 끊어낼 필요가 있음.
