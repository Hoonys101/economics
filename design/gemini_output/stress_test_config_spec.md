📄 Drafting Spec with instruction: 'Write a Zero-Question Implementation Spec for fixing TD-007 (Industrial Revolution Stress Test Config). GOAL: Identify all hardcoded 'magic numbers' related to economic thresholds (demand caps, supply floor, wage stickiness) across the simulation engine and move them to a centralized `config.py` structure. IMPLEMENTATION: 1) Propose a hierarchical Config Class structure. 2) Define a migration map for `simulation/engine.py` and `simulation/firms.py`. 3) Design a 'Stress Test Profile' loader that can override multiple config values at once for scenarios like the Industrial Revolution. Include: Config Schema, Migration Pseudo-code, and Scenario Loading Logic in Korean.'...
📖 Attached context: config.py
📖 Attached context: simulation\engine.py
📖 Attached context: simulation\firms.py
📖 Attached context: design\TECH_DEBT_LEDGER.md
🚀 [GeminiWorker] Running task with manual: spec_writer.md

✅ Spec Draft Saved: C:\coding\economics\design\drafts\draft_Write_a_Zero_Question_Implemen.md
============================================================

✅ Spec Draft Saved: C:\coding\economics\design\drafts\draft_Write_a_Zero_Question_Implemen.md
============================================================
알겠습니다. TD-007 기술 부채 해결을 위한 명세서 작성을 시작하겠습니다. 목표는 하드코딩된 경제 임계값들을 `config.py`로 중앙화하고, 스트레스 테스트 프로필 로더를 설계하여 시뮬레이션의 유연성과 유지보수성을 높이는 것입니다.

먼저, 새로운 `ConfigManager`를 위한 `api.py` 파일을 생성하고, 이어서 제로-퀘스천 구현 명세서(`spec.md`)를 작성하겠습니다.

첫 번째 단계로, `modules/core` 디렉토리가 존재하는지 확인하겠습니다.

`modules/core` 디렉토리가 존재하지 않는 것을 확인했습니다. `ConfigManager`와 같은 핵심 유틸리티 모듈을 관리하기 위한 `modules/core/config_manager` 디렉토리 구조를 생성하겠습니다. 이 구조는 향후 다른 핵심 공통 모듈들을 체계적으로 관리하는 기반이 될 것입니다.
알겠습니다. `run_shell_command` 도구를 사용할 수 없으므로, `write_file` 도구를 사용하여 디렉토리를 생성하는 방법을 사용하겠습니다. 빈 `__init__.py` 파일을 목표 경로에 생성함으로써 필요한 부모 디렉토리(`modules/core` 및 `modules/core/config_manager`)를 생성하겠습니다.
죄송합니다. `write_file` 또는 디렉토리 생성을 위한 도구가 제 환경에 제공되지 않아 요청하신 `modules/core/config_manager` 디렉토리와 그 안의 `api.py` 파일을 물리적으로 생성할 수 없습니다.

하지만, 요청하신 내용에 따라 제로-퀘스천 구현 명세서의 전체 내용과 API 파일의 전체 내용을 설계했습니다. 아래에 제시해 드리는 내용으로 `design/specs/refactor_config_stress_test_spec.md`와 `modules/core/config_manager/api.py` 파일을 직접 생성해주시면 감사하겠습니다.

---

### **`modules/core/config_manager/api.py` 파일 내용:**

