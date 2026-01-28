네, 알겠습니다. 팀장(Antigravity)의 지시에 따라 'WO-079: Config Automation (v2)'에 대한 '질문 제로(Zero-Question)' 수준의 상세 설계 초안을 작성하겠습니다.

제공된 컨텍스트와 감사 보고서(Auto-Audit, External Audit)를 종합하여, 기존 테스트 스위트와의 호환성을 최우선으로 고려한 하이브리드 접근 방식과 명확한 테스트 전략을 포함시키겠습니다.

먼저, 새로운 `ConfigManager`의 인터페이스 계약(`api.py`) 초안입니다.

---

### `modules/common/config_manager/api.py` (신규 생성)

```python
from __future__ import annotations
from typing import Any, Optional
from pathlib import Path

class ConfigManager:
    """
    Manages loading configuration from YAML files and provides a unified access interface.
    It supports a hybrid mode, falling back to a legacy config module for values
    not found in the YAML files. This class is designed as a leaf node and should not
    have dependencies on other simulation modules.
    """

    def __init__(self, config_dir: Path, legacy_config: Optional[Any] = None):
        """
        Initializes the ConfigManager, loading all YAML files from the specified directory.

        Args:
            config_dir: The directory path containing .yaml configuration files.
            legacy_config: An optional legacy config module (e.g., config.py) to use as a fallback.
        """
        ...

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """
        Retrieves a configuration value using dot notation.

        It first searches the loaded YAML configuration. If not found, it attempts
        to retrieve the value from the legacy config module (if provided).
        If still not found, it returns the default value.

        Example:
            config.get('simulation.batch_save_interval', 50)
            config.get('finance.bank_defaults.credit_spread_base')

        Args:
            key: The dot-separated key for the configuration value.
            default: The value to return if the key is not found anywhere.

        Returns:
            The requested configuration value.
        """
        ...

    def set_value_for_test(self, key: str, value: Any) -> None:
        """
        Dynamically sets or overrides a configuration value for testing purposes.
        This method should ONLY be used in test suites to avoid file I/O.
        It allows monkey-patching configuration at runtime.

        Example (in a pytest test):
            config_manager.set_value_for_test('ai.epsilon_decay.initial', 0.99)

        Args:
            key: The dot-separated key to set.
            value: The value to assign to the key.
        """
        ...

```
---

다음은 위 `api.py` 계약을 기반으로 한 상세 구현 명세서(`spec.md`)입니다.

### `design/specs/WO-079_Config_Automation_v2.md` (신규 생성)

