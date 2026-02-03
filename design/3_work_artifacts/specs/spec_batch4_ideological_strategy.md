# Specification - Batch 4: Ideological Strategy Pattern (Government)

This specification defines the refactoring of the Government decision-making engine into a dual-layered Strategy Pattern, combining Political Ideology and Economic Schools.

## 🏛️ 1. Concept: The Governing Matrix (2x2 Model)
The Government agent will explicitly separate **"Objectives" (Political Ideology)** from **"Mechanisms" (Economic School)**.

### The 2x2 Strategy Matrix
| Axis | Factor | Focus | Targets / Levers |
|---|---|---|---|
| **Y (Identity)** | **Ideology** | **Target Setting** | RED (Equity/Gini/Employment) vs BLUE (Growth/Profit/GDP) |
| **X (Technical)** | **School** | **Lever Selection** | Keynesian (Stimulus/Deficit) vs Austrian (Austerity/Neutrality) |

> **Political Paradox**: This allows for "RED+Austrian" (Inflation-targeting welfare cuts) or "BLUE+Keynesian" (Deficit-funded corporate subsidies).

## 🛠️ 2. Core Components & Logic

### [NEW] `IGovStrategy` (Unified Interface)
```python
class IGovStrategy(Protocol):
    def get_objectives(self) -> List[GovObjective]: ... # e.g., Target Gini < 0.35
    def decide_action(self, signals: SensoryDTO) -> List[PolicyIntent]: ...
```

### [NEW] The Fiscal Hydraulic System
Synthesis of `TaxationSystem` and `WelfareManager` into a single "Reservoir" model.
- **The Reservoir**: Real-time tax revenue inflows vs welfare outflows.
- **The Automatic Stabilizer**: `Welfare_Budget = f(Current_Tax_Revenue, Ideology_Factor)`.
- **Debt Trigger**: If `Mandated_Welfare > Reservoir`, automatically trigger **Bond Market** issuance (Deficit Spending).

### [NEW] The Social Damper (Physics-based)
Social Metrics act as friction in the economic engine.
- **Approval Lag**: High disapproval leads to `Policy Latency` (ticks delay for intent execution).
- **Cohesion Friction**: `Factory_Output = Base_Output * (0.5 + 0.5 * Cohesion_Score)`.
- **Strike Probability**: Triggered when Cohesion drops below 30%.

## 📉 3. Decision Logic Flow (Example Interaction)

1. **Party Influence**: A **RED Party** (Pro-Household) is in power. It wants low income tax.
2. **Advisor Influence**: The **Keynesian Advisor** detects a 2% GDP drop and recommends a **刺激(Stimulus)** stance of `+0.3`.
3. **Synthesis**:
   - The `Government` agent takes the `Keynesian` stimulus stance (+0.3).
   - It appends the `RED` ideology bias (prioritize welfare over corporate grants).
   - **Result**: Significant increase in transfer payments (Welfare) and moderate income tax cut, while keeping corporate tax relatively stable.

If the same **RED Party** had an **Austrian Advisor**, the 2% GDP drop would result in **No Change** (Neutral stance), even though the party *wants* to help households.

## ✅ 4. Verification Plan
- **Ideological Consistency**: Verify BLUE party reduces corporate tax while RED party increases basic welfare.
- **Economic Response**: Verify Keynesian strategist triggers stimulus during GDP drops, while Austrian strategist maintains budget neutrality.
- **Unit Tests**: Test each `Strategist` class in isolation with synthetic market data.