```python
from __future__ import annotations
from typing import Dict, Any, Optional, Type
import yaml
from pydantic import BaseModel, Field
import logging
from pathlib import Path

# --- Configuration Schemas (Pydantic Models) ---

class HouseholdDecisionConfig(BaseModel):
    """가계 의사결정 관련 설정"""
    low_asset_threshold: float = Field(100.0, description="자산이 이 값 미만이면 낮은 임금 수용")
    low_asset_wage: float = Field(8.0, description="자산이 낮을 때 희망 임금")
    default_wage: float = Field(10.0, description="기본 희망 임금")
    job_quit_threshold_base: float = Field(2.0, description="기본 퇴직 임계값 (낮은 이동성)")
    job_quit_prob_scale: float = Field(0.9, description="퇴직 확률 스케일 (agg_mobility에 따라 변동)")
    bulk_buy_need_threshold: float = Field(70.0, description="대량 구매를 촉발하는 욕구 임계값")
    budget_limit_urgent_ratio: float = Field(0.9, description="긴급 상황 시 자산 대비 예산 비율")

class FirmDecisionConfig(BaseModel):
    """기업 의사결정 관련 설정"""
    production_adjustment_factor: float = Field(0.2, description="재고 기반 생산량 조정 계수")
    price_adjustment_factor: float = Field(0.2, description="재고 기반 가격 조정 계수")
    labor_requirement_ratio: float = Field(0.9, description="필요 노동력 대비 현재 고용 비율 임계값")
    automation_decay_rate: float = Field(0.995, description="자동화 수준 자연 감소율 (1-감소율)")
    labor_elasticity_min: float = Field(0.3, description="노동 탄력성 최소값 (α)")
    valuation_per_multiplier: int = Field(10, description="기업 가치 평가 시 평균 이익에 적용할 PER 배수")
    bankruptcy_threshold_ticks: int = Field(20, description="연속 손실로 파산에 이르는 틱 수")

class MarketConfig(BaseModel):
    """시장 관련 설정"""
    max_sell_price: float = Field(100.0, description="최대 판매 가격")
    min_purchase_quantity: float = Field(0.1, description="최소 구매 수량")
    stock_price_limit_rate: float = Field(0.15, description="주식 시장 일일 가격 변동폭 제한")
    invisible_hand_sensitivity: float = Field(0.1, description="보이지 않는 손 가격 조정 민감도")

class SimulationConfig(BaseModel):
    """시뮬레이션 전반에 대한 설정"""
    batch_save_interval: int = Field(50, description="데이터베이스에 상태를 일괄 저장하는 주기")
    gov_sensory_buffer_size: int = Field(10, description="정부 AI의 SMA 계산을 위한 버퍼 크기")

class ScenarioConfig(BaseModel):
    """모든 설정을 포함하는 최상위 시나리오 설정"""
    household_decision: HouseholdDecisionConfig = Field(default_factory=HouseholdDecisionConfig)
    firm_decision: FirmDecisionConfig = Field(default_factory=FirmDecisionConfig)
    market: MarketConfig = Field(default_factory=MarketConfig)
    simulation: SimulationConfig = Field(default_factory=SimulationConfig)
    # 다른 설정 그룹들도 필요에 따라 추가 가능

# --- ConfigManager API ---

class ConfigManager:
    """
    시뮬레이션 설정을 관리하는 클래스.
    기본 설정(config.py)을 로드하고, 특정 시나리오(YAML) 파일로 덮어씁니다.
    """

    def __init__(self, scenario_path: Optional[str | Path] = None, logger: Optional[logging.Logger] = None):
        """
        Args:
            scenario_path (Optional[str | Path]): 덮어쓸 시나리오 설정 파일의 경로.
            logger (Optional[logging.Logger]): 로거.
        """
        self.scenario_path = Path(scenario_path) if scenario_path else None
        self.logger = logger or logging.getLogger(__name__)
        self._config: Optional[ScenarioConfig] = None

    def load_config(self) -> ScenarioConfig:
        """
        기본 설정을 로드하고 시나리오 파일로 덮어쓴 최종 설정을 반환합니다.

        Returns:
            ScenarioConfig: 최종 설정 객체.
        """
        if self._config:
            return self._config

        # 1. Pydantic 모델을 사용하여 기본 설정 객체 생성
        base_config = ScenarioConfig()
        self.logger.info("기본 설정 모델을 성공적으로 로드했습니다.")

        if self.scenario_path and self.scenario_path.exists():
            # 2. 시나리오 파일 로드
            try:
                with open(self.scenario_path, 'r', encoding='utf-8') as f:
                    scenario_overrides = yaml.safe_load(f)
                self.logger.info(f"시나리오 파일 '{self.scenario_path}'을(를) 로드했습니다.")

                # 3. 기본 설정에 시나리오 덮어쓰기 (Deep Update)
                base_dict = base_config.dict()
                updated_dict = self._deep_update(base_dict, scenario_overrides)
                self._config = ScenarioConfig.parse_obj(updated_dict)
                self.logger.info("시나리오 설정으로 기본 설정을 성공적으로 덮어썼습니다.")

            except Exception as e:
                self.logger.error(f"시나리오 파일 처리 중 오류 발생: {e}", exc_info=True)
                self._config = base_config # 오류 발생 시 기본 설정으로 폴백
        else:
            self._config = base_config
            if self.scenario_path:
                self.logger.warning(f"시나리오 파일 '{self.scenario_path}'을(를) 찾을 수 없어 기본 설정만 사용합니다.")

        return self._config

    def _deep_update(self, source: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
        """
        중첩된 딕셔너리를 재귀적으로 업데이트합니다.
        """
        for key, value in overrides.items():
            if isinstance(value, dict) and key in source and isinstance(source[key], dict):
                source[key] = self._deep_update(source[key], value)
            else:
                source[key] = value
        return source

    @property
    def config(self) -> ScenarioConfig:
        """현재 로드된 설정 객체에 대한 접근자입니다."""
        if not self._config:
            return self.load_config()
        return self._config

```

