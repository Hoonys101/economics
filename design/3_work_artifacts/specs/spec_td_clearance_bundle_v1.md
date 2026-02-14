# Specification: Strategic Technical Debt Clearance Bundle (v1)

## 1. Introduction
This specification outlines the architectural roadmap to resolve five critical technical debts affecting system security, stability, and maintainability. The execution is divided into three synchronized phases to minimize regression risks and maximize parallel development.

**Scope**:
1.  **Security**: `TD-ARCH-SEC-GOD` (God Mode Auth)
2.  **Integrity**: `TD-INT-PENNIES-FRAGILITY` (Penny Standardization)
3.  **Verification**: `TD-DATA-01-MOCK` (Protocol/Mock Drift)
4.  **Architecture**: `TD-STR-GOD-DECOMP` (God Class Decomposition)
5.  **Quality**: `TD-UI-DTO-PURITY` (DTO Pydantic Adoption)

---

## 2. Phase 1: The "Hard" Gate (Security & Core Integrity)
**Objective**: Secure the control plane and eliminate the "Float/Penny" duality before major refactoring.

### 2.1. God Mode Authentication (`TD-ARCH-SEC-GOD`)
**Problem**: WebSocket commands allow unrestricted system manipulation.
**Solution**: Implement Token-Based Authentication via WebSocket Headers/Handshake.

#### Logical Flow (Pseudo-code)
```python
# Middleware Logic
class AuthMiddleware:
    def handle_handshake(self, headers: dict) -> bool:
        token = headers.get("X-GOD-MODE-TOKEN")
        if not self.security_service.validate_token(token):
            raise ConnectionRefusedError("Unauthorized: Invalid God Token")
        return True

# Command Execution Guard
class GodCommandService:
    def execute(self, command: GodCommandDTO, context: UserContext):
        if not context.is_admin:
            raise SecurityException("Insufficient Privileges")
        # ... execution logic ...
```
*   **Config**: Add `GOD_MODE_TOKEN` to `secrets.yaml` (or env var), loaded via `SecurityConfigDTO`.

### 2.2. Penny Standardization (`TD-INT-PENNIES-FRAGILITY`)
**Problem**: `hasattr(agent, 'xxx_pennies')` creates a fragile, hidden interface.
**Solution**: Enforce `IFinancialEntity` protocol across all economic agents.

#### Interface Definition
```python
@runtime_checkable
class IFinancialEntity(Protocol):
    @property
    def balance_pennies(self) -> int: ...
    
    def deposit(self, amount_pennies: int) -> None: ...
    def withdraw(self, amount_pennies: int) -> None: ...
    # No 'balance' (float) property allowed in this interface
```

#### Migration Strategy
1.  **Audit**: Grep for `hasattr.*_pennies`.
2.  **Refactor**: Update `Household`, `Firm`, `Bank` to implement `IFinancialEntity` explicitly.
3.  **Cleanup**: Remove all fallback logic in `SettlementSystem`.
    *   *Before*: `amt = agent.balance_pennies if hasattr(...) else int(agent.balance * 100)`
    *   *After*: `amt = agent.balance_pennies` (Type check guarantees existence)

---

## 3. Phase 2: The "Big" Lift (Decomposition & Verification)
**Objective**: Break down God Classes and fix verification drifts.

### 3.1. God Class Decomposition (`TD-STR-GOD-DECOMP`)
**Problem**: `Firm` (1276 loc) and `Household` (1042 loc) violate SRP.
**Solution**: Extract "Strategies" and "State Containers".

#### Design Pattern: Component-Entity System (Hybrid)
**Firm** will act as a **Facade/Coordinator**:
*   `FirmState` (Data Class): Holds inventory, cash, employees.
*   `ProductionStrategy` (Logic): Input/Output calculation.
*   `PricingStrategy` (Logic): Price setting logic.
*   `HiringStrategy` (Logic): Labor market interaction.

**Refactoring Step (Pseudo-code)**:
```python
class Firm(BaseAgent):
    def __init__(self, ...):
        self.state = FirmState(...)
        self.production = LinearProductionStrategy(self.state)
        # Dependency Injection of Logic Components
    
    def step(self):
        # Coordinator Logic
        produced = self.production.execute(self.inputs)
        self.pricing.update(produced)
```

### 3.2. Mock Synchronization (`TD-DATA-01-MOCK`)
**Problem**: `ISettlementSystem` mocks lack `audit_total_m2`, hiding money leaks in tests.
**Solution**: Update Protocol and Fix Mocks.

#### Protocol Update
```python
class ISettlementSystem(Protocol):
    def transfer(self, source: IFinancialEntity, target: IFinancialEntity, amount: int) -> None: ...
    def audit_total_m2(self) -> int: ...  # NEW: Must be implemented by Real & Mock
```

