# Mission Guide: Protocol Enforcement (Architectural Lockdown)

## 1. Objectives (Phase 15 Lockdown)
- **Static Enforcement**: Design/Implement static analysis rules (Ruff/Mypy) to block private member access (e.g., `.inventory`, `.wallet`) from outside engines.
- **Runtime Guardrails**: Design decorators/context managers to verify protocol compliance at runtime.
- **Documentation Alignment**: Update `QUICKSTART.md` with "Mandatory Protocol" sections.

## 2. Reference Context (MUST READ)
### Governance
- [QUICKSTART.md](../../QUICKSTART.md) (Architect's Rule)
- [platform_architecture.md](../../1_governance/platform_architecture.md) (Domain boundaries)

### Implementation (Engine Pattern)
- [sales_engine.py](../../../simulation/components/engines/sales_engine.py) (Reference for SEO pattern)
- [finance_engine.py](../../../simulation/components/engines/finance_engine.py)

## 3. Implementation Roadmap
### Phase 1: Enforcement Design
- Identify high-risk "Leak" points (e.g., direct attribute access in tests or legacy agents).
- Propose a `ruff` rule configuration or a custom script to detect `.xxx_pennies` vs `.xxx` access patterns.

### Phase 2: Spec Generation
- Draft the mission for Jules to hardening the codebase.
- Propose the exact wording for the updated `QUICKSTART.md`.

## 4. Success Criteria
- A "Lockdown" script that returns non-zero exit code if any architectural violation is found.
- Updated contribution guide approved by the Architect.
