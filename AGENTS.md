# AGENTS.md - Jules Agent Instructions

> 이 파일은 Jules AI 에이전트가 본 프로젝트에서 작업할 때 반드시 따라야 하는 규칙과 컨텍스트입니다.

## 1. 프로젝트 개요

**프로젝트명**: 살아있는 디지털 경제 (Living Digital Economy)
**설명**: 에이전트 기반 경제 시뮬레이션 시스템. Household, Firm, Government, Bank 등의 AI 에이전트들이 시장에서 상호작용하며 거시경제 현상을 창발시킵니다.

**기술 스택**:
- Backend: Python 3.13+, NumPy (Vectorized Logic)
- Frontend: React + TypeScript (Vite)
- Database: SQLite (시뮬레이션 결과 저장)
- AI: Q-Learning, Rule-Based Decision Engines

---

## 2. 아키텍처 규칙 (CRITICAL)

### 2.1 계층형 아키텍처 (Layered Architecture)
```
[DTO] ←→ [DAO] ←→ [Service/Logic] ←→ [Controller/Agent]
```
- **DTO (Data Transfer Object)**: 계층 간 데이터 전달은 반드시 DTO를 통해서만 수행
- **DAO (Data Access Object)**: DB/파일 I/O는 DAO가 전담
- **Service**: 비즈니스 로직 실행
- **Agent**: 의사결정 및 행동 수행

### 2.2 파일 구조 제약
```
simulation/
├── agents/          # Government, CentralBank 등 시스템 에이전트
├── ai/              # AI 엔진 (household_ai.py, government_ai.py)
├── decisions/       # 의사결정 엔진
├── interfaces/      # 추상 인터페이스 (IGovernmentPolicy 등)
├── policies/        # 정책 구현체 (taylor_rule_policy.py 등)
├── systems/         # 시스템 매니저 (housing_system.py 등)
├── dtos.py          # DTO 정의
├── engine.py        # 시뮬레이션 엔진 (메인 루프)
├── core_agents.py   # Household 에이전트
├── firms.py         # Firm 에이전트
└── bank.py          # 상업은행

config.py            # 모든 설정 상수 (API Key 하드코딩 금지!)
```

### 2.3 수정 금지 영역
다음 파일/폴더는 **명시적인 승인 없이 수정 금지**:
- `/core/`, `/interface/` (존재할 경우)
- `config.py`의 기존 상수값 (추가만 허용)
- `main.py`

---

## 3. 코딩 스타일

### 3.1 Python
- **PEP 8** 준수
- **Type Hints** 필수: 모든 함수/메서드에 타입 힌트 명시
- **Docstring** 필수: Google 스타일
- **포매터**: `ruff format .` 실행 후 커밋

### 3.2 네이밍 컨벤션
- 클래스: `PascalCase` (예: `GovernmentAI`)
- 함수/변수: `snake_case` (예: `calculate_reward`)
- 상수: `UPPER_SNAKE_CASE` (예: `TARGET_INFLATION_RATE`)
- DTO: `<Name>DTO` (예: `GovernmentStateDTO`)

### 3.3 로깅
```python
logger.info(
    f"ACTION_NAME | Key: {value:.2f}",
    extra={"tick": current_tick, "agent_id": self.id, "tags": ["category"]}
)
```

---

## 4. 작업 워크플로우

### 4.1 Work Order 구조
모든 작업은 `design/work_orders/WO-XXX-*.md` 형식의 지시서를 따릅니다.

### 4.2 테스트 요구사항
- 모든 새 기능은 `tests/` 디렉토리에 테스트 코드 포함 필수
- 테스트 명명: `test_<module>_<feature>.py`
- 실행: `pytest tests/test_<module>.py -v`

### 4.3 커밋 메시지 형식
```
<type>: <subject>

Types: feat, fix, docs, refactor, test, chore
Example: feat: implement 81-state Q-Learning engine for GovernmentAI
```

---

## 5. 현재 프로젝트 상태

### 5.1 활성 개발 중
- **WO-056**: The Invisible Hand (Shadow Mode) - Money Leak 디버깅
- **WO-057**: The Smart Leviathan (AI Policy) - Q-Learning 정부 AI

### 5.2 최근 완료
- **WO-055**: Golden Age Stabilization
- **Phase 23**: The Great Expansion (Public Education, Fertilizer)

---

## 6. 핵심 DTO 및 인터페이스

### GovernmentStateDTO (WO-057-B)
```python
@dataclass
class GovernmentStateDTO:
    tick: int
    inflation_sma: float      # 10-Tick SMA
    unemployment_sma: float
    gdp_growth_sma: float
    wage_sma: float
    approval_sma: float
```

### IGovernmentPolicy (Policy Interface)
```python
class IGovernmentPolicy(ABC):
    @abstractmethod
    def decide(self, government: Any, market_data: Dict, tick: int) -> Dict:
        """Returns: {"policy_type": str, "interest_rate_delta": float, "tax_rate_delta": float}"""
```

---

## 7. 중요 설정 상수 (config.py)

```python
# WO-057 관련
GOVERNMENT_POLICY_MODE = "TAYLOR_RULE"  # or "AI_ADAPTIVE"
TARGET_INFLATION_RATE = 0.02
TARGET_UNEMPLOYMENT_RATE = 0.04
GOV_ACTION_INTERVAL = 30  # 30틱마다 정책 결정
RL_LEARNING_RATE = 0.1
RL_DISCOUNT_FACTOR = 0.95
```

---

## 8. 이 프로젝트에서 하지 말아야 할 것

1. ❌ API Key 하드코딩
2. ❌ 테스트 없는 기능 추가
3. ❌ Type Hint 생략
4. ❌ 기존 API 시그니처 변경 (하위 호환성 유지)
5. ❌ `simulation/engine.py`에 비즈니스 로직 추가 (시스템만 담당)

---

## 9. 참조 문서

- [Project Status](design/project_status.md)
- [Handover](design/HANDOVER.md)
- [GEMINI.md](GEMINI.md) - 상세 개발 지침
- [Work Orders](design/work_orders/) - 작업 지시서

---

> **Tip**: 작업 중 질문이 있으면 `communications/requests/` 폴더에 질의 문서를 생성하세요.

## 10. Core Principles & Lessons

### Principle: All Agents are Born with Purpose (Newborn Initialization)

-   **Phenomenon**: Newborn agents were created but remained inactive, eventually being culled by the simulation for failing to act.
-   **Cause**: Agents were initialized with an empty `initial_needs` dictionary (`{}`). The decision-making engine had no unmet needs to address, resulting in a permanent state of inaction (apathy).
-   **Solution**: A default set of `NEWBORN_INITIAL_NEEDS` (e.g., for survival, social status) is now defined in `config/economy_params.yaml`. The `DemographicManager` injects these needs upon agent creation, providing an immediate set of goals.
-   **Lesson**: An agent's existence requires not just physical attributes but also **intrinsic motivation**. Every agent must be initialized with a non-empty set of needs that drives their first actions. Without a goal, an agent is inert.
