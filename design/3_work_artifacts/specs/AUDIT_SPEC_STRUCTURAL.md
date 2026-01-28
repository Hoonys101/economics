# AUDIT_SPEC_STRUCTURAL: Structural Integrity Audit (v2.0)

**목표**: WO-103 이후 확립된 'DTO 기반 디커플링' 및 'Component SoC' 아키텍처가 실제 코드베이스에서 엄격히 준수되고 있는지 기술적으로 검증한다.

## 1. 용어 정의 (Terminology)
- **God Class**: 단일 클래스가 800라인 이상의 물리적 코드를 소유하거나, 분리 가능한 도메인 책임(예: 가계의 생존 로직과 주식 포트폴리오 로직)을 3개 이상 혼합하여 소유한 상태.
- **Leaky Abstraction (누출된 추상화)**: DTO(Data Transfer Object)를 사용해야 하는 구간(예: `DecisionContext`)에서 에이전트 객체(`Household`, `Firm`)의 인스턴스를 직접 전달하여 객체의 내부 상태를 외부 모듈에 노출시키는 행위.
- **Sacred Sequence (신성한 시퀀스)**: 시뮬레이션 틱 내에서 `Decisions -> Matching -> Transactions -> Lifecycle`로 이어지는 불변의 실행 순서.
- **Purity Gate**: 에이전트의 내부 필드(예: `_assets`)에 접근하기 위해 반드시 거쳐야 하는 프로퍼티 또는 컴포넌트 메서드.

## 2. 논리 전개 (Logical Flow)
1. **정적 스캔**: 파일 크기 및 클래스 메서드 개수를 파악하여 God Class 후보군을 식별한다.
2. **의존성 그래프 분석**: `import` 구문을 추적하여 순환 참조 및 `tests/` -> `simulation/` 과 같은 계층 위반을 탐색한다.
3. **인터페이스 검사**: `DecisionContext` 및 `make_decision` 호출부를 전수 조사하여 DTO 패턴 적용 여부를 확인한다.
4. **시퀀스 검증**: `tick_scheduler.py`와 `Simulation` 클래스의 `step` 메서드를 비교하여 시퀀스 우회 로직을 찾아낸다.

## 3. 구체적 방법 예시 (Concrete Examples)
- **위반 예시 (SoC Violation)**:
  ```python
  # BAD: DecisionContext에 household 객체 자체를 넘김
  context = DecisionContext(household=self, market_data=md)
  ```
- **준수 예시 (DTO Pattern)**:
  ```python
  # GOOD: snapshot(DTO)을 생성하여 전달
  dto = self.get_state_dto()
  context = DecisionContext(household_state=dto, market_data=md)
  ```
- **God Class 탐지**: `Firm` 클래스 내에 생산 로직, 마케팅 로직, 재무 로직이 모두 구현되어 있다면 이를 `ProductionDepartment`, `SalesDepartment` 등으로 분리할 것을 권고한다.

## 4. 구조적 모듈 현황 진단
- **메인 구조**: `Simulation` (Orchestrator) -> `System` (Logic) -> `Component` (State).
- **모듈 현황**: `modules/household/`, `modules/firm/` 내의 컴포넌트들이 각 지배 클래스로부터 얼마나 독립적으로 테스트 가능한지 평가한다.
- **Util 현황**: `simulation/utils/` 내의 유틸리티들이 특정 도메인에 종속되어 구조적 결합도를 높이고 있지는 않은가?
