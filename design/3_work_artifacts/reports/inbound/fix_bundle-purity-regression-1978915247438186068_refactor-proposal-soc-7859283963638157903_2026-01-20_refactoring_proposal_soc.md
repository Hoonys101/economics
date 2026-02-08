# SoC(관심사 분리) 기반 리펙토링 제안서

**날짜:** 2026년 1월 20일
**작성:** Jules (Observer)

## 1. 개요 (Executive Summary)
본 보고서는 `simulation` 모듈 내에서 **관심사 분리(SoC, Separation of Concerns)** 원칙을 위반하고 있는 주요 "God Class"를 식별하고, 이에 대한 구체적인 리펙토링 방안을 제안합니다. 분석 결과 **`Household`**, **`Firm`**, **`TickScheduler`** 클래스가 가장 시급한 개선 대상으로 확인되었습니다. 제안된 리펙토링은 코드의 유지보수성, 테스트 용이성, 확장성을 확보하는 것을 목표로 합니다.

## 2. 분석 방법 (Methodology)
- **정량적 분석:** Python `ast` 모듈을 활용하여 클래스별 라인 수(LOC)와 메서드 수를 측정했습니다.
- **정성적 분석:** 각 클래스의 책임(Responsibility), 의존성(Dependency), 응집도(Cohesion)를 검토했습니다.
- **대상 범위:** `simulation/` 디렉토리 전체.

### 주요 "God Class" 식별 결과
| 클래스명 | LOC | 메서드 수 | 파일 위치 | 주요 문제점 |
|---|---|---|---|---|
| **Household** | 820 | 123 | `core_agents.py` | 압도적인 메서드 수(123개). 생물학, 경제, 사회, 의사결정 로직이 한 클래스에 뒤엉켜 있음. |
| **Firm** | 528 | 30 | `firms.py` | 기업의 모든 활동(생산, 재무, 인사, 전략)을 단일 클래스에서 처리. 높은 복잡도. |
| **TickScheduler** | 620 | 3 | `tick_scheduler.py` | 메서드 수는 적으나 LOC가 높음. 이는 "Long Method" 안티 패턴으로, 시뮬레이션의 모든 단계가 절차적 코드로 나열됨. |

---

## 3. 상세 분석 및 리펙토링 제안

### 3.1. 대상: `Household` (가계 에이전트)
**현황 (Current State):**
- **위치:** `simulation/core_agents.py`
- **혼재된 책임:**
  - **생물학적(Biological):** 나이, 건강, 배고픔, 사망, 자녀 출산.
  - **경제적(Economic):** 노동, 임금 수령, 소비, 자산 관리, 은행 거래.
  - **사회적(Social):** 정치 성향, 인맥 관리, 사회적 지위.
  - **의사결정(Decision):** 취업 결정, 소비 결정 (DecisionEngine이 있지만 상태값은 Household에 혼재).
- **문제점:** 123개의 메서드는 단일 책임 원칙(SRP)을 심각하게 위반하며, 특정 로직(예: 노화) 수정이 전혀 다른 로직(예: 재정)에 사이드 이펙트를 줄 위험이 큼.

**제안: 컴포넌트-엔티티 시스템 (Component-Entity System)**
`Household`를 껍데기(Shell) 클래스로 만들고, 구체적인 기능은 별도의 컴포넌트로 위임합니다.

**설계안:**
```python
class Household(BaseAgent):
    def __init__(self):
        self.bio = BiologicalComponent(self)   # 나이, 건강, 욕구(Needs)
        self.econ = EconomicComponent(self)    # 지갑, 직업, 자산, 세금
        self.social = SocialComponent(self)    # 인맥, 정치 성향
        self.brain = DecisionEngine(self)      # 의사결정 로직
```
**실행 단계:**
1. `BiologicalComponent` 추출: `age`, `health`, `consume_food()`, `die()` 등 이동.
2. `EconomicComponent` 추출: `money`, `assets`, `receive_wage()`, `pay_tax()` 등 이동.
3. `SocialComponent` 추출: `friends`, `political_view` 관련 로직 이동.

