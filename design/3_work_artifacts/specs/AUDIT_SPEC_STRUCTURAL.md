# AUDIT_SPEC_STRUCTURAL: Structural Integrity Audit (v3.0)

**목표**: 이후 확립된 'DTO 기반 디커플링' 및 'Component SoC' 아키텍처가 실제 코드베이스에서 엄격히 준수되고 있는지 **정적(Static) 분석**으로 검증한다.

**관심사 경계 (SoC Boundary)**:
> 이 감사는 오직 **"코드가 어떻게 조직되어 있는가 (Static Architecture)"**만을 다룬다.
> - ✅ God Class 탐지 (라인 수 + 메서드 수 + 책임 수)
> - ✅ Import-level 의존성 분석 (정적 결합도)
> - ✅ Interface/Protocol 준수 여부 (DTO 패턴, Protocol Evasion)
> - ✅ WorldState 순수성 (서비스 인스턴스 보유 여부)
> - ✅ Phase 시퀀스 무결성
> - ❌ 런타임 순환 참조 / GC 분석 → `AUDIT_MEMORY_LIFECYCLE`
> - ❌ 설계 문서와의 정합성 → `AUDIT_PARITY`
> - ❌ 테스트의 Mock 패턴 → `AUDIT_TEST_HYGIENE`

## 1. 용어 정의 (Terminology)
- **God Class**: 단일 클래스가 800라인 이상의 물리적 코드를 소유하거나, public 메서드가 15개를 초과하거나, 분리 가능한 도메인 책임을 3개 이상 혼합하여 소유한 상태.
- **Leaky Abstraction (누출된 추상화)**: DTO(Data Transfer Object)를 사용해야 하는 구간에서 에이전트 객체의 인스턴스를 직접 전달하여 객체의 내부 상태를 외부 모듈에 노출시키는 행위.
- **Sacred Sequence (신성한 시퀀스)**: 시뮬레이션 틱 내에서 `Decisions -> Matching -> Transactions -> Lifecycle`로 이어지는 불변의 실행 순서.
- **Purity Gate**: 에이전트의 내부 필드에 접근하기 위해 반드시 거쳐야 하는 프로퍼티 또는 컴포넌트 메서드.
- **Protocol Evasion**: `hasattr()` / `isinstance()` 등으로 Protocol 인터페이스를 우회하여 타입 안전성을 무시하는 코드 패턴.

## 2. Severity Scoring Rubric

| Severity | 기준 | 예시 |
| :--- | :--- | :--- |
| **Critical** | Sacred Sequence 우회 또는 SSoT 위반 | Phase 외부에서 직접 settlement 호출 |
| **High** | God Class (800줄+ 또는 15+ public 메서드) | `Firm` 1800줄, 생산+마케팅+재무 혼합 |
| **Medium** | Protocol Evasion 또는 추상화 누출 | `hasattr(agent, 'hr_state')` 사용 |
| **Low** | 경미한 결합도 (역방향 import 1건 등) | `utils/` → 특정 도메인 종속 |

## 3. 논리 전개 (Logical Flow)
1. **정적 스캔**: 파일 크기, 클래스 메서드 개수, public 메서드 수를 파악하여 God Class 후보군을 식별한다.
2. **의존성 그래프 분석**: `import` 구문을 추적하여 `tests/` -> `simulation/` 과 같은 계층 위반을 탐색한다.
3. **인터페이스 검사**: `DecisionContext` 및 `make_decision` 호출부를 전수 조사하여 DTO 패턴 적용 여부를 확인한다.
4. **Protocol Evasion 탐지**: `grep -rn "hasattr\|isinstance" simulation/` 결과에서 Protocol 우회 패턴을 식별한다.
5. **시퀀스 검증**: `tick_scheduler.py`와 `Simulation` 클래스의 `step` 메서드를 비교하여 시퀀스 우회 로직을 찾아낸다.
6. **WorldState 순수성 검증**: `WorldState.__init__`에서 Service 클래스를 직접 인스턴스화하고 보유하는 "God Class Incursion" 패턴을 탐지한다.
7. **정량적 Coupling Matrix**: 모듈 간 import 횟수를 행렬로 산출하여 결합도 핫스팟을 시각화한다.

## 4. 구체적 방법 예시 (Concrete Examples)
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

## 5. 구조적 모듈 현황 진단
- **메인 구조**: `Simulation` (Orchestrator) -> `System` (Logic) -> `Component` (State).
- **모듈 현황**: `modules/household/`, `modules/firm/` 내의 컴포넌트들이 각 지배 클래스로부터 얼마나 독립적으로 테스트 가능한지 평가한다.
- **Util 현황**: `simulation/utils/` 내의 유틸리티들이 특정 도메인에 종속되어 구조적 결합도를 높이고 있지는 않은가?

## 6. Output Configuration
- **Output Location**: `reports/audit/`
- **Recommended Filename**: `AUDIT_REPORT_STRUCTURAL.md`
