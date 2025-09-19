# 고급 디버깅 전략 제안

## 1. 문제 정의

현재 시뮬레이션은 복잡성이 높아지면서, 원인을 파악하기 어려운 버그(예: "기업 생산량 0" 문제)가 발생하고 있습니다. 이런 버그들은 여러 에이전트와 모듈의 상호작용에 걸쳐 발생하기 때문에, 기존의 선형적인 로그 분석만으로는 추적이 어렵습니다. 따라서 보다 체계적이고 효율적인 디버깅을 위해, 리팩토링을 통해 쉽게 적용할 수 있는 세 가지 고급 디버깅 전략을 제안합니다.

## 2. 제안 전략

### 전략 1: 구조화된 로깅 (Structured Logging) 도입

**- 현황 및 문제점**
현재 로그는 사람이 읽기 좋은 문자열 형태이지만, 특정 조건(예: 자산 100 이하, 생존 욕구 80 이상인 모든 가계)으로 로그를 필터링하고 분석하기 어렵습니다.

**- 해결 방안**
로그 메시지를 단순 문자열이 아닌, **JSON 형식의 구조화된 데이터**로 변경합니다. `log_config.json`에 `json` 포맷터를 추가하고, 로깅 시 `extra` 파라미터를 적극적으로 활용합니다.

**- 리팩토링 예시**
- **변경 전** (in `firms.py`):
  ```python
  self.logger.info(f"Starting production. Total labor skill: {total_labor_skill:.1f}, Number of employees: {len(self.employees)}")
  ```
- **변경 후** (in `firms.py`):
  ```python
  log_extra = {
      'event': 'production_start',
      'total_labor_skill': total_labor_skill,
      'employee_count': len(self.employees),
      'productivity_factor': self.productivity_factor
  }
  self.logger.info("Starting production", extra={**base_log_extra, **log_extra})
  ```

**- 기대 효과**
- `jq`와 같은 커맨드라인 도구나 Python 스크립트로 로그를 쉽게 필터링하고 집계할 수 있습니다.
- Grafana, ELK Stack 같은 로그 분석 플랫폼과 손쉽게 연동하여 대시보드를 구축할 수 있습니다.

### 전략 2: 상태 스냅샷 및 감사 (State Snapshotting & Auditing)

**- 현황 및 문제점**
특정 틱(tick)에서 에이전트의 상태가 왜 그렇게 변했는지 파악하려면, 이전 틱의 상태와 비교하며 로그를 역추적해야 하는 어려움이 있습니다.

**- 해결 방안**
1.  **`get_snapshot()` 메서드 구현**: `BaseAgent`에 에이전트의 모든 상태(자산, 욕구, 재고 등)를 `dict`로 반환하는 `get_snapshot()` 메서드를 추가합니다.
2.  **디버그 모드 추가**: `Simulation` 클래스에 `debug_mode` 플래그를 추가합니다. 이 모드가 활성화되면, 매 틱 종료 시 모든 에이전트의 상태 스냅샷을 별도의 로그 파일(예: `state_snapshots.jsonl`)에 저장합니다.
3.  **상태 비교(Diffing) 유틸리티 개발**: 두 개의 틱(tick) 번호를 입력받아, 해당 틱 사이의 모든 에이전트 상태 변화를 비교하여 보여주는 간단한 분석 스크립트를 작성합니다.

**- 기대 효과**
- "55틱에서 56틱으로 넘어갈 때, 왜 A 기업의 직원 수가 5명에서 0명이 되었는가?"와 같은 질문에 즉시 답을 찾을 수 있습니다.
- 특정 에이전트의 상태 변화를 시계열로 추적하여 버그의 근본 원인을 빠르게 파악할 수 있습니다.

### 전략 3: 단언문 기반 디버깅 (Assertion-Based Debugging)

**- 현황 및 문제점**
잘못된 상태가 발생하더라도 시스템이 즉시 멈추지 않고 계속 실행되다가, 나중에 예상치 못한 곳에서 오류가 발생하여 디버깅이 어려워집니다.

**- 해결 방안**
코드의 핵심적인 지점에 **시스템이 반드시 만족해야 하는 조건(불변성, Invariant)을 단언문(`assert`)으로 명시**합니다. 이는 "조용한 실패"를 "시끄러운 실패"로 바꾸어 버그를 발생 즉시 포착하게 합니다.

**- 리팩토링 예시**
- **`Firm.produce()` 메서드 상단**:
  ```python
  assert len(self.employees) > 0, f"Firm {self.id} has no employees at tick {current_time} before production."
  ```
- **`Simulation.run_tick()` 메서드 종료 직전**:
  ```python
  self._check_invariants()
  ```
- **`Simulation._check_invariants()` (신규 메서드)**:
  ```python
  def _check_invariants(self):
      # 예시: 모든 가계의 자산은 0 이상이어야 한다.
      for h in self.households:
          assert h.assets >= 0, f"Household {h.id} has negative assets: {h.assets}"
      # 예시: 고용된 가계는 반드시 employer_id를 가져야 한다.
      for h in self.households:
          if h.is_employed:
              assert h.employer_id is not None, f"Employed household {h.id} has no employer_id."
  ```

**- 기대 효과**
- 데이터가 오염되거나 잘못된 상태가 전파되기 전에, 문제 발생 즉시 실행을 중단시키므로 디버깅 범위가 크게 축소됩니다.
- 코드의 핵심 가정이 문서화되는 효과가 있어, 새로운 개발자가 코드를 이해하는 데 도움이 됩니다.

## 3. 결론

위 세 가지 전략은 서로 보완적이며, 함께 적용될 때 가장 큰 효과를 발휘합니다. 특히 **구조화된 로깅**과 **상태 스냅샷**은 데이터 기반의 정밀한 디버깅을 가능하게 하고, **단언문**은 잠재적인 버그를 조기에 발견하여 시스템의 안정성을 크게 향상시킬 것입니다. 이 전략들을 점진적으로 도입하여 프로젝트의 유지보수성과 개발 효율성을 높일 것을 제안합니다.
