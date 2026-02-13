# Specification: Government Module Decomposition (FOUND-02)

**Status**: Draft (Scribe)  
**Version**: 1.0.0  
**Mission Key**: FOUND-02-GOV-DECOMP  
**Related Docs**: [GODMODE-WATCHTOWER-EXECUTION](../../../reports/audits/GODMODE_EXECUTION_ROADMAP.md), [SEO_PATTERN.md](../../../design/1_governance/architecture/standards/SEO_PATTERN.md)

---

## 1. 개요 (Objective)
본 명세는 `Government` 모듈의 거대 객체(God Class)를 해체하여 관심사를 분리하고, 확장성과 테스트 용이성을 확보하는 것을 목표로 합니다. 특히 `TaxService`, `WelfareService`, `FiscalBondService`를 독립된 서비스로 추출하고, `Government` 클래스는 이를 총괄하는 오케스트레이터 역할로 축소합니다.

---

## 2. 시스템 아키텍처 (Architecture Overview)

### 2.1 분리 구조 (Decomposition Structure)
- **Government (Orchestrator)**: 예산 편성, 정책 기조 결정, 하위 서비스 호출 및 상태 동기화. (800라인 미만 유지)
- **TaxService (Stateless Engine)**: 소득세/법인세 계산 로직, 세수 징수 트랜잭션 생성.
- **WelfareService (Stateless Engine)**: 복지 수급 자격 판별, 보조금 지급 트랜잭션 생성.
- **FiscalBondService (Stateless Engine)**: 국채 발행, 수익률(Yield) 계산, 부채 상환 관리.

### 2.2 의존성 구조 (DI & Protocols)
- 모든 서비스는 `ISettlementSystem`, `IGlobalRegistry`, `IAnalyticsProvider` 프로토콜에 의존합니다.
- 순환 참조 방지를 위해 서비스 생성 시에는 프로토콜만 참조하며, 실제 객체는 `Simulation` 초기화 단계에서 주입됩니다.

---

## 3. 인터페이스 명세 (Interface Specification)

### 3.1 DTO 정의 (`modules/government/dtos.py`)

```python
class TaxPolicyDTO(TypedDict):
    income_tax_brackets: List[Dict[str, int]]  # Pennies (TD-278)
    corporate_tax_rate: float
    vat_rate: float

class FiscalContextDTO(TypedDict):
    current_gdp: int # Pennies
    debt_to_gdp_ratio: float
    population_count: int
    treasury_balance: int # Pennies

class BondIssueRequestDTO(TypedDict):
    amount_pennies: int
    maturity_ticks: int
    target_yield: float
```

### 3.2 서비스 인터페이스 (`modules/government/api.py`)

```python
class ITaxService(Protocol):
    def calculate_tax(self, income_pennies: int, policy: TaxPolicyDTO) -> int: ...
    def collect_taxes(self, agents: List[FinancialEntity], context: FiscalContextDTO) -> List[TransactionRequest]: ...

class IFiscalBondService(Protocol):
    def calculate_yield(self, context: FiscalContextDTO) -> float: ...
    def issue_bonds(self, request: BondIssueRequestDTO, context: FiscalContextDTO) -> TransactionRequest: ...
```

---

## 4. 로직 설계 (Logic Flow & Pseudo-code)

### 4.1 Tax Collection (Phase 3: Settlement)
1. `Government`가 `Analytics`로부터 `FiscalContextDTO`를 수집.
2. `TaxService`에 징수 대상 에이전트 목록과 컨텍스트 전달.
3. `TaxService`는 각 에이전트의 `Taxable Income`을 검증(TD-277).
4. `Penny Standard`를 준수하여 소수점 버림 처리된 세액 계산.
5. `SettlementSystem`으로 전달할 `TransactionRequest` 리스트 반환.

### 4.2 Bond Issuance (Phase 0: Intercept / Phase 4: Expansion)
1. `Government`가 예산 부족(Deficit) 감지.
2. `FiscalBondService`가 `debt_to_gdp_ratio` 기반 위험 프리미엄이 반영된 수익률 계산(TD-FIN-004).
3. `GodCommand`를 통해 `Phase 0`에서 국채 발행 파라미터가 수정되었는지 확인.
4. 국채 발행 및 시장 매도 트랜잭션 생성.

---

## 5. 예외 처리 (Exception Handling)

- **Solvency Risk**: 복지 예산 집행 시 Treasury 잔액 부족 시 `GovernmentInsolvencyError` 발생 및 우선순위(1. 생계급여, 2. 실업급여)에 따른 차등 지급 로직 실행.
- **Type Mismatch**: `Pennies` 단위가 아닌 `float` 입력 시 `SettlementTypeError`를 사전에 방지하기 위한 `int()` 강제 형변환 유효성 검사 계층 추가.
- **Race Condition**: `Analytics` 데이터가 최신이 아닐 경우(Stale Data), `FiscalContext` 내부에 `tick_id`를 포함하여 정합성 검증.

---

## 6. 리스크 및 영향도 감사 (Risk & Impact Audit)

- **Circular Dependency**: `Government` ↔ `SettlementSystem` 간의 직접 참조를 제거하고, `ISettlementSystem` 프로토콜을 통한 메시지 전달로 구조 변경 필수.
- **Data Definition Drift (TD-277)**: '과세 대상 소득'의 정의가 `Firm.profit`과 `Household.income`에서 일치하지 않을 위험. `AccountingStandard` 클래스를 신설하여 이를 통제해야 함.
- **Performance**: 대규모 에이전트 세금 계산 시 루프 오버헤드 발생 가능. `TaxService`는 내부적으로 NumPy 벡터 연산을 사용하도록 설계 권장.
- **Zero-Sum Integrity**: 국채 발행 및 이자 지급 시 '생성된 돈(Magic Money)'이 `SettlementSystem`의 감사(Audit)를 통과하는지 반드시 확인해야 함.

---

## 7. 검증 및 테스트 전략 (Verification Strategy)

### 7.1 단위 테스트 (Unit Tests)
- `test_tax_bracket_calculation`: 다양한 소득 구간에 대한 `TaxService`의 정확성 검증 (Penny 단위).
- `test_bond_yield_curve`: 부채 비율 증가에 따른 수익률 상승 로직 검증.
- `test_government_orchestrator_lines`: `Government.py`가 800라인을 초과하지 않는지 정적 분석.

### 7.2 통합 및 골든 데이터 테스트
- `scripts/fixture_harvester.py`를 사용하여 `golden_government_state`를 생성하고, 리팩토링 전후의 세수 총액이 일치하는지 비교.
- `SimulationConfig`에 신규 필드(`tax_policy`, `bond_parameters`) 추가 여부 확인.

---

## 8. Mandatory Reporting Verification

본 설계 과정에서 식별된 아키텍처적 인사이트와 기술 부채(TD-277, TD-278 해결 방안 등)는 다음 파일에 독립적으로 기록되었습니다.
- **인사이트 보고서**: `communications/insights/FOUND_02_GOV_DECOMP_INSIGHTS.md`

> **Scribe's Note**: 정부 모듈의 해체는 단순한 코드 분리가 아닌, 국가 재정 시스템을 '예측 가능한 서비스'로 전환하는 공정입니다. `Penny Standard`와 `Zero-Sum` 원칙을 한 치의 오차 없이 적용하십시오.