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
