# Strategic Parallel Roadmap: Phase 8 & Beyond

## 1. Executive Summary
This roadmap outlines the plan for resolving identified technical debt and architectural leaks, prioritized by complexity and dependency. To accelerate progress, work is divided into three parallel streams that can be executed independently by different workers (Gemini/Jules).

---

## 2. Workstream Categorization

### 🏗️ Stream A: Core Structural Purification
*Focus: Eliminating deep coupling and O(n*m) leaks.*

| ID | Task | Complexity | Priority | Dependencies |
| :--- | :--- | :--- | :--- | :--- |
| **TD-276** | **HR/Finance Agent Coupling** | 🔴 Critical | P0 | None |
| **TD-275** | **Dividend Logic (ShareholderRegistry)** | 🟠 High | P0 | None |
| **TD-270** | **Firm-Department Circular Refs** | 🟡 Medium | P1 | None |

### 🏦 Stream B: Banking & Systems Refactor
*Focus: Decomposition of god-classes and protocol enforcement.*

| ID | Task | Complexity | Priority | Dependencies |
| :--- | :--- | :--- | :--- | :--- |
| **TD-274** | **Bank Class Decomposition** | 🟡 Medium | P1 | None |
| **TD-273** | **liquid_assets Protocol Enforcement** | 🟡 Medium | P1 | None |
| **TD-125** | **FE-BE Contract Sync** | 🟠 High | P2 | None |

### 🛠️ Stream C: Infrastructure & Dev-Ex
*Focus: Orchestration, configuration, and verification.*

| ID | Task | Complexity | Priority | Dependencies |
| :--- | :--- | :--- | :--- | :--- |
| **TEST-INT**| **Audit Test Integration** | 🟡 Medium | P0 | None |
| **TD-277** | **TickOrchestrator Phase Cleanup** | 🟢 Low | P2 | None |
| **TD-268** | **BaseAgent Constructor Reform** | 🟡 Medium | P2 | None |
| **TD-265** | **Config Access Standard (YAML)** | 🟡 Medium | P3 | None |

---

## 3. Parallel Execution Plan (Proposal)

### Phase 8.1: Hardening Foundations (Immediate)
- **Worker 1 (Jules)**: [Stream C] Merge `audit-economic-integrity` and stabilize verification. (Easy-Medium)
- **Worker 2 (Gemini)**: [Stream A] Spec `ShareholderRegistry` (TD-275). (High)
- **Worker 3 (Jules/Gemini)**: [Stream B] Split `Bank` into `LoanManager` & `DepositManager` (TD-274). (Medium)

### Phase 8.2: Deep Decoupling (Follow-up)
- **Worker 1 (Gemini)**: Spec `AgentRegistry-driven HR` (TD-276). (Critical)
- **Worker 2 (Jules)**: Refactor `TickOrchestrator` phases (TD-277). (Easy)
- **Worker 3 (Jules)**: Standardize Config access (TD-265). (Medium)

---

## 4. 🚨 Risk Audit
- **Integration Risk**: TD-276 is a "breaking change" for agent state management. Must be sequenced after Stream C's audit tests are live.
- **Resource Conflict**: Stream A and Stream B touch `Firm` and `Bank` logic; ensure separate mission contexts to avoid merge hell.
