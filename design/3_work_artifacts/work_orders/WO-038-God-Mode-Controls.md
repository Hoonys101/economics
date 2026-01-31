# Work Order: - God Mode Controls

## Phase: 20.5 Step 2 (Stabilization)

## Objective
Sidebar의 슬라이더 조작을 통해 시뮬레이션 파라미터를 실시간으로 변경한다.

---

## 1. `dashboard/app.py` Update (UI)

### Sidebar 구성:
- **Demographics:** `Education Level` (Mean), `Marriage Age`
- **Economics:** `Income Tax Rate`, `Inheritance Tax Rate`
- **Tech/Social:** `Formula Tech Level` (0.0~1.0), `Lactation Barrier`

### State Binding:
- 각 슬라이더의 값을 `st.session_state['params']` 딕셔너리에 바인딩.

### Action:
- "Apply Parameters" 버튼 클릭 시 `connector.update_params()` 호출.

---

## 2. `dashboard_connector.py` Update (Bridge)

### New Method:
```python
def update_params(simulation: Simulation, new_params: dict) -> None:
 """
 Updates simulation configuration at runtime.
 """
 for key, value in new_params.items():
 if hasattr(simulation.config_module, key):
 setattr(simulation.config_module, key, value)
 logger.info(f"[Dashboard] Updated config: {key} -> {value}")
 else:
 logger.warning(f"[Dashboard] Unknown config key: {key}")
```

---

## 3. Verification
- 슬라이더를 움직이고 적용했을 때, 다음 틱의 로그나 메트릭에서 변경된 수치가 반영되는지 확인.
- Example: `FORMULA_TECH_LEVEL`을 0.0 -> 1.0으로 변경 후 100틱 진행, 출산율 변화 관측.

---

## Deliverables
- Updated `dashboard/app.py` with sliders.
- Updated `dashboard_connector.py` with `update_params()`.
- Screenshot or log showing parameter change reflected in simulation.
