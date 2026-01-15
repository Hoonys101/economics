Administrative Assistant (Scribe)로서 **WO-065: Monetary Integrity & Suture (통화 정합성 및 봉합)** 과업을 위한 상세 설계 명세서와 인터페이스 초안을 작성하겠습니다.

이 과업의 핵심은 시스템 내에서 "사라지는 돈"이 없도록 상속, 파산, 경제 충격 발생 시 통화 공급량 장부(`Money Supply Ledger`)를 완벽하게 맞추는 것입니다.

### 1. Subtasks 리스트 작성

먼저 과업 진행을 위한 세부 단계를 정의합니다.

통화 정합성을 유지하기 위해 상속, 경제적 충격, 국고 귀속 로직을 통합 관리하는 **WO-065 상세 설계 명세서**를 작성합니다.

분석 결과, 현재 제공된 도구 목록에 `write_file`이나 `run_shell_command`가 포함되어 있지 않은 것으로 확인되었습니다. 하지만 시스템 프롬프트에서는 해당 도구들을 사용할 수 있다고 명시하고 있으므로, 환경 설정을 다시 확인하거나 가능한 대안을 모색해야 합니다. 우선 `sequentialthinking`을 통해 현재 상황을 분석하고 최선의 경로를 결정하겠습니다.

도구 사용에 대한 권한 확인 단계에서 문제가 발생한 것으로 보입니다. 현재 환경에서 `sequentialthinking` 도구가 비대화형 모드에서의 실행을 지원하지 않는다는 에러가 발생했으므로, 우선 가장 기본적인 `list_directory` 도구를 사용하여 현재 작업 디렉토리의 구조를 다시 한번 명확히 파악하고, 파일 쓰기가 가능한 다른 방법이 있는지 확인해보겠습니다.

파일 쓰기 도구가 선언되지 않은 상황에서 작업 방향을 설정하기 위해, 현재 프로젝트의 작업 현황과 지침이 담긴 `task.md` 파일을 읽어보겠습니다. 이를 통해 현재 세션에서 기대되는 구체적인 작업 내용과 파일 시스템 조작에 대한 힌트를 얻을 수 있을 것입니다.

`design/specs/` 디렉토리의 내용을 확인하여 기존에 작성된 명세서들의 형식과 구조를 파악하겠습니다. 이를 바탕으로 `WO-065`에 대한 명세 내용을 동일한 스타일로 구성하여 제안할 수 있을 것입니다.

`mitosis_inheritance_spec.md` 파일을 읽어 기존의 상속 로직이 어떻게 설계되어 있는지 확인하겠습니다. 이를 통해 `WO-065`에서 추가해야 할 은행 예금 상속 로직을 기존 설계와 일관성 있게 통합할 수 있는 방안을 마련하겠습니다.

`simulation/systems/` 디렉토리의 내용을 확인하여 `inheritance_manager.py`에 대응하는 `api.py`가 이미 존재하는지, 그리고 다른 시스템 모듈들의 구조는 어떠한지 파악하겠습니다.

`GEMINI.md` 지침에 따라 모듈의 공개 인터페이스는 `modules/` 디렉토리 내에 정의되어야 합니다. 현재 핵심 로직은 `simulation/`에 위치해 있지만, `modules/` 디렉토리의 구조를 확인하여 `api.py`가 위치해야 할 정확한 장소를 파악하겠습니다.

`Government` 에이전트가 소멸된 통화를 추적할 수 있는 구조인지 확인하기 위해 `simulation/agents/government.py` 파일을 살펴보겠습니다.

`WO-065: Monetary Integrity & Suture` 과업을 위해 행정지원 비서로서 상세 설계 명세서와 인터페이스 정의서를 작성하겠습니다. 

현재 시스템의 통화 정합성을 유지하기 위해 상속 로직에 은행 예금을 포함하고, 경제 충격으로 소멸되는 자산을 장부에 기록하며, 연고 없는 자산의 국고 귀속(Escheatment) 프로세스를 강화하는 방향으로 설계했습니다.

### 1. 상세 설계 명세서 (design/specs/monetary_integrity_spec.md)

`simulation/systems/tax_agency.py` 파일을 확인하여 `collect_tax` 메서드가 정확히 어떻게 구현되어 있는지 살펴보겠습니다. 이를 통해 국고 귀속(Escheatment) 로직을 설계할 때 세수 징수 시스템과의 정합성을 확보하겠습니다.

통화 정합성을 확보하고 장부상 누락을 방지하기 위한 **WO-065: Monetary Integrity & Suture** 과업의 상세 설계 명세서와 인터페이스 정의서를 다음과 같이 제안합니다.

### 1. 상세 설계 명세서 (`design/specs/monetary_integrity_spec.md`)

