# Work Order: (Operation Shock Therapy)

## 🏢 Context
1차 Awakening Run에서 Smart Leviathan이 "아무것도 하지 않는 것이 최선"이라는 **국소 최적해(Local Minimum)**에 빠졌습니다. 이를 해결하기 위해 **충격 요법(Shock Therapy)**을 시행합니다.

## 🎯 Objectives
1. **Epsilon Decay 구현**: 초기 0.5 → 최종 0.05, 700틱에 걸쳐 선형 감소
2. **Reward Scaling 구현**: 보상값 ×100 증폭
3. **Chaos Injection 구현**: Tick 200, 600에 경제 위기 주입
4. **1,000틱 시뮬레이션 실행 및 학습 곡선 생성**

---

## 📋 상세 구현 지침

### 1. Epsilon Decay 구현
**파일**: `simulation/ai/action_selector.py`

```python
def get_epsilon(self, current_tick: int) -> float:
 """Linear Decay: 0.5 → 0.05 over 700 ticks."""
 initial = 0.5
 final = 0.05
 decay_steps = 700

 if current_tick >= decay_steps:
 return final

 return initial - (initial - final) * (current_tick / decay_steps)
```

**파일**: `simulation/ai/government_ai.py`
- `decide_policy()`에서 `self.action_selector.choose_action()`을 호출할 때 동적 epsilon 전달

### 2. Reward Scaling 구현
**파일**: `simulation/ai/government_ai.py`

```python
def calculate_reward(self, market_data: Dict[str, Any]) -> float:
 # ... 기존 로직 ...
 loss = (0.5 * (inf_gap ** 2)) + (0.4 * (unemp_gap ** 2)) + (0.1 * (debt_gap ** 2))
 reward = -loss * 100.0 # ×100 스케일링 적용
 return reward
```

### 3. Chaos Injection 구현
**파일**: `simulation/engine.py` - `run_tick()` 메서드 내

```python
# ===== Chaos Injection Events =====
if self.time == 200:
 self.logger.warning("🔥 CHAOS: Inflation Shock at Tick 200!")
 for market_name, market in getattr(self, 'goods_markets', {}).items():
 if hasattr(market, 'current_price'):
 market.current_price *= 1.5
 if hasattr(market, 'avg_price'):
 market.avg_price *= 1.5

if self.time == 600:
 self.logger.warning("🔥 CHAOS: Recession Shock at Tick 600!")
 for household in self.households:
 household.assets *= 0.5
```

---

## 📂 관련 파일들
| 분류 | 파일 | 변경 내용 |
| :--- | :--- | :--- |
| **Target** | `simulation/ai/action_selector.py` | `get_epsilon()` 메서드 추가 |
| **Target** | `simulation/ai/government_ai.py` | Reward ×100, 동적 epsilon 적용 |
| **Target** | `simulation/engine.py` | Chaos Injection 로직 추가 |
| **Execution** | `main.py` | 시뮬레이션 실행 |
| **Analysis** | `scripts/generate_learning_curve.py` | 결과 시각화 |

---

## ⚠️ 제약 사항
- **Non-Coding Rule**: 팀장(Antigravity)은 직접 코딩하지 않습니다. 모든 구현은 귀하(Jules)가 수행합니다.
- **Single-Pull Rule**: 이 지침은 최초 1회만 전달되므로, 모든 지시 사항을 완벽히 숙지한 후 수행하십시오.

---

## 🧪 검증 기준 (Success Criteria)
1. 학습 곡선에서 **Tick 200, 600 부근 급격한 보상 하락** 확인
2. 이후 **보상 회복 추세** 확인 (Rising Slope)
3. 최종적으로 **Plateau 형성** 확인

## 📢 결과 보고
- `reports/learning_curve_v2.png` 생성
- Tick 200/600 전후 AI 행동 빈도 분석
