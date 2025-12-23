# Household.update_needs 구현 문제 트러블슈팅

## 1. 문제 인식 (Problem Recognition)

시뮬레이션 실행 중 `TypeError: Can't instantiate abstract class Household without an implementation for abstract method 'update_needs'` 오류가 발생하여 `Household` 클래스를 인스턴스화할 수 없습니다. 이는 `Household` 클래스가 `BaseAgent`로부터 상속받은 추상 메서드인 `update_needs`를 제대로 구현하지 않았다고 파이썬 런타임이 판단하고 있음을 의미합니다.

## 2. 확인 방법 (Verification Method)

`python run_experiment.py` 명령을 실행할 때 시뮬레이션 초기화 단계에서 위 `TypeError`가 발생하며 프로그램이 종료됩니다.

## 3. 현재까지의 분석 (Current Analysis)

*   `Household` 클래스는 `simulation/base_agent.py`에 정의된 `BaseAgent` 클래스를 상속받습니다.
*   `BaseAgent` 클래스는 `update_needs` 메서드를 `@abstractmethod`로 명시하여 추상 메서드로 정의하고 있습니다.
*   `simulation/core_agents.py` 파일 내 `Household` 클래스에는 `update_needs` 메서드가 정의되어 있습니다. 그러나 파이썬 런타임은 이 메서드를 `BaseAgent`의 추상 메서드에 대한 유효한 구현으로 인식하지 못하고 있습니다.
*   **가설:**
    *   `Household.update_needs` 메서드의 들여쓰기가 잘못되어 `Household` 클래스의 멤버로 인식되지 않을 수 있습니다.
    *   `BaseAgent.update_needs`와 `Household.update_needs`의 메서드 시그니처(매개변수 이름, 타입 힌트 등)가 미묘하게 일치하지 않을 수 있습니다.
    *   이전 코드 수정 과정에서 `Household.update_needs` 메서드 자체가 실수로 삭제되었거나 내용이 손상되었을 가능성이 있습니다.

## 4. 해결 방법 (Solution Method) - 다음 단계

1.  **`simulation/core_agents.py` 파일의 `Household` 클래스 내 `update_needs` 메서드 존재 여부 및 내용 확인:**
    *   메서드가 실제로 존재하는지, 그리고 그 내용이 올바른지 육안으로 확인합니다.
    *   메서드의 시그니처(`def update_needs(self, current_time: int) -> None:`)가 `BaseAgent`의 추상 메서드 시그니처(`def update_needs(self, current_tick: int):`)와 일치하는지 확인합니다. 특히 매개변수 이름(`current_time` vs `current_tick`)을 통일합니다.
    *   메서드의 들여쓰기가 `Household` 클래스의 다른 메서드와 동일한 수준인지 확인합니다.
2.  **`@override` 데코레이터 추가:** `update_needs` 메서드 위에 `@override` 데코레이터를 명시적으로 추가하여 파이썬 런타임이 이 메서드를 `BaseAgent`의 추상 메서드에 대한 재정의로 명확하게 인식하도록 돕습니다.
3.  **`ruff check` 및 `run_experiment.py` 재실행:** 수정 후 `ruff check`를 통해 구문 오류를 확인하고, `run_experiment.py`를 다시 실행하여 `TypeError`가 해결되었는지 검증합니다.