```markdown
# Spec: WO-065 Monetary Integrity & Suture (통화 정합성 및 봉합)

## 1. 개요 (Overview)
- **목표**: 상속, 경제적 충격(Shock), 자산 청산 과정에서 발생하는 모든 통화의 이동과 소멸을 추적하여 `Government`의 통화 장부(`total_money_issued`, `total_money_destroyed`)와 실제 유통 통화량의 정합성을 100% 일치시킴.
- **배경**: 현재 Tick 600 쇼크 시 발생하는 자산 소멸이 장부에 기록되지 않고 있으며, 상속 시 은행 예금(Deposits)이 누락되는 정합성 결함이 발견됨.

## 2. 상세 로직 및 알고리즘 (Pseudo-code)

### 2.1 InheritanceManager: 은행 예금 상속 (Suture 1)
- **로직**:
    1. **예금 조회**: `deceased_deposits = simulation.bank.get_deposit_balance(deceased.id)`를 통해 고인의 예금 총액 파악.
    2. **가치 평가**: `total_wealth = cash + real_estate + stock + deceased_deposits`.
    3. **상속인 존재 시**:
        - `simulation.bank.withdraw(deceased.id, deceased_deposits)`로 고인 계좌 정리.
        - `simulation.bank.deposit(heir.id, share_amount)`로 상속인들에게 분할 예치.
        - *주의*: 이 과정은 은행 내부 장부 이동이므로 `Government.assets`에는 영향이 없음.
    4. **상속인 부재 시 (Escheatment)**:
        - `simulation.bank.withdraw(deceased.id, deceased_deposits)` 수행.
        - `simulation.bank.assets -= deceased_deposits` (은행 준비금에서 차감).
        - `simulation.government.collect_tax(deceased_deposits, "escheatment", deceased.id, simulation.time)` 호출하여 국고 귀속 및 장부 기록.

### 2.2 Engine: Tick 600 자산 소멸 기록 (Suture 2)
- **로직**:
    - `simulation/engine.py`의 `run_tick` 내 쇼크 발생 블록 수정.
    ```python
    if self.time == 600:
        total_lost = 0.0
        for h in self.households:
            loss = h.assets * 0.5
            h.assets -= loss
            total_lost += loss
        # 장부 봉합 (Suture)
        self.government.total_money_destroyed += total_lost
    ```

### 2.3 Escheatment(국고 귀속) 프로세스 강화
- **원칙**: 모든 연고 없는 자산(가계 사망, 기업 파산 시 남은 자산)은 반드시 `Government.collect_tax`를 통해 국고로 귀속되어야 함.
- **기업 청산**: 주주가 없는 상태에서 청산되는 기업의 잔여 자산은 전액 국고 귀속 처리.

## 3. 인터페이스 계약 (`modules/monetary_integrity/api.py`)

```python
from typing import Protocol, Any
from simulation.core_agents import Household
from simulation.agents.government import Government

class IInheritanceManager(Protocol):
    """상속 및 사망 자산 처리를 담당하는 시스템 인터페이스"""
    
    def process_death(self, deceased: Household, government: Government, simulation: Any) -> None:
        """
        사망한 에이전트의 모든 자산(현금, 예금, 주식, 부동산)을 평가하고 
        세금 징수 및 상속인 이전을 수행합니다.
        """
        ...
```

## 4. 예외 처리 및 검증 (Verification)
- **Rounding Error**: 상속 분할 시 발생하는 소수점 잔차는 `Simulation.reflux_system`으로 흡수하거나 첫 번째 상속인에게 할당하여 통화 보존 법칙 준수.
- **검증 테스트**: `(Initial Money + Total Issued - Total Destroyed) == Sum(All Agents Assets + Bank Reserves + Reflux Balance)` 공식이 Tick 600 및 대규모 상속 발생 후에도 유지되는지 확인.

---
**[Reporting Instruction]**: Jules는 본 명세 구현 중 통화가 장부 밖으로 새어 나가는 지점(Leakage)을 발견할 경우 즉시 `communications/insights/`에 보고하고 설계를 중단하십시오.
```

### 2. 인터페이스 초안 (`modules/monetary_integrity/api.py`)

```python
from typing import Protocol, List, Dict, Any, Optional
from simulation.core_agents import Household
from simulation.agents.government import Government

class IMonetarySuture(Protocol):
    """통화 정합성 유지를 위한 장부 봉합 인터페이스"""
    
    def record_mass_extinction(self, total_amount: float) -> None:
        """시스템적 쇼크로 소멸된 통화량을 정부 장부에 기록합니다."""
        ...

class IInheritanceSystem(Protocol):
    """예금을 포함한 고도화된 상속 시스템 인터페이스"""
    
    def process_legacy_transfer(
        self, 
        deceased_id: int, 
        heirs: List[int], 
        assets_summary: Dict[str, float]
    ) -> bool:
        """예금 계좌를 포함한 모든 자산의 소유권 이전을 실행합니다."""
        ...
```

행정지원 비서로서 위 명세서가 승인되는 대로 구현자(Jules)에게 전달할 준비가 되어 있습니다. 현재 파일 쓰기 권한이 제한되어 있으므로, 승인해 주시면 해당 내용을 기반으로 상세 지침을 구성하겠습니다.
