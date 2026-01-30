# 🦅 Project Apex: The Living Economic Laboratory

**Project Apex** is a state-of-the-art, AI-driven macro-economic simulation engine. Unlike traditional formulaic models, Apex treats the economy as a **complex adaptive system** where thousands of autonomous agents—households, firms, banks, and governments—interact in real-time to create emergent economic phenomena.

> "We don't just calculate numbers; we simulate behavior."

---

## 🌟 Vision: Why Project Apex?
The global economy is too complex for static equations. Project Apex was built to:
- **Analyze Emergent Behavior**: Observe how individual greed, fear, and Maslow-inspired needs translate into inflation, cycles, and crises.
- **Stress-Test Policy**: Inject radical fiscal/monetary shocks to verify the resilience of the "Great Moderator" stabilizer system.
- **Bridge AI & Economics**: Use Reinforcement Learning (Q-Learning) to give agents "intelligence," allowing them to adapt their strategies as markets evolve.

---

## 🚀 Quick Start

### 1. Installation
```powershell
# Clone and install dependencies
git clone https://github.com/Hoonys101/economics.git
cd economics
pip install -r requirements.txt
```

### 2. Run Headless Simulation
Execute the core engine to see a standard run:
```powershell
python main.py
```

### 3. Launch the Web Dashboard
Visualize the economy in real-time (GDP, Volume, Inflation graphs):
```powershell
streamlit run dashboard/app.py
```
*Access via `http://localhost:8501`*

---

## 🧪 Injecting Scenarios & Stress Tests
Project Apex uses a **Scenario-Driven** approach. You can inject specific macro-economic shocks (e.g., hyperinflation, labor strikes, tech revolutions) via YAML/JSON configurations.

### How to Run a Specific Scenario:
```powershell
# Example: Run a Perfect Storm stress test
python scripts/run_phenomena_analysis.py --scenario config/scenarios/stress_test_phenomena.yaml
```

**Available Scenarios (`config/scenarios/`):**
- `golden_era_init.json`: A baseline state of stable growth.
- `phase29_depression.json`: A liquidity-starved crisis scenario.
- `stress_test_phenomena.yaml`: A modular reporting run focusing on Resilience Indices.

---

## 📊 Observation: Phenomena Reporting
We have moved beyond simple "Pass/Fail" unit tests. Apex utilizes **Phenomena Detectors** to report on the "health" of the simulation:
- **Resilience Index**: A composite score of the economy's ability to bounce back from shocks.
- **Liquidity Crisis Detector**: Identifies credit crunches at the bank-reserve level.
- **Policy Synergy Analysis**: Measures how fiscal and monetary stabilizers interfere or harmonize.

Reports are saved in `design/3_work_artifacts/reports/` for deep forensic analysis.

---

## 📂 Deep Dive: Documentation
For contributors and architects, the project's "Source of Truth" is contained within the `design/` directory:

- **[QUICKSTART Guide](design/QUICKSTART.md)**: Detailed onboarding for AI Agents (Gemini/Jules) and human architects.
- **[Platform Architecture](design/1_governance/platform_architecture.md)**: The "Sacred Sequence" (Orchestration) and Agent Value Systems (Maslow).
- **[Technical Debt Ledger](design/2_operations/ledgers/TECH_DEBT_LEDGER.md)**: Transparent tracking of architectural compromises and repayment plans.

---
*Developed by the Apex Collective. "Arm the tool, do not be the tool."*
