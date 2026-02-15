# Resolution Specification: Technical Debt (Float/Penny/Security)

## 1. Overview
This specification addresses three critical technical debt items identified in the pre-flight audit. It serves as the blueprint for "Jules" implementation tracks to restore architectural integrity to the simulation platform.

### Targeted Debts
1.  **TD-CRIT-FLOAT-SETTLE**: Critical Float Leak in Settlement (Crash Risk).
2.  **TD-ARCH-SEC-GOD**: God-Mode Security Vulnerability (Unauthorized Access Risk).
3.  **TD-INT-PENNIES-FRAGILITY**: Penny-Float Duality (Maintenance & Logic Risk).

---

## 2. TD-CRIT-FLOAT-SETTLE: Strict Integer Arithmetic

### 2.1. Problem Definition
The `SettlementSystem` strictly enforces `int` types for all transfers (`TypeError` on float). However, `Firm` and its sub-engines (`ProductionEngine`, `AssetManagementEngine`) currently compute and return `float` values for costs and liquidation proceeds. This necessitates ad-hoc, error-prone casting (`int()`) in the Orchestrator layer, creating a "Float Leak" risk where a float might slip through to the Settlement System, causing a crash.

### 2.2. Solution Specification
All Stateless Engines generating monetary values MUST return strictly typed `int` (pennies) in their Result DTOs.

#### 2.2.1. Updated DTOs (`modules/firm/api.py`)

```python
@dataclass
class ProductionResultDTO:
    """
    Result of a production cycle.
    """
    quantity_produced: float
    quality: float
    production_cost_pennies: int  # CHANGED: Strictly Int (was float)
    inputs_consumed: Dict[str, float]
    capital_depreciation: float
    automation_decay: float
    success: bool

@dataclass
class LiquidationResultDTO:
    """
    Result of asset liquidation calculation.
    """
    assets_returned: Dict[CurrencyCode, int] # CHANGED: Values must be int pennies
    capital_stock_to_write_off: float
    automation_level_to_write_off: float
    is_bankrupt: bool
```

### 2.3. Implementation Logic
1.  **ProductionEngine**: Perform internal calculations in `float` for precision. Finalize `production_cost` by applying `math.ceil()` (conservative cost accounting) and casting to `int`.
2.  **AssetManagementEngine**: Ensure all currency values in `assets_returned` are cast to `int`.
3.  **Firm (Orchestrator)**: Remove manual `int()` casts. Bind DTO fields directly to `SettlementSystem` calls.

---

## 3. TD-ARCH-SEC-GOD: Security Hardening

### 3.1. Problem Definition
The `SimulationServer` binds to `self.host` (potentially `0.0.0.0`) and relies solely on a `X-GOD-MODE-TOKEN` header. If the token is compromised or the port is inadvertently exposed to the public internet, the simulation is vulnerable to unauthorized command injection.

### 3.2. Solution Specification
1.  **Localhost Binding**: Enforce `127.0.0.1` as the default bind address.
2.  **Config Strictness**: Explicitly define security parameters in `ServerConfigDTO`.

#### 3.2.1. Updated Config DTO (`simulation/dtos/config_dtos.py`)

```python
@dataclass
class ServerConfigDTO:
    host: str = "127.0.0.1"  # RESTRICTED: Default to loopback
    port: int = 8000
    god_mode_enabled: bool = False
    god_mode_token: str = "" # Mandatory if enabled
    allowed_origins: List[str] = field(default_factory=lambda: ["http://localhost:3000"])
```

#### 3.2.2. Server Logic (`modules/system/server.py`)
-   **Validation**: In `__init__`, if `god_mode_enabled` is True and `host` is NOT `127.0.0.1`, log a `CRITICAL` security warning.
-   **Handshake**: Maintain existing `X-GOD-MODE-TOKEN` check.
-   **Payload**: While `GodCommandDTO` integrity is important, strict ingress isolation (Localhost + Token) is sufficient for Phase 1.