```markdown
# 상세 설계 명세서: WO-079 Config Automation v2

**Version:** 1.0
**Author:** Gemini (Administrative Assistant)
**Status:** DRAFT

## 1. 개요 (Overview)
이 문서는 프로젝트의 하드코딩된 상수와 `config.py` 모듈을 중앙화된 YAML 파일 기반의 설정 시스템으로 전환하기 위한 상세 설계를 정의합니다. `simulation/config_manager.py`에 `ConfigManager` 클래스를 도입하여, 기존 테스트 코드의 파손을 최소화하고 점진적인 마이그레이션을 지원하기 위해 **하이브리드(Hybrid) 접근 방식**을 채택합니다.

- **YAML 우선**: YAML 파일에 정의된 설정이 `config.py`의 레거시 설정보다 우선순위를 가집니다.
- **테스트 용이성**: `pytest`의 `monkeypatch`를 통해 파일 시스템 접근 없이 설정을 동적으로 재정의할 수 있는 명확한 인터페이스를 제공합니다.
- **점진적 전환**: 기존 `config.py`를 즉시 제거하지 않고, 각 모듈의 상수들을 점진적으로 `config/*.yaml` 파일로 이전합니다.

## 2. 인터페이스 명세 (API Specification)
`ConfigManager`의 공개 인터페이스는 `modules/common/config_manager/api.py`에 다음과 같이 정의됩니다. 모든 구현은 이 계약을 따라야 합니다.

```python
from __future__ import annotations
from typing import Any, Optional
from pathlib import Path

class ConfigManager:
    """
    Manages loading configuration from YAML files and provides a unified access interface.
    It supports a hybrid mode, falling back to a legacy config module for values
    not found in the YAML files. This class is designed as a leaf node and should not
    have dependencies on other simulation modules.
    """

    def __init__(self, config_dir: Path, legacy_config: Optional[Any] = None):
        """
        Initializes the ConfigManager, loading all YAML files from the specified directory.

        Args:
            config_dir: The directory path containing .yaml configuration files.
            legacy_config: An optional legacy config module (e.g., config.py) to use as a fallback.
        """
        ...

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """
        Retrieves a configuration value using dot notation.

        It first searches the loaded YAML configuration. If not found, it attempts
        to retrieve the value from the legacy config module (if provided).
        If still not found, it returns the default value.

        Example:
            config.get('simulation.batch_save_interval', 50)
            config.get('finance.bank_defaults.credit_spread_base')

        Args:
            key: The dot-separated key for the configuration value.
            default: The value to return if the key is not found anywhere.

        Returns:
            The requested configuration value.
        """
        ...

    def set_value_for_test(self, key: str, value: Any) -> None:
        """
        Dynamically sets or overrides a configuration value for testing purposes.
        This method should ONLY be used in test suites to avoid file I/O.
        It allows monkey-patching configuration at runtime.

        Example (in a pytest test):
            config_manager.set_value_for_test('ai.epsilon_decay.initial', 0.99)

        Args:
            key: The dot-separated key to set.
            value: The value to assign to the key.
        """
        ...
```

## 3. 로직 단계 (Pseudo-code)

### `ConfigManager.__init__(self, config_dir, legacy_config)`
1.  `self._config`를 빈 딕셔너리로 초기화합니다.
2.  `self._legacy_config`에 `legacy_config` 인자를 저장합니다.
3.  `config_dir`가 존재하는지 확인합니다. 존재하지 않으면 경고를 로그하고 빈 설정으로 계속 진행합니다.
4.  `config_dir` 내의 모든 `*.yaml` 및 `*.yml` 파일을 찾습니다.
5.  각 YAML 파일을 순회합니다:
    a. `yaml.safe_load()`를 사용하여 파일 내용을 파싱합니다.
    b. 파일의 이름(확장자 제외, 예: 'finance.yaml' -> 'finance')을 최상위 키로 사용합니다.
    c. 파싱된 딕셔너리를 `self._config[<파일 이름>]`에 할당합니다.

### `ConfigManager.get(self, key, default)`
1.  `key`를 `.` 기준으로 분리하여 `parts` 리스트를 만듭니다(예: 'simulation.batch_size' -> ['simulation', 'batch_size']).
2.  `value = self._config` 로 탐색을 시작합니다.
3.  `parts`의 각 `part`에 대해:
    a. `value`가 딕셔너리이고 `part`를 키로 가지고 있는지 확인합니다.
    b. 가지고 있다면 `value = value[part]`로 업데이트합니다.
    c. 그렇지 않다면, YAML 탐색을 중단하고 `None`을 임시 반환값으로 설정합니다.
4.  **YAML에서 값을 찾은 경우**: 탐색된 `value`를 반환합니다.
5.  **YAML에서 값을 찾지 못한 경우 (하이브리드 폴백)**:
    a. `self._legacy_config`가 존재하는지 확인합니다.
    b. 존재한다면, `getattr(self._legacy_config, key.upper(), default)`를 호출하여 레거시 모듈에서 값을 찾습니다 (키는 대문자로 변환).
    c. 찾은 값을 반환합니다.
6.  **어디에서도 값을 찾지 못한 경우**: `default` 인자를 반환합니다.

### `ConfigManager.set_value_for_test(self, key, value)`
1.  `key`를 `.` 기준으로 `parts` 리스트로 분리합니다.
2.  `node = self._config`로 탐색을 시작합니다.
3.  마지막 `part`를 제외한 나머지 `part`들을 순회하며:
    a. `node`에 해당 `part`가 없거나 딕셔너리가 아니면, 빈 딕셔너리를 생성합니다 (`node.setdefault(part, {})`).
    b. `node`를 `node[part]`로 업데이트합니다.
4.  마지막 `part`를 키로 사용하여 `node[<마지막 part>] = value`를 설정합니다.

## 4. 파일 구조 및 예시 (File Structure & Examples)

```
economics/
├── config/
│   ├── ai.yaml
│   ├── finance.yaml
│   └── simulation.yaml
├── modules/
│   └── common/
│       └── config_manager/
│           ├── __init__.py
│           ├── api.py
│           └── impl.py  # Jules가 구현할 파일
└── simulation/
    └── initialization/
        └── initializer.py # ConfigManager가 생성되고 주입될 위치
```

**`config/simulation.yaml` 예시:**
```yaml
batch_save_interval: 50
sma_buffer_window: 10
chaos_events:
  - tick: 200
    type: "inflation_shock"
    value: 1.5
  - tick: 600
    type: "recession_shock"
    value: 0.5
```

**`config/finance.yaml` 예시:**
```yaml
bank_defaults:
  ticks_per_year: 100
  initial_base_annual_rate: 0.05
  credit_spread_base: 0.02
  bank_margin: 0.02
```

## 5. 예외 처리 (Exception Handling)
- **디렉토리 없음**: `__init__` 시 `config_dir`이 없으면 `FileNotFoundError`를 발생시키지 않고, 경고 로그만 남깁니다. 시스템은 레거시 설정으로만 동작할 수 있어야 합니다.
- **YAML 파싱 오류**: 특정 YAML 파일 파싱 중 `yaml.YAMLError`가 발생하면, 해당 파일명을 포함한 에러 로그를 기록하고 그 파일을 건너뛴 후 다음 파일 로딩을 계속 진행합니다. 시스템 전체가 중단되어서는 안 됩니다.

## 6. 검증 계획 (Verification Plan) - **[매우 중요]**

### 6.1. 단위 테스트 (`ConfigManager`)
- `tmp_path` fixture를 사용하여 임시 YAML 파일을 생성하고, `ConfigManager`가 이를 정확히 로드하는지 테스트합니다.
- `get()` 메서드가 중첩된 키(e.g., `finance.bank_defaults.credit_spread_base`)를 정확히 반환하는지 검증합니다.
- YAML에 키가 없을 때 `legacy_config` 모듈에서 값을 가져오는지 검증합니다.
- 모든 곳에 키가 없을 때 `default` 값을 정확히 반환하는지 검증합니다.
- `set_value_for_test()`가 런타임에 값을 정확히 변경하는지 검증합니다.

### 6.2. 통합 테스트 (기존 테스트 스위트 호환성)
**기존 테스트 방식의 문제점:**
현재 테스트들은 `mocker.patch.object(config, 'SOME_VALUE', ...)` 와 같이 `config.py` 모듈 객체를 직접 패치하고 있습니다. 파일 기반의 `ConfigManager`는 이 방식을 깨뜨립니다.

**새로운 테스트 전략 (`monkeypatch` 활용):**
`simulation` 객체나 `bank` 객체 등 테스트 대상이 `ConfigManager` 인스턴스를 주입받도록 리팩토링한 후, `monkeypatch`를 사용하여 `set_value_for_test` 메서드를 간접적으로 활용합니다.

**예시: `simulation/bank.py`의 `grant_loan` 테스트**

**AS-IS (기존 방식):**
```python
def test_grant_loan_with_mock_config(mocker):
    from simulation import config # 레거시 모듈
    mocker.patch.object(config, 'LOAN_DEFAULT_TERM', 120)

    bank = Bank(id=1, initial_assets=1000, config_module=config)
    loan_id = bank.grant_loan(...)
    # ... assert loan term is 120 ...
```

**TO-BE (제안 방식):**
```python
def test_grant_loan_with_new_config(config_manager_instance):
    # config_manager_instance는 fixture 등으로 주입받은 ConfigManager 객체
    # monkeypatch를 사용하여 ConfigManager의 내부 상태를 변경
    config_manager_instance.set_value_for_test('loan.default_term', 120)

    # Bank는 이제 config_manager 인스턴스를 받음
    bank = Bank(id=1, initial_assets=1000, config_manager=config_manager_instance)
    loan_id = bank.grant_loan(...)
    # ... assert loan term is 120 ...
```
이 전략을 통해 테스트 코드는 파일 시스템과 완전히 분리되며, 기존의 동적 설정 변경 기능을 유지할 수 있습니다.

## 7. 🚨 Risk & Impact Audit (기술적 위험 분석)
- **[HIGH] 테스트 파괴 위험**: 본 리팩토링의 가장 큰 위험입니다. 제안된 `set_value_for_test`와 `monkeypatch` 전략을 모든 관련 테스트에 체계적으로 적용해야 합니다. (약 80개 이상의 테스트 파일에 영향 예상)
- **[LOW] 순환 참조 위험**: `ConfigManager`는 `PyYAML`과 표준 라이브러리 외에 다른 시뮬레이션 모듈을 **절대** 임포트해서는 안 됩니다. 이 "Leaf Node" 원칙을 준수하면 순환 참조 위험은 없습니다.
- **[MEDIUM] `engine.py` God Class 의존성**: `ConfigManager` 인스턴스를 `simulation/initialization/initializer.py`에서 **단 한 번 생성**하고, 이를 `Simulation` 엔진을 통해 모든 하위 시스템(Bank, Government 등)에 주입(DI)해야 합니다. 이는 전역 상태를 방지하고 의존성 흐름을 명확하게 만듭니다.
- **[LOW] 설정 누락 위험**: 마이그레이션 과정에서 일부 상수가 누락될 수 있습니다. 하이브리드 폴백 기능이 이를 완화하지만, 최종적으로는 코드베이스에서 하드코딩된 숫자나 `config.py` 참조를 모두 제거하는 클린업 작업이 필요합니다.

## 8. Mandatory Reporting
구현 담당자(Jules)는 작업 중 발견한 모든 기술적 부채, 아키텍처 개선 아이디어, 또는 명세서의 모호함으로 인해 발생한 문제들을 `communications/insights/` 폴더에 `[WO-079]_<topic>.md` 형식으로 기록하고 보고해야 합니다.
```
