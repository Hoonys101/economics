# WORK ORDER: WO-057-C (The Actuator)

**To:** Jules Charlie
**Role:** Actuator Module Developer & Safety Engineer
**Status:** [ ] Draft [ ] Assigned [ ] In-Progress [ ] Completed

---

## 🏗️ Mission: "The Moving Hand"
Brain(Alpha)이 내리는 추상적 인덱스 명령을 현실의 경제 정책 수단(금리, 세율)으로 변환하고 집행하는 **Actuator Module**을 구현하십시오. 

당신의 최우선 가치는 **'안전(Safety)'**입니다. 급격한 정책 변화로부터 경제 시스템을 보호하는 베이비스텝(Baby Step) 원칙을 코드로 구현해야 합니다.

---

## 🛠️ Technical Specs

### 1. 📂 Context & Files
| 분류 | 경로 | 역할 |
| :--- | :--- | :--- |
| **Source** | `simulation/ai/government_ai.py` | 5개 Action의 정의 확인 |
| **Contract** | `simulation/interfaces/policy_interface.py` | `IGovernmentPolicy` 인터페이스 준수 |
| **Destination** | `simulation/policies/smart_leviathan_policy.py` | Actuator 로직 구현 위치 |

### 2. 🧠 Translation Logic (Brain Index -> Policy Delta)
`government_ai.py`에서 정의된 `action_idx`를 다음 정책 변화량으로 매핑하십시오.

- `0 (Dovish)`: `market_data["central_bank"].base_rate` -= 0.0025 (0.25%p)
- `1 (Neutral)`: No Change
- `2 (Hawkish)`: `market_data["central_bank"].base_rate` += 0.0025 (0.25%p)
- `3 (Fiscal Ease)`: `government.tax_rate` -= 0.01 (1.0%p)
- `4 (Fiscal Tight)`: `government.tax_rate` += 0.01 (1.0%p) & `government.budget_allocation` -= 0.05 (5%)

### 3. 🛡️ Safety Valve (Clipping & Bounds)
- **금리 한계**: `0.0 (0%)` ~ `0.20 (20%)` 사이로 `clamp` (마이너스 금리 절대 금지)
- **세율 한계**: `0.05 (5%)` ~ `0.50 (50%)` 사이로 `clamp`
- **예산 배정**: `0.1 (10%)` ~ `1.0 (100%)` 사이로 `clamp` (국가 최소 유지비 보장)
- **로깅**: 정책 변경 시 `logger.info`를 통해 변경 전/후 수치를 명확히 기록하십시오.

### 4. ⏱️ Action Interval (Policy Throttling)
- `config.GOV_ACTION_INTERVAL` (기본 30틱) 주기를 Actuator 레벨에서 강제하십시오.
- `current_tick % config.GOV_ACTION_INTERVAL != 0` 인 경우, `Brain`에 연산을 요청하지 않고 직전 정책을 유지하거나 `return` 합니다.

---

## 🧪 Verification Tasks
1. **Unit Test**: `tests/test_government_actuator.py`를 작성하여 30틱 주기성과 Clipping 로직을 검증하십시오.
2. **Logging Check**: 시뮬레이션 실행 시 정책 변경 로그가 "BABY_STEP | Rate: 0.050 -> 0.0525" 형식으로 남는지 확인하십시오.

---

> [!IMPORTANT]
> 정책을 결정할 때 `market_data["central_bank"]` 객체를 통해 `base_rate`를 직접 조정해야 함을 잊지 마십시오. (정부는 중앙은행에 대한 지배력을 가짐)

**Execute with Precision.**