---

## 4. TD-INT-PENNIES-FRAGILITY: Protocol Standardization

### 4.1. Problem Definition
`Firm` implements both `IFinancialEntity` (Pennies) and `IFinancialAgent` (Floats). The `SettlementSystem` has to check `isinstance` for both, creating ambiguity. Tests often mock `IFinancialAgent` (easier with floats), leading to "Mock Drift" where tests pass but production (using Pennies) fails.

### 4.2. Solution Specification
1.  **Primary Protocol**: `IFinancialEntity` (Pennies) is the Canonical Interface.
2.  **Deprecation**: `IFinancialAgent` (Floats) is Deprecated.
3.  **Unified State**: `Firm` must store state *only* in `Wallet` (Ints). Float properties are read-only computed views.

#### 4.2.1. Firm Interface Refactoring (`simulation/firms.py`)

```python
class Firm(IFinancialEntity, ...):
    # Canonical Source of Truth
    @property
    def balance_pennies(self) -> int:
        return self.wallet.get_balance(DEFAULT_CURRENCY)

    # --- DEPRECATED INTERFACE (IFinancialAgent) ---
    @property
    def assets(self) -> float:
        """
        DEPRECATED: Use balance_pennies.
        View-only adapter for legacy UI/Tests.
        """
        return self.balance_pennies / 100.0

    def get_balance(self, currency: CurrencyCode = DEFAULT_CURRENCY) -> float:
        """DEPRECATED"""
        return self.wallet.get_balance(currency) / 100.0
```

---

## 5. Parallel Execution Plan (Jules Tracks)

| Track | Owner | Scope | Key Tasks |
| :--- | :--- | :--- | :--- |
| **A: Settlement & Logic** | **Jules-1** | `Firm`, `ProductionEngine`, `AssetManagementEngine` | 1. **Refactor Engines**: Update `ProductionResultDTO` & `LiquidationResultDTO` to `int`.<br>2. **Update Firm**: Remove manual casts, use new DTO fields.<br>3. **Deprecate Protocol**: Mark `IFinancialAgent` methods in `Firm`. |
| **B: Security & Infra** | **Jules-2** | `SimulationServer`, `Config` | 1. **Update Config**: Implement `ServerConfigDTO` with strict defaults.<br>2. **Harden Server**: Implement Host binding check & warning.<br>3. **Verify**: Test connection rejection without token. |

---

## 6. Risk & Impact Audit (Architecture Insights)

### 6.1. Risks
-   **Legacy Test Breakage**: Tests relying on `Firm.assets` (float setter) will fail as it becomes read-only or deprecated. **Mitigation**: Update tests to use `deposit`/`withdraw` or `wallet` manipulation.
-   **Household Agent Duality**: This spec only covers `Firm`. `Household` likely suffers the same Penny/Float duality. **Risk**: `SettlementSystem` changes might break `Household` if it doesn't implement `IFinancialEntity`. **Mitigation**: `SettlementSystem` must retain `IFinancialAgent` fallback (with warning) until Phase 2.

### 6.2. Architecture Decision Record (ADR)
-   **ADR-001**: Monetary values in Engine DTOs are strictly `int` (Pennies).
-   **ADR-002**: Simulation Server defaults to `localhost` binding for security.

---

## 7. Verification Plan (Test Evidence)

*(To be filled by Implementation Agent)*

### 7.1. Critical Test Cases
-   `tests/modules/firm/test_production_int_cost.py`: Verify `ProductionEngine` returns `int` cost and `Firm` accepts it without error.
-   `tests/system/test_server_security.py`: Verify `SimulationServer` binds to `127.0.0.1` and rejects invalid tokens.
-   `tests/simulation/test_settlement_types.py`: Verify `SettlementSystem` rejects `float` amounts with `TypeError`.

### 7.2. Evidence Log
```text
[PENDING IMPLEMENTATION - LOGS WILL APPEAR HERE]
```