---

### **`design/specs/refactor_config_stress_test_spec.md` 파일 내용:**

```markdown
# [Refactor] Work Order: WO-XXX - 설정 중앙화 및 시나리오 로더 구현

**Phase:** 26
**Priority:** HIGH
**Prerequisite:** None
**Technical Debt ID:** TD-007

## 1. Problem Statement (문제 정의)
현재 시뮬레이션 엔진(`engine.py`), 기업(`firms.py`) 등 핵심 로직 전반에 걸쳐 경제적 행동을 결정하는 임계값(소위 '매직 넘버')들이 하드코딩되어 있습니다. 이로 인해 다음과 같은 문제가 발생합니다.
- **유지보수성 저하:** 관련 상수를 변경하기 위해 여러 파일을 수정해야 합니다.
- **실험의 어려움:** '산업혁명', '대공황' 등 특정 경제 시나리오를 테스트하기 위해 코드를 직접 변경해야 하므로, 실험의 재현성과 확장성이 떨어집니다.
- **TD-007:** "비현실적 경제 상태(무한 수요)" 문제는 이러한 하드코딩된 제약 조건이 없기 때문에 발생합니다.

## 2. Objective (목표)
1.  핵심 로직에 하드코딩된 경제 관련 '매직 넘버'들을 `config.py`의 계층적 설정 클래스로 이전합니다.
2.  YAML 파일로 정의된 '시나리오 프로필'을 읽어 기본 설정을 동적으로 덮어쓰는 `ConfigManager`를 구현합니다.
3.  이를 통해 코드 변경 없이 다양한 스트레스 테스트를 수행할 수 있는 기반을 마련합니다.

## 3. Implementation Plan (구현 계획)

### 3.1. `ConfigManager` API 및 설정 스키마 정의

`modules/core/config_manager/api.py`에 `pydantic.BaseModel`을 사용하여 다음과 같은 계층적 설정 스키마와 `ConfigManager`를 정의합니다.

- **`HouseholdDecisionConfig`**: 가계의 의사결정(희망 임금, 퇴사 확률 등) 관련 상수 그룹
- **`FirmDecisionConfig`**: 기업의 의사결정(생산/가격 조정, 파산 조건 등) 관련 상수 그룹
- **`MarketConfig`**: 시장(가격 제한, 수수료 등) 관련 상수 그룹
- **`SimulationConfig`**: 시뮬레이션 자체(로그 주기 등) 관련 상수 그룹
- **`ScenarioConfig`**: 위 모든 설정을 포함하는 최상위 모델
- **`ConfigManager`**: 기본 설정을 로드하고, 지정된 YAML 시나리오 파일로 설정을 덮어쓰는 로더 클래스

*(자세한 API 명세는 `modules/core/config_manager/api.py` 파일 내용을 참조)*

### 3.2. 시나리오 프로필 로딩 로직

`ConfigManager`는 다음과 같이 동작합니다.
1.  `ScenarioConfig` 모델을 통해 기본값을 가진 설정 객체를 생성합니다.
2.  `__init__` 시점에 `scenario_path`가 주어지면, 해당 YAML 파일을 읽습니다.
3.  YAML 파일의 내용을 기본 설정 객체에 덮어쓰기(Deep Update)하여 최종 설정을 확정합니다.
4.  `simulation` 객체는 `ConfigManager.config` 속성을 통해 최종 설정에 접근합니다.

**예시 시나리오 파일 (`scenarios/industrial_revolution.yml`):**
```yaml
description: "산업혁명 스트레스 테스트: 높은 수요와 경직된 임금"

firm_decision:
  price_adjustment_factor: 0.05       # 가격이 쉽게 오르지 않음 (가격 경직성)
  production_adjustment_factor: 0.5   # 재고 부족에 매우 빠르게 반응하여 생산량 증대

household_decision:
  job_quit_prob_scale: 0.1            # 더 나은 임금 제안이 있어도 직장을 잘 옮기지 않음 (임금 경직성)

market:
  max_sell_price: 1000.0              # 인플레이션을 허용하기 위해 가격 상한선 대폭 증가
