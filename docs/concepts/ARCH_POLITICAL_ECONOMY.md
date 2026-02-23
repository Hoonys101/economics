# Architecture: Political Economy (The Clash of Mandates)

## 1. Philosophical Foundation
In the Living Economic Laboratory, the macro-economy is not a coordinated machine but a **clash of conflicting mandates**. We explicitly model the tension between political survival (Fiscal) and mathematical stability (Monetary).

### The Populist Government (RL Brain)
- **Character**: Greedy, short-termist, and survival-oriented.
- **Mechanism**: Reinforced Learning (RL) via `GovernmentAI`.
- **Goal**: Maximize **Approval Rating** (Votes) to stay in power.
- **Behavior**: Will tend towards "Fiscal Ease" (Tax cuts, Stimulus) to buy votes, even at the cost of long-term debt or inflation.

### The Cold Machine Bank (Rule-based Anchor)
- **Character**: Deterministic, hawkish, and indifferent to public opinion.
- **Mechanism**: Strict Strategy Pattern (`IMonetaryRule`).
- **Goal**: Maintain **Price Stability** (Inflation Target) and M2 integrity.
- **Behavior**: Acts as a "Mathematical Anchor." If the Government overheats the economy, the Bank will move in the opposite direction (hiking rates) regardless of political pressure.

---

## 2. The Political Pipeline (Vote-to-Mandate)

To ground the Government's RL reward in agent reality, we move from "Bulk Scans" to **Individual Mandate Tracking**.

### Individual Voting (`VoteRecordDTO`)
- Agents (Households) do not just have an "Approval" number.
- They evaluate the current state vs. their **Personality** and **Economic Vision**.
- They cast a formal `VoteRecordDTO`, which becomes the primary input for the `PoliticalOrchestrator`.

### The Lobbying Layer (Interest Groups)
- **Aggregated Influence**: Instead of pure 1-agent-1-vote, we model **Interest Groups (PACs/Unions)**.
- **Lobbying Power**: Groups and Firms can submit `LobbyingEffortDTO` to shift the priority of certain policy tags.
- **Political Weight**: The `PoliticalOrchestrator` weights votes based on the socioeconomic status and lobbying funds of the participants.

---

## 3. Monetary Strategy Pattern

The Central Bank provides the "Physics" of the monetary world. It supports switching between historically significant rules:

| Rule | Focus | Behavior |
| :--- | :--- | :--- |
| **Taylor Rule** | Inflation + Output Gap | Counter-cyclical interest rate adjustment. |
| **Friedman Rule** | M2 Money Supply | Constant growth rate of money supply, ignoring cyclicality. |
| **McCallum Rule** | Nominal GDP | Adjusts base money to target a specific NGDP path. |

---

## 4. Emergent Tension
The "Drama" of the simulation arises from the **Multi-agent Chaos** created when the Government tries to satisfy volatile voters while the Central Bank strictly enforces mathematical constraints. 

> [!IMPORTANT]
> **Architectural Guardrail**: Never introduce RL to the Central Bank. Its role is to be the "Fixed Point" that the Government AI must learn to navigate within.
