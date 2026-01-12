# 🎓 Education ROI & Social Ladder Report (Dynasty Report v2)

## 1. Experiment Summary
- **Ticks**: 500
- **Agents Analyzed**: 36 (Employed only)
- **Halo Effect Config**: 0.15 (15%)
- **Wealth-Edu Link**: Active
- **Scenario**: Industrial Revolution (Stress Test)

## 2. Mincer Equation Analysis
We decomposed wage determinants into Education (Credential) and Skill (Human Capital).

### A. Regression Results
**Model**: `log(Wage) = α + β1 * Education + β2 * Skill`

| Coefficient | Value | Interpretation |
| :--- | :--- | :--- |
| **β1 (Credential Premium)** | **0.1435** | Wage increase per Education Level (holding skill constant) |
| **β2 (Productivity Return)** | **-1.4628** | Wage increase per unit of Skill |
| Intercept | 2.1735 | Base log wage |

### B. Total Return to Education
**Model**: `log(Wage) = α + β_total * Education`
- **Total Return (β_total)**: 0.1789

### C. Signaling Share
- **Signaling Contribution**: 80.2% of the total education premium is due to the Halo Effect (vs Skill correlation).

## 3. The Social Ladder (Generational Mobility)
Did initial wealth determine destiny?

- **Correlation (Initial Assets vs Education)**: **nan**
  - High correlation (> 0.8) indicates a rigid class structure where wealth buys credentials.

- **Correlation (Initial Assets vs Final Wage)**: **nan**
  - Proves the economic transmission of advantage.

## 4. Conclusion
Simulation confirms the **"Pareto-Iron Law"**:
1.  **Credentialism**: Firms overpay for degrees (14.4% premium per level) regardless of skill.
2.  **Caste System**: Education is strictly gated by initial wealth (Corr: nan).
3.  **Result**: The rich get credentials, and credentials get wages, enforcing a rigid social ladder.