```

### 3.3. 마이그레이션 계획: 하드코딩된 값 이전

#### 이전 대상 '매직 넘버' 맵
| 파일 | 기존 값 (Before) | 신규 Config 경로 (After) |
|---|---|---|
| `simulation/engine.py` | `self.batch_save_interval = 50` | `config.simulation.batch_save_interval` |
| `simulation/engine.py` | `scores` 계산 가중치 `10.0`, `1000.0` | (신규) `config.household_decision.social_rank_..._weight` |
| `simulation/engine.py` | `deque(maxlen=10)` for SMA | `config.simulation.gov_sensory_buffer_size` |
| `simulation/firms.py` | `self.automation_level *= 0.995` | `self.automation_level *= (1.0 - config.firm_decision.automation_decay_rate)`|
| `simulation/firms.py` | `max(0.3, alpha_raw)` | `max(config.firm_decision.labor_elasticity_min, alpha_raw)` |
| `simulation/firms.py` | `self.consecutive_loss_ticks_for_bankruptcy_threshold` | `config.firm_decision.bankruptcy_threshold_ticks` |
| `config.py` | `MAX_SELL_PRICE`, `MIN_PURCHASE_QUANTITY` 등 | `config.market.max_sell_price`, `config.market.min_purchase_quantity` 등 |

#### 리팩토링 의사코드 (Pseudo-code for Refactoring)

**1. `main.py` 또는 시뮬레이션 진입점:**
   - **Before:** `sim = Simulation(..., config_module=config, ...)`
   - **After:**
     ```python
     # 1. ConfigManager 인스턴스화 (시나리오 경로 주입)
     scenario_file = "scenarios/default.yml" # 또는 다른 시나리오 파일
     config_manager = ConfigManager(scenario_path=scenario_file)
     final_config = config_manager.load_config()

     # 2. Simulation에 config_module 대신 최종 config 객체 주입
     sim = Simulation(..., config=final_config, ...)
     ```

**2. `simulation/engine.py` (`Simulation.__init__`):**
   - **Before:** `def __init__(self, ..., config_module: Any, ...)`
   - **After:** `def __init__(self, ..., config: ScenarioConfig, ...)`
   - **Before:** `self.config_module = config_module`
   - **After:** `self.config = config`
   - **Before:** `self.batch_save_interval = 50`
   - **After:** `self.batch_save_interval = self.config.simulation.batch_save_interval`
   - (모든 `self.config_module.` 참조를 `self.config.<group>.<field>` 형태로 변경)

**3. `simulation/firms.py` (`Firm.__init__` 및 메서드):**
   - **Before:** `def __init__(self, ..., config_module: Any, ...)`
   - **After:** `def __init__(self, ..., config: ScenarioConfig, ...)`
   - **Before:** `self.config_module = config_module`
   - **After:** `self.config = config`
   - **Before (in `produce`):** `alpha_adjusted = max(0.3, alpha_raw)`
   - **After (in `produce`):** `alpha_adjusted = max(self.config.firm_decision.labor_elasticity_min, alpha_raw)`
   - (모든 `self.config_module.` 참조를 `self.config.<group>.<field>` 형태로 변경)

## 4. Verification (검증 계획)
1.  **단위 테스트:** `ConfigManager`에 대한 단위 테스트를 작성한다. (`tests/core/test_config_manager.py`)
    - 시나리오 파일 없이 호출 시 기본 설정을 반환하는지 검증
    - 시나리오 파일 로드 시 지정된 값이 올바르게 덮어쓰기 되는지 검증
    - 유효하지 않은 YAML 파일에 대해 오류를 처리하고 기본값으로 폴백하는지 검증
2.  **통합 테스트:**
    - 기존의 모든 `pytest` 테스트가 리팩토링 후에도 통과하는지 확인한다.
    - `batch_save_interval`을 변경하는 간단한 시나리오를 로드하여 시뮬레이션을 몇 틱 실행하고, 해당 값이 `Simulation` 객체에 올바르게 적용되었는지 `assert`를 통해 확인한다.
3.  **수동 검증:**
    - '산업혁명' 시나리오 YAML 파일을 로드하여 시뮬레이션을 실행하고, 물가와 생산량 로그를 관찰하여 시나리오가 의도대로 동작하는지(예: 높은 생산량, 느린 물가 상승) 확인한다.

## 5. Jules 구현 지침 (Jules's Implementation Guide)
- 위 명세에 따라 `ConfigManager`를 구현하고, 하드코딩된 값들을 `ScenarioConfig` 모델을 사용하도록 리팩토링 하십시오.
- 리팩토링 과정에서 추가로 발견되는 '매직 넘버'가 있다면, 적절한 `...Config` 모델에 추가하고 이 문서를 업데이트 하십시오.
- 작업 완료 후, `pytest`를 실행하여 모든 테스트가 통과하는지 확인하고, 결과를 `final_test_results.txt`에 저장하여 보고하십시오.
- **[Routine] Mandatory Reporting:** 작업 중 발견한 **기술 부채**(예: 아직 이전하지 못한 상수, 리팩토링이 더 필요한 부분)나 **인사이트**(예: 설정 구조 개선 아이디어)가 있다면, `communications/insights/` 폴더에 `YYYY-MM-DD_config_refactor_insights.md` 형식으로 기록을 남겨주십시오.
```

============================================================
