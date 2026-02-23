# Technical Debt Ledger (TECH_DEBT_LEDGER.md)

## 📑 Table of Contents
1. [Core Summary Table](#-core-summary-table)
2. [Architecture & Infrastructure](#architecture--infrastructure)
3. [Financial Systems (Finance & Transactions)](#financial-systems-finance--transactions)
4. [AI & Economic Simulation](#ai--economic-simulation)
5. [Market & Systems](#market--systems)
6. [Lifecycle & Configuration](#lifecycle--configuration)
7. [Testing & Quality Assurance](#testing--quality-assurance)
8. [DX & Cockpit Operations](#dx--cockpit-operations)

---

## 📊 Core Summary Table

| ID | Module / Component | Description | Priority / Impact | Status |
| :--- | :--- | :--- | :--- | :--- |
| **TD-ARCH-GOV-MISMATCH** | Architecture | **Singleton vs List**: `WorldState` has `governments` (List) vs Singleton `government`. | **Medium**: Logic Drift. | Open |
| **TD-INT-BANK-ROLLBACK** | Finance | **Rollback Coupling**: Bank rollback logic dependent on `hasattr` implementation. | **Low**: Leak. | Open |
| **TD-SYS-ACCOUNTING-GAP** | Systems | `accounting.py` misses tracking buyer expenses. | **Medium**: Accuracy. | Open |
| **TD-ECON-M2-INV-BUG** | Economic | **M2 Audit Logic**: `audit_total_m2` naively sums negative balances. | **CRITICAL**: Integrity. | **RESOLVED** |
| **TD-SYS-BATCH-RACE** | Finance | **Atomic Batch Race**: Multiple withdrawals in a batch bypass balance checks. | **High**: Soundness. | **RESOLVED** |
| **TD-TEST-TX-MOCK-LAG** | Testing | **Transaction Test Lag**: `test_transaction_engine.py` mocks are out of sync. | **Low**: Flakiness. | Identified |
| **TD-TEST-TAX-DEPR** | Testing | **Deprecated Tax API in Tests**: `test_transaction_handlers.py` still uses `collect_tax`. | **Medium**: Tech Debt. | Identified |
| **TD-ECON-INSTABILITY-V2** | Economic | **Rapid Collapse**: Sudden Zombie/Fire Sale clusters despite high initial assets. | **High**: Logic Drift. | **IDENTIFIED** |
| **TD-ARCH-ORCH-HARD** | Architecture | **Orchestrator Fragility**: `TickOrchestrator` lacks hardening against missing DTO attributes in mocks. | **Medium**: Resilience. | **NEW (PH21)** |
| **TD-ARCH-SETTLEMENT-BLOAT** | Architecture | **Settlement Overload**: `SettlementSystem` handles orchestration, ledgers, metrics, and indices. | **High**: Maintainability. | **RESOLVED (PH4.1)** |
| **TD-CONFIG-HARDCODED-MAJORS** | Configuration | **Hardcoded Majors**: `MAJORS` list hardcoded in `labor/constants.py` instead of yaml. | **Low**: Flexibility. | **RESOLVED (PH4.1)** |
| **TD-ECON-M2-REGRESSION** | Economic | **M2 Negative Inversion**: `calculate_total_money()` sums negative balances. | **CRITICAL**: Integrity. | **SPECCED (PH22)** |
| **TD-FIN-SAGA-REGRESSION** | Finance | **Saga Drift**: Sagas skipped due to missing/dead participant IDs. | **High**: Protocol. | **SPECCED (PH22)** |
| **TD-LIFECYCLE-GHOST-FIRM** | Lifecycle | **Ghost Firm Bug**: Transactions precede registration during startup. | **CRITICAL**: Integrity. | **SPECCED (PH22)** |
| **TD-BANK-RESERVE-CRUNCH** | Finance | **Reserve Constraint**: Bank 2 lacks reserves (1M) to fund infrastructure bonds (8M+). | **Medium**: Logic. | **NEW** |
| **TD-ECON-ZOMBIE-FIRM** | Economic | **Firm Extinction**: Rapid collapse of basic_food firms causing FIRE_SALE spam. | **High**: Balance. | **NEW** |
| **TD-ARCH-SEO-LEGACY** | Firm | **Legacy SEO Gap**: `brain_scan` skips legacy decision logic unless mocked. | **Medium**: AI Integrity. | **NEW (PH4.1)** |
| **TD-TEST-DTO-MOCK** | Testing | **DTO Hygiene**: `tests/test_firm_brain_scan.py` uses permissive `MagicMock` for DTOs. | **Low**: Stability. | **RESOLVED (PH4.1)** |
| **TD-LIFECYCLE-NAMING** | Lifecycle | **Variable Naming**: `capital_stock_pennies` multiplied by 100, implies units. | **Medium**: Inflation. | **NEW (PH4.1)** |
| **TD-LABOR-METADATA** | Market | LaborMarket uses `Order.metadata` for Major matching instead of DTO. | **Low**: Typing. | **NEW (PH4.1)** |
| **TD-FIN-MAGIC-BASE-RATE** | Finance | `FinanceSystem.issue_treasury_bonds` uses hardcoded `0.03`. | **Low**: Config. | Identified |
| **TD-WAVE3-DTO-SWAP** | DTO | **IndustryDomain Shift**: Replace `major` with `IndustryDomain` enum. | **Medium**: Structure. | **SPECCED** |
| **TD-WAVE3-TALENT-VEIL** | Agent | **Hidden Talent**: `EconStateDTO` missing `hidden_talent`. | **High**: Intent. | **SPECCED** |
| **TD-WAVE3-MATCH-REWRITE** | Market | **Bargaining vs OrderBook**: Existing LaborMarket assumes sorting. | **High**: Economy. | **SPECCED** |
| **TD-FIN-INVISIBLE-HAND** | Finance | **Initialization Order**: CB/PublicManager registered after AgentRegistry snapshot. | **CRITICAL**: Runtime failure. | **NEW (AUDIT)** |
| **TD-MARKET-FLOAT-TRUNC** | Market | **Wealth Destruction**: `MatchingEngine` truncates fractional pennies via `int()`. | **High**: Deflationary bias. | **NEW (AUDIT)** |
| **TD-SYS-ANALYTICS-DIRECT** | Systems | **Stateless Bypass**: `AnalyticsSystem` calls agent methods instead of using DTO snapshots. | **Medium**: Pattern violation. | **NEW (AUDIT)** |
| **TD-DX-CONTEXT-BLOAT** | DX / Infra | **Context Bloat**: `git-go` review injects full `.py` source files (~30 files) instead of lightweight `.pyi` stubs. | **Medium**: Token waste / Review quality. | **NEW** |
| **TD-DX-RECORD-REVENUE-DICT** | DTO Hygiene | **Dict→DTO Migration**: `record_revenue` called with raw `dict` instead of `TaxCollectionResult` DTO. | **High**: Runtime crash. | **RESOLVED** |
| **TD-SYS-TRANSFER-HANDLER-GAP** | Systems | **Handler Omission**: Simple "transfer" type transactions lack a handler in `TransactionProcessor`. | **CRITICAL**: Accounting Invisibility. | **NEW (WV5)** |

---

## Architecture & Infrastructure
---
### ID: TD-ARCH-SETTLEMENT-BLOAT
- **Title**: SettlementSystem Responsibility Overload
- **Symptom**: `SettlementSystem` handles transaction orchestration, ledger delegation, internal bank indexing (`_bank_depositors`), and metrics.
- **Risk**: High coupling makes future FX/Market expansions (multi-hop swaps) difficult to test and maintain.
- **Solution**: Extract `BankRegistry` and `MetricsRecording` into dedicated services. Keep `SettlementSystem` purely for orchestration.
- **Status**: RESOLVED (Phase 4.1)

### ID: TD-ARCH-GOV-MISMATCH
- **Title**: Singleton vs List Mismatch
- **Symptom**: `WorldState` has `governments` (List) vs Singleton `government`.
- **Risk**: Logic Fragility.
- **Solution**: Standardize on a single representation for government access.

---

## Financial Systems (Finance & Transactions)
---
### ID: TD-CRIT-FLOAT-CORE (M&A Expansion)
- **Title**: M&A and Stock Market Float Violation
- **Symptom**: `MAManager` passes `float` offer prices to settlement, causing errors.
- **Risk**: Runtime crash during hostile takeovers or mergers.
- **Solution**: Quantize all valuations using `round_to_pennies()`.

### ID: TD-FIN-SAGA-REGRESSION
- **Title**: Saga Participant Drift (Regression)
- **Symptom**: Massive spam of `SAGA_SKIP` logs with missing participant IDs. Sagas persist references to dead/failed agents.
- **Risk**: Transactions fail to complete; orphaned processes consume compute cycles.
- **Solution**: Re-verify ID propagation in `TickOrchestrator`. Implement saga cleanup for dead participants.
- **Status**: SPECCED (Phase 22)

### ID: TD-BANK-RESERVE-CRUNCH
- **Title**: Bank Reserve Structural Constraint
- **Symptom**: `BOND_ISSUANCE_FAILED` because Bank 2 only has 1,000,000 pennies in reserves but tries to issue bonds for 8M - 40M.
- **Risk**: Macroeconomic scale of the government is completely stunted because central/commercial banks lack fractional elasticity.
- **Solution**: Implement proper fractional reserve system or inject more liquidity early on.
- **Status**: NEW

### ID: TD-INT-BANK-ROLLBACK
- **Title**: Rollback Coupling
- **Symptom**: Bank rollback logic dependent on `hasattr` implementation details.
- **Risk**: Abstraction Leak.
- **Solution**: Move rollback logic to `TransactionProcessor` and use strict protocols.

### ID: TD-FIN-MAGIC-BASE-RATE
- **Title**: Magic Number for Base Interest Rate
- **Symptom**: `FinanceSystem.issue_treasury_bonds` uses a hardcoded `0.03` fallback when no banks are available.
- **Risk**: Lack of configurability and transparency.
- **Solution**: Define a named constant in `modules.finance.constants`.
- **Status**: Identified (Follow-up from BankRegistry Extraction)


## AI & Economic Simulation
---
### ID: TD-ECON-M2-REGRESSION
- **Title**: M2 Negative Inversion (Regression)
- **Symptom**: Aggregate money supply goes negative (`Current: -153521427.00`).
- **Risk**: Deflationary spiral, math errors in interest calculation.
- **Solution**: Update `calculate_total_money()` to `Sum(max(0, balance_i))`. Track negative balances as `SystemDebt`, not M2 deduction.
- **Status**: SPECCED (Phase 22)

### ID: TD-ECON-ZOMBIE-FIRM
- **Title**: Rapid Extinction of basic_food Firms
- **Symptom**: Firms (e.g., Firm 121, 122) trigger `FIRE_SALE` continually, go `ZOMBIE` (cannot afford wage), and then `FIRM_INACTIVE` within the first 30 ticks.
- **Risk**: Destruction of the simulation economy early in the run.
- **Solution**: Re-tune pricing constraints, initial reserves, or labor cost expectations specifically for essential goods.
- **Status**: NEW

### ID: TD-LABOR-METADATA
- **Title**: Order Metadata Refactor for Labor Matches
- **Symptom**: The `LaborMarket` currently uses `Order.metadata` to pass major information rather than strongly typed logic.
- **Risk**: Abstraction leak in the order pipeline. 
- **Solution**: Refactor to pass Major information through native DTOs.
- **Status**: NEW

### ID: TD-SYS-ACCOUNTING-GAP
- **Title**: Missing Buyer Expense Tracking
- **Symptom**: `accounting.py` fails to track expenses for raw materials on the buyer's side.
- **Risk**: Asymmetric financial logging that complicates GDP and profit analyses.
- **Solution**: Update Handler and `accounting.py` to ensure reciprocal debit/credit logging.

### ID: TD-ECON-M2-INV
- **Title**: M2 Negative Inversion
- **Symptom**: Aggregate money supply becomes negative when debt > cash.
- **Risk**: Simulation logic breaks (interest rates, policy) when "Money" is negative.
- **Solution**: Distinguish Liquidity from Liability in `calculate_total_money()`.


## Lifecycle & Configuration
---
### ID: TD-LIFECYCLE-GHOST-FIRM
- **Title**: Atomic Startup Failure (Ghost Firm Bug)
- **Symptom**: `SETTLEMENT_FAIL | Engine Error: Destination account does not exist: [IDs]`.
- **Risk**: Capital injections fail silently, leaving firms in "Zombie" states. Investor funds may be debited without corresponding credit.
- **Solution**: Implement `FirmFactory` to ensure Registration -> Bank Account Opening -> Injection sequence is atomic and blocking.
- **Status**: SPECCED (Phase 22)

### ID: TD-CONFIG-HARDCODED-MAJORS
- **Title**: Hardcoded Labor Majors
- **Symptom**: `MAJORS` list is currently hardcoded in `modules/labor/constants.py`.
- **Risk**: Adding new sectors requires code changes rather than just adjusting `economy_params.yaml`.
- **Solution**: Move `MAJORS` definitions to `economy_params.yaml` or a dedicated sector config file.
- **Status**: RESOLVED (Phase 4.1)

---

## DX & Cockpit Operations
---
### ID: TD-DX-CONTEXT-BLOAT
- **Title**: Git-Review Context Injection Bloat (`.pyi` Stub Migration)
- **Symptom**: `git-go.bat` 리뷰 시 `get_core_contract_paths()`가 전체 `.py` 소스 파일(예: `modules/finance/api.py` 1046줄)을 컨텍스트로 주입. 도메인 횡단 PR의 경우 30개 이상의 전체 파일이 주입되어 토큰 비용 급증 및 리뷰 품질 저하.
- **Root Cause**: `.pyi` 스텁 파일이 존재하지 않으며, `context.py`가 경량 대안 없이 전체 소스를 직접 읽음.
- **Solution**:
  1. **스텁 자동 생성**: 각 `api.py` / `dtos.py`에서 클래스/메서드 시그니처만 추출한 `.pyi` 스텁 파일 자동 생성.
  2. **Mtime 기반 무효화**: 스텁 파일이 없거나, 스텁 파일의 수정 시간(mtime)이 원본 소스보다 오래된 경우에만 스텁을 재생성.
  3. **`get_core_contract_paths()` 수정**: `.py` 대신 `.pyi`를 우선 탐색하여 컨텍스트에 주입.
- **Impact**: 컨텍스트 토큰 사용량 ~90% 감소 예상, 리뷰 정확도 향상.
- **Priority**: Medium
- **Status**: NEW

### ID: TD-SYS-TRANSFER-HANDLER-GAP
- **Title**: Generic Transfer Handler Omission
- **Symptom**: `SettlementSystem._create_transaction_record` hardcodes `transaction_type="transfer"`. The `TransactionProcessor` lacks a handler for this type, causing P2P transfers to be silently skipped during ledger processing.
- **Risk**: Absolute accounting failure for non-market transfers. The `MonetaryLedger` only sees transactions with specialized handlers (LLR, Tax, Goods), creating a massive "dark pool" of money movement.
- **Solution**: Register a `DefaultTransferHandler` in `initializer.py` or update `SettlementSystem` to use specific types for all operations.
- **Status**: NEW (Wave 5 Audit)

---
> [!NOTE]
> ✅ **Resolved Debt History**: For clarity, all resolved technical debt items and historical lessons have been moved to [TECH_DEBT_HISTORY.md](./TECH_DEBT_HISTORY.md).
