# Work Order: WO-HOTFIX-Test-Coverage

## Priority: IMMEDIATE (Before )

## Objective
누락된 Headless 검증 스크립트 작성.

## Tasks
1. Create `tests/verify_dashboard_connector.py`.
2. **Scenario:**
 - Import `dashboard_connector` module.
 - Call `get_engine_instance()` and verify the returned object is a valid `Simulation` instance.
 - Call `run_tick(engine)` once and verify it returns an integer (new tick number).
 - Call `get_metrics(engine)` and verify the returned dict contains keys: `tick`, `total_population`, `gdp`, `average_assets`, `unemployment_rate`.
3. **Constraint:** Must pass without Streamlit/Browser. Pure Python execution via `pytest`.

## Verification
```bash
pytest tests/verify_dashboard_connector.py -v
```

## Deliverable
- `tests/verify_dashboard_connector.py` committed and pushed.
