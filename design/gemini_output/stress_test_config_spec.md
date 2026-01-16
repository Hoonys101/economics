# WO-077: Config Automation & Stress Test Threshold Migration

## 1. 개요 (Overview)
*   **Goal**: 시뮬레이션 엔진(`engine.py`, `firms.py` 등)에 산재된 하드코딩된 경제 파라미터(Magic Numbers)를 제거하고, 중앙 집중식 `config.py`로 통합 관리합니다. 이를 통해 **산업혁명(Industrial Revolution)** 등 다양한 경제 시나리오(Stress Test)를 JSON 프로파일 교체만으로 실험할 수 있게 만듭니다.
*   **Target**: `simulation/config.py` (신설/확장), `simulation/engine.py`, `simulation/firms.py`

## 2. 아키텍처 설계 (Architecture Design)

### 2.1 계층형 Config 구조
단순 변수 나열이 아닌, 도메인별 dataclass를 활용한 계층 구조를 도입합니다.

```python
# simulation/config.py (Proposed Structure)

from dataclasses import dataclass, field
from typing import Dict, Any
import json
import os

@dataclass
class EconomyConfig:
    # Macroeconomic Parameters
    TAX_RATE: float = 0.2
    BASE_INTEREST_RATE: float = 0.05
    GOV_BUDGET_BOND_RATIO: float = 0.3  # 예산 중 국채 발행 비중
    BAILOUT_THRESHOLD_RATIO: float = 0.5 # 구제금융 조건 (자본잠식 비율)

@dataclass
class AgentConfig:
    # Agent Behaviors
    LABOR_ELASTICITY_MIN: float = 0.3
    CONSUMPTION_SMOOTHING: float = 0.8
    INVENTORY_BUFFER: float = 2.0
    
@dataclass
class SimulationConfig:
    economy: EconomyConfig = field(default_factory=EconomyConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)
    # Simulation Settings
    MAX_TICKS: int = 1000
    TICKS_PER_YEAR: int = 100

    @classmethod
    def load(cls, profile_name: str = "default.json") -> "SimulationConfig":
        # 로직: default값 생성 -> JSON 파일 로드 -> 값 덮어쓰기 (Overriding)
        # 구현 필수
        pass

# Global Singleton Instance
sim_config = SimulationConfig()
```

### 2.2 마이그레이션 대상 (Constants to Migrate)

| 기존 위치 | 변수명(유사) | 이동 경로 | 비고 |
|---|---|---|---|
| `simulation/agents.py` | `TAX_RATE` | `sim_config.economy.TAX_RATE` | |
| `simulation/engine.py` | `LABOR_MARKET_FLEXIBILITY` | `sim_config.agent.LABOR_ELASTICITY_MIN` | 명칭 구체화 |
| `simulation/firms.py` | `INVENTORY_TARGET` | `sim_config.agent.INVENTORY_BUFFER` | |
| `simulation/engine.py` | `BASE_INTEREST_RATE` | `sim_config.economy.BASE_INTEREST_RATE` | |

## 3. 구현 상세 (Implementation Details)

### 3.1 `simulation/config.py` 작성
*   위 `SimulationConfig` 구조를 구현하십시오.
*   `profiles/` 디렉토리를 생성하고, `default.json`과 `industrial_revolution.json` 예제를 생성하십시오.
*   **Industrial Revolution Profile 예시**:
    ```json
    {
        "economy": {
            "TAX_RATE": 0.1, 
            "BASE_INTEREST_RATE": 0.02 
        },
        "agent": {
            "LABOR_ELASTICITY_MIN": 0.1,
            "INVENTORY_BUFFER": 5.0
        }
    }
    ```

### 3.2 Reference 수정 (Refactoring)
*   `simulation/engine.py`와 `simulation/firms.py` 등에서 기존 상수를 import하는 대신, `from simulation.config import sim_config`를 사용하고 `sim_config.economy.TAX_RATE`와 같이 접근하도록 수정하십시오.
*   기존의 하드코딩된 상수 정의는 삭제하십시오.

## 4. 검증 계획 (Verification Plan)
1.  **Unit Test**: `test_config_loading.py`를 작성하여 JSON 프로파일이 올바르게 로드되고 오버라이딩되는지 확인하십시오.
2.  **Integrity Check**: 시뮬레이션을 짧게(10 tick) 돌려서 파라미터가 적용된 상태로 에러 없이 돌아가는지 확인하십시오.

## 5. 제약 사항 (Constraints)
*   기존 비즈니스 로직을 변경하지 마십시오. 오직 파라미터 접근 방식만 변경해야 합니다.
*   모든 Config 클래스는 Type Hint를 완벽하게 지원해야 합니다.