---

### 3.2. 대상: `Firm` (기업 에이전트)
**현황 (Current State):**
- **위치:** `simulation/firms.py`
- **혼재된 책임:**
  - **생산(Production):** 자동화 레벨, 생산성, 재고 관리.
  - **인사(HR):** 채용, 해고, 임금 책정, 직원 목록 관리.
  - **재무(Finance):** 대출, 파산 처리, 배당금, 주식 발행.
  - **영업(Sales):** 가격 책정, 마케팅.
- **문제점:** 해고 로직(HR)이 현금(Finance)과 생산량(Production)을 직접 조작하는 등 결합도가 매우 높음.

**제안: 부서 기반 아키텍처 (Departmental Architecture)**
실제 기업 조직처럼 부서(Department) 객체에게 책임을 위임합니다.

**설계안:**
```python
class Firm(BaseAgent):
    def __init__(self):
        self.hr = HRDepartment(self)           # 직원 관리, 임금, 채용/해고
        self.finance = FinanceDepartment(self) # 현금 흐름, 대출, 주식
        self.production = ProductionDept(self) # 재고, 기술, 생산량 계산
        self.sales = SalesDepartment(self)     # 판매, 가격 결정
```
**실행 단계:**
1. `HRDepartment` 신설 및 `employees` 리스트 관리 이관.
2. `ProductionDepartment` 신설 및 `production_function` 로직 이관.
3. 기존 `FinanceDepartment`의 역할을 확대하여 재무 로직 완전 통합.

---

### 3.3. 대상: `TickScheduler` (시뮬레이션 스케줄러)
**현황 (Current State):**
- **위치:** `simulation/tick_scheduler.py`
- **책임:** 시뮬레이션 루프 제어, 에이전트 호출 순서 관리, 데이터 수집, 시장 업데이트.
- **문제점:** `run_tick` 메서드 내부에 수백 줄의 절차적 코드가 존재하여, 실행 흐름을 파악하거나 순서를 변경하기 매우 어려움.

**제안: 페이즈 기반 스케줄러 (Phase-Based Scheduler)**
하루(Tick)를 명확한 '단계(Phase)'로 나누고, 각 단계를 담당하는 객체나 메서드로 분리합니다.

**설계안:**
```python
class TickScheduler:
    def __init__(self):
        self.phases = [
            SetupPhase(),          # 초기화
            ProductionPhase(),     # 기업 생산
            LaborMarketPhase(),    # 채용/해고
            ConsumptionPhase(),    # 가계 소비
            FinancialMarketPhase(),# 금융 거래
            CleanupPhase()         # 데이터 집계 및 정리
        ]

    def run_tick(self):
        for phase in self.phases:
            phase.execute(self.world_state)
```

---

## 4. 기대 효과
1. **테스트 용이성 (Testability):** `Household` 전체를 생성하지 않고도 `BioComponent`나 `ProductionDept` 단위로 격리된 테스트가 가능해집니다.
2. **유지보수성 (Maintainability):** 특정 기능(예: 세금 계산 방식 변경) 수정 시, 관련된 컴포넌트(`EconomicComponent`)만 수정하면 되므로 사이드 이펙트가 최소화됩니다.
3. **확장성 (Extensibility):** 새로운 기능(예: 전염병 시스템) 추가 시 기존 코드를 건드리지 않고 새로운 컴포넌트만 부착하면 됩니다.
4. **협업 효율:** 여러 개발자가 서로 다른 컴포넌트/부서를 동시에 개발할 수 있습니다.

## 5. 결론
`Household`, `Firm`, `TickScheduler`의 리펙토링은 프로젝트의 기술 부채를 해소하고 장기적인 개발 속도를 높이기 위해 필수적입니다. 본 제안서의 SoC 전략을 통해 코드를 더 직관적이고 견고한 구조로 개선할 것을 권장합니다.