# Work Order: WO-057-D Operation Awakening (가동식)

## 🏢 Context
Smart Leviathan의 삼위일체(눈, 뇌, 손) 통합이 완료되었습니다. 이제 실제 시뮬레이션 환경에서 1,000틱간의 '통치술 학습'을 수행하고 그 결과를 분석해야 합니다.

## 🎯 Objectives
1. **Fix Immediate Crash**: `simulation/agents/government.py`의 `NameError`를 해결하십시오. 
    - `real_gdp_growth` 및 `inflation` 변수가 `make_policy_decision` 메서드 내에서 정의되지 않아 크래시가 발생합니다.
    - 아래의 누락된 계산 로직을 `make_policy_decision` 내 적절한 위치(Taylor Rule 계산 전)에 복구하십시오.

```python
        # 1. Calculate Inflation (YoY)
        inflation = 0.0
        if len(self.price_history_shadow) >= 2:
            current_p = self.price_history_shadow[-1]
            past_p = self.price_history_shadow[0]
            if past_p > 0:
                inflation = (current_p - past_p) / past_p

        # 2. Calculate Real GDP Growth
        real_gdp_growth = 0.0
        if len(self.gdp_history) >= 2:
            current_gdp = self.gdp_history[-1]
            past_gdp = self.gdp_history[-2]
            if past_gdp > 0:
                real_gdp_growth = (current_gdp - past_gdp) / past_gdp
```

2. **Execute Awakening Run**: 1,000틱간의 시뮬레이션을 실행하십시오.
    - `config.py`의 `GOVERNMENT_POLICY_MODE = "AI_ADAPTIVE"` 상태여야 합니다.
    - `SIMULATION_TICKS = 1000`으로 설정하십시오.
3. **Analyze & Report**: 학습 곡선(Learning Curve)을 생성하고 분석하십시오.
    - `scripts/analyze_learning.py`를 실행하여 `reports/learning_curve.png`를 생성하십시오.

## 📂 관련 파일들
| 분류 | 파일 | 역할 |
| :--- | :--- | :--- |
| **Target** | [government.py](file:///c:/coding/economics/simulation/agents/government.py) | `inflation`, `real_gdp_growth` 복구 |
| **Config** | [config.py](file:///c:/coding/economics/config.py) | 시뮬레이션 모드 및 틱 설정 확인 |
| **Execution** | [main.py](file:///c:/coding/economics/main.py) | 시뮬레이션 진입점 |
| **Analysis** | [analyze_learning.py](file:///c:/coding/economics/scripts/analyze_learning.py) | 결과 시각화 |

## ⚠️ 제약 사항 및 가이드라인
- **Baby Step & Clamping**: 정책 변동이 안전 범위를 벗어나지 않는지 로그를 모니터링하십시오.
- **Three-Phase Observation**: 
    - Phase 1: Chaos (0~300)
    - Phase 2: Convergence (300~700)
    - Phase 3: Stability (700~1,000)
- **Single-Pull Rule**: 이 지침은 최초 1회만 전달되므로, 모든 지시 사항을 완벽히 숙지한 후 수행하십시오.
- **Non-Coding Rule Compliance**: 팀장(Antigravity)은 코딩을 하지 않습니다. 모든 수정은 귀하(Jules)가 수행합니다.

## 📢 결과 보고
- 시뮬레이션 완료 후 `logs/simulation.log`에서 추출한 핵심 지표 요약.
- 학습 곡선 그래프(`reports/learning_curve.png`)의 형상에 대한 해석 (수렴 여부).
