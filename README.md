# Living Economic Laboratory (LEL)

![Project Phase](https://img.shields.io/badge/Phase-16_God--Mode_Watchtower-blueviolet?style=for-the-badge)
![Build Status](https://img.shields.io/badge/Build-PASSING_(580/580)-success?style=for-the-badge)
![Architecture](https://img.shields.io/badge/Architecture-SEO_Pattern-orange?style=for-the-badge)
![Integrity](https://img.shields.io/badge/Integrity-Zero--Sum-forestgreen?style=for-the-badge)

> **"Arm the Tool, Do not be the Tool."**

The **Living Economic Laboratory** is a high-fidelity multi-agent simulation designed to reconstruct complex macroeconomic phenomena from the bottom up. Unlike traditional econometric models that rely on static equations, LEL generates economic laws (inflation, recession, growth) as emergent properties of interacting, intelligent agents.

---

## 🏛️ Architecture & Philosophy

This project is built on a strict 5-layer architecture designed to ensure data purity, causal traceability, and zero-sum financial integrity.

### 1. The Sacred Sequence (Time)
Time is treated as a physical constraint. The simulation advances through a rigid 8-step "Sacred Sequence" (`Phase 0` to `Phase 7`), ensuring that **Cognition** always precedes **Action**, and **Settlement** always follows **Execution**. This prevents causal paradoxes and race conditions.

### 2. SEO Pattern (Stateless Engine & Orchestrator)
We strictly separate concerns to prevent "God Classes":
- **State (Repository)**: Dumb data containers (Dataclasses/DTOs).
- **Logic (Engine)**: Pure, stateless functions that transform input DTOs to output DTOs.
- **Orchestration (Service)**: The glue that pulls data, invokes engines, and updates state.

### 3. Financial Fortress (Zero-Sum)
Money is never created or destroyed, only transferred. The `SettlementSystem` acts as the Single Source of Truth (SSoT) for all value exchange. Any discrepancy in the global ledger triggers an immediate `SystemHalt`.

### 4. Agent Intelligence (Dual-Layer)
Agents are not simple scripts. They possess:
- **Maslow's Hierarchy**: A prioritized needs system (Survival > Comfort > Luxury).
- **Q-Learning Strategy**: Adaptive behaviors that evolve based on market feedback.

### 5. God-Mode Watchtower
A real-time, bidirectional cockpit allows operators to observe the economy's "nervous system" and inject shocks (e.g., hyperinflation, harvest failure) to stress-test system resilience.

👉 **[Deep Dive: Platform Architecture](./design/1_governance/platform_architecture.md)**

---

## 📂 Project Structure

```text
C:\CODING\ECONOMICS
├── analysis_report/       # Generated visual artifacts & forensic reports
├── config/                # Simulation parameters (YAML) & Domain Configs
├── design/                # Architectural Decision Records (ADRs) & Specifications
│   └── 1_governance/      # Core protocols and master roadmap
├── modules/               # Source Code (Domain-Driven Design)
│   ├── api/               # Public Interfaces (Protocols)
│   ├── finance/           # Settlement, Tax, & Banking Engines
│   ├── market/            # Stateless Matching Engines (OrderBooks)
│   └── ...
├── tests/                 # Pytest Suite (Mirroring modules structure)
└── main.py                # Simulation Entry Point
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.13+
- `uv` or `pip`

### Installation

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/your-org/economics.git
    cd economics
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the Simulation**
    ```bash
    # Run a standard 365-day simulation
    python main.py --days 365
    ```

4.  **Run the Dashboard (Watchtower)**
    ```bash
    # Launch the God-Mode Cockpit
    streamlit run dashboard/app.py
    ```

---

## 🧪 Verification & Testing

The project maintains a strict **100% Pass Rate** policy.

```bash
# Run the full test suite
pytest

# Run specific domain tests
pytest tests/finance
```

**Key Testing Concepts:**
- **Golden Data**: We use pre-validated "Golden" fixtures for deterministic testing.
- **Mock Purity**: Mocks must strictly adhere to Protocols (`@runtime_checkable`).

---

## 📜 Documentation Map

| Document | Purpose |
|---|---|
| [**PROJECT_STATUS.md**](./PROJECT_STATUS.md) | Current phase, active tracks, and recent achievements. |
| [**HANDOVER.md**](./HANDOVER.md) | Critical context for new developers or session handover. |
| [**TECH_DEBT_LEDGER.md**](./design/2_operations/ledgers/TECH_DEBT_LEDGER.md) | Tracked technical debt and liquidation plans. |
| [**QUICKSTART.md**](./design/QUICKSTART.md) | Detailed setup and contribution guide. |

---

## 🤝 Contribution Guidelines

1.  **Protocol First**: Never bypass `api.py`. Use defined DTOs.
2.  **No Magic Money**: Ensure every transaction balances (`Debit == Credit`).
3.  **Test Driven**: Verify changes with `pytest` before submission.

---

*Generated by Gemini CLI (Scribe) - Phase 16*