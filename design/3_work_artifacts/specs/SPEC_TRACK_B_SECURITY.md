# Mission Guide: Track B - Security & Infra Hardening

## 1. Objectives
- **TD-ARCH-SEC-GOD**: Harden `SimulationServer` by enforcing localhost binding and strict security config.

## 2. Reference Context (MUST READ)
- **Primary Spec**: `design/3_work_artifacts/specs/RESOLUTION_STRATEGY_PHASE_18.md` (Section 3)
- **Affected Files**:
    - `simulation/dtos/config_dtos.py` (ServerConfigDTO)
    - `modules/system/server.py` (Server implementation)

## 3. Implementation Roadmap
### Phase 1: Config Hardening
- Update `ServerConfigDTO` in `simulation/dtos/config_dtos.py` to default `host` to `127.0.0.1`.
- Ensure `god_mode_token` is handled securely.
### Phase 2: Server Enforcement
- Update `SimulationServer` in `modules/system/server.py` to check `host` binding.
- Add critical logs if security constraints are violated.

## 4. Verification
- Run: `pytest tests/system/test_server_security.py`