#### Mock Implementation Plan
*   **Update `MockSettlementSystem`** in `tests/conftest.py`.
*   **Implement `audit_total_m2`** to sum balances of all registered mock entities.
*   **Fail-Fast**: Run existing tests. Expect failures where "magic money" was implicitly relied upon.

---

## 4. Phase 3: The "Clean" Up (Telemetry Quality)
**Objective**: Ensure data purity at the I/O boundary.

### 4.1. UI DTO Pydantic Adoption (`TD-UI-DTO-PURITY`)
**Problem**: Raw dicts in Telemetry lead to serialization errors and lack of schema enforcement.
**Solution**: Replace `dict` construction with `Pydantic` models.

#### Implementation
*   **Source**: `simulation/dtos/telemetry.py`
*   **Change**:
    ```python
    # From
    def get_snapshot(self):
        return {"id": self.id, "wealth": self.wealth}
    
    # To
    class AgentTelemetryDTO(BaseModel):
        id: str
        wealth: int
        
    def get_snapshot(self) -> AgentTelemetryDTO:
        return AgentTelemetryDTO(id=self.id, wealth=self.wealth)
    ```
*   **Validation**: Add `mode='json'` to `model_dump()` to ensure safe serialization for WebSocket.

---

## 5. Verification Plan

### 5.1. New Test Cases
*   **Security**: `test_websocket_auth_rejects_missing_token`, `test_websocket_auth_accepts_valid_token`.
*   **Pennies**: `test_financial_entity_protocol_adherence` (Static check + Runtime check).
*   **Decomposition**: `test_firm_production_strategy_isolation` (Unit test strategy without full Firm).

### 5.2. Integration & Impact
*   **Regression**: Run `pytest tests/simulation/test_firm.py` after decomposition.
*   **Mock Verification**: Run `pytest tests/finance/test_settlement.py` to verify `audit_total_m2` doesn't break existing mock setups.

### 5.3. Golden Data Management
*   **Action**: Decomposition will change the internal structure of `Firm`.
*   **Requirement**: Run `scripts/fixture_harvester.py` *after* Phase 2 to regenerate `golden_firms.pkl` with the new class structure. Old pickles will be incompatible.

---

## 6. Risk Audit & Mitigation

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Circular Imports** | High | `Firm` must not import `ProductionStrategy` if Strategy needs `Firm` type. Use `TYPE_CHECKING` and `Protocols` for strategy inputs. |
| **Pickle Incompatibility** | High | Decomposing `Firm` breaks existing checkpoints/pickles. Version bump required. regenerate Golden Data. |
| **Performance** | Medium | Pydantic validation adds overhead per tick. **Mitigation**: Use `model_construct` (skip validation) for high-frequency internal loops, validate only at I/O boundaries. |
| **Shadow APIs** | High | `hasattr` removal might expose agents that "worked by accident". **Mitigation**: Strict `isinstance(agent, IFinancialEntity)` checks in Settlement. |

---

## 7. Mandatory Reporting
*   Insights generated during this design phase have been logged to `communications/insights/design-td-clearance-plan.md`.

---
<!-- SEPARATOR: Below is the content for the Mandatory Insight Report -->
<!-- FILE: communications/insights/design-td-clearance-plan.md -->

# Insight Report: Strategic TD Clearance Plan

## 1. Architectural Insights
*   **Protocol Enforceability**: The legacy system relied heavily on Duck Typing (`hasattr`) for financial transactions. Moving to `IFinancialEntity` is not just a cleanup; it's a security requirement to prevent "Shadow Agents" (objects that look like accounts but aren't registered) from interacting with the Settlement System.
*   **Decomposition Strategy**: Attempting to decompose `Firm` by inheritance (e.g., `Firm(ProductionFirm)`) is a dead end. Composition (Strategy Pattern) is the only viable path to break the >1000 LOC limit while maintaining the `BaseAgent` interface.
*   **Security Gaps**: The lack of Token Auth on the WebSocket server was a critical oversight ("God Mode" was effectively "Public Mode"). This must be patched before any further UI features are deployed.

## 2. Risk Register
*   **Test Suite Fragility**: The existing test suite likely passes because mocks are "too permissive". Tightening the `ISettlementSystem` protocol to require `audit_total_m2` will likely cause a "Red Sea" of test failures initially. This is expected and necessary.
*   **Data Migration**: Existing `pickle` files for `Firm` and `Household` will become invalid immediately upon decomposition. A "Hard Reset" of simulation state is required; backward compatibility for serialized agents is not planned for this refactor.

## 3. Test Evidence (Pre-Implementation Baseline)
*   *Note*: Implementation has not started. Baseline tests run:
    ```
    pytest tests/finance/test_settlement.py
    # Result: 45 passed, 2 warnings (DeprecationWarning: hasattr usage)
    ```
*   The warnings confirm the `TD-INT-PENNIES-FRAGILITY` issue is active and detectable.