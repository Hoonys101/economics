# Golden Fixture Migration

## 🎯 Objective
테스트 코드의 `MagicMock` 기반 에이전트 목을 **Golden Fixture** 기반으로 마이그레이션하여 타입 안전성과 테스트 신뢰도를 향상시킵니다.

---

## 📋 Phase 1: Golden Fixture 생성 (우선순위 HIGH)

### Task 1.1: 실제 시뮬레이션에서 골든 데이터 캡처

1. **시뮬레이션 실행 스크립트 생성**
```python
# scripts/generate_golden_fixtures.py
from simulation.initialization.initializer import SimulationInitializer
from scripts.fixture_harvester import FixtureHarvester

def main():
 # 기본 시뮬레이션 빌드
 initializer = SimulationInitializer(...)
 sim = initializer.build_simulation()

 harvester = FixtureHarvester(output_dir="tests/goldens")

 # Tick 0: 초기 상태
 harvester.capture_agents(sim.households, sim.firms, tick=0)
 harvester.capture_config(sim.config_module)
 harvester.save_all("initial_state.json")

 # Tick 10: 조기 경제
 for _ in range(10):
 sim.run_tick()
 harvester.capture_agents(sim.households, sim.firms, tick=10)
 harvester.save_all("early_economy.json")

 # Tick 100: 안정화된 경제
 for _ in range(90):
 sim.run_tick()
 harvester.capture_agents(sim.households, sim.firms, tick=100)
 harvester.save_all("stable_economy.json")

 print("✅ Golden fixtures generated successfully!")

if __name__ == "__main__":
 main()
```

2. **실행하여 골든 파일 생성**
```bash
python scripts/generate_golden_fixtures.py
```

3. **생성할 골든 픽스처 목록**

| 파일명 | 용도 | Tick |
|---|---|---|
| `initial_state.json` | 초기화 테스트 | 0 |
| `early_economy.json` | 부트스트랩 테스트 | 10 |
| `stable_economy.json` | 통합 테스트 | 100 |
| `crisis_scenario.json` | Phase 28/29 스트레스 테스트 | 50 (쇼크 후) |
| `high_employment.json` | 노동시장 테스트 | 특정 조건 |

---

## 📋 Phase 2: conftest.py 확장

### Task 2.1: 시나리오별 픽스처 추가

`tests/conftest.py`에 다음 픽스처 추가:

```python
@pytest.fixture
def golden_initial_households():
 """Tick 0 초기 가구 상태"""
 loader = _get_golden_loader("initial_state.json")
 return loader.create_household_mocks() if loader else []

@pytest.fixture
def golden_initial_firms():
 """Tick 0 초기 기업 상태"""
 loader = _get_golden_loader("initial_state.json")
 return loader.create_firm_mocks() if loader else []

@pytest.fixture
def golden_stable_households():
 """Tick 100 안정화된 가구"""
 loader = _get_golden_loader("stable_economy.json")
 return loader.create_household_mocks() if loader else []

@pytest.fixture
def golden_stable_firms():
 """Tick 100 안정화된 기업"""
 loader = _get_golden_loader("stable_economy.json")
 return loader.create_firm_mocks() if loader else []
```

---

## 📋 Phase 3: 기존 테스트 마이그레이션 (선택적)

### 마이그레이션 우선순위

| 우선순위 | 파일 | 이유 |
|---|---|---|
| 🔴 HIGH | `test_phase29_depression.py` | 최신 Phase, 활발히 사용 |
| 🔴 HIGH | `test_stress_scenarios.py` | Mock 복잡도 높음 |
| 🟡 MEDIUM | `test_engine.py` | 핵심 통합 테스트 |
| 🟡 MEDIUM | `test_firms.py` | Firm Mock 집중 |
| 🟢 LOW | 나머지 | 점진적 마이그레이션 |

### 마이그레이션 패턴

**Before (MagicMock):**
```python
def test_crisis_monitor():
 firms = [MagicMock() for _ in range(5)]
 for i, f in enumerate(firms):
 f.id = 100 + i
 f.is_active = True
 f.assets = 5000
 # ... 30줄의 수동 설정
```

**After (Golden Fixture):**
```python
def test_crisis_monitor(golden_firms):
 # golden_firms는 자동으로 실제 데이터에서 로드됨
 monitor = CrisisMonitor(logger, run_id=0)
 result = monitor.monitor(tick=1, firms=golden_firms)
 assert result["active"] == len(golden_firms)
```

---

## ✅ Acceptance Criteria

1. [ ] `tests/goldens/` 폴더에 최소 3개의 골든 픽스처 파일 생성
2. [ ] `scripts/generate_golden_fixtures.py` 스크립트 실행 가능
3. [ ] `conftest.py`에 시나리오별 픽스처 정의
4. [ ] 최소 1개의 기존 테스트를 골든 픽스처로 마이그레이션
5. [ ] `pytest tests/` 전체 테스트 통과

---

## 📚 참고 자료

- `scripts/fixture_harvester.py` - FixtureHarvester, GoldenLoader 클래스
- `tests/goldens/README.md` - 골든 픽스처 사용 가이드
- `design/manuals/spec_writer.md` - Mocking 가이드 섹션

---

## ⚠️ 주의사항

1. **DB 의존성**: 시뮬레이션 실행에 SQLite DB가 필요할 수 있음 - 테스트용 임시 DB 사용
2. **Config 의존성**: `config/simulation_config.yaml` 필요
3. **Mock 완전 대체 금지**: 모든 MagicMock을 대체하지 않음 - 에이전트(Household, Firm)에만 집중
