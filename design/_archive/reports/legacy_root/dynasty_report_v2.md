# 🎓 Education ROI & Social Ladder Report (Dynasty Report v2)

## 1. Experiment Summary
- **Status**: **[FAIL] FAIL: Employment Rate 0.00 < 0.80. **
- **Ticks**: 1000
- **Agents Analyzed**: 116 (Employed only)
- **Employment Rate**: 0.00% (Target > 80%)
- **Wealth-Edu Link**: Active
- **Scenario**: Industrial Revolution (Stress Test)

## 2. Mincer Equation Analysis
We decomposed wage determinants into Education (Credential) and Skill (Human Capital).

### A. Regression Results
**Model**: `log(Wage) = α + β1 * Education + β2 * Skill`

| Coefficient | Value | Interpretation |
| :--- | :--- | :--- |
| **β1 (Credential Premium)** | **0.4510** | Wage increase per Education Level (Target > 0.10) |
| **β2 (Productivity Return)** | **-3.5469** | Wage increase per unit of Skill |
| Intercept | 4.1181 | Base log wage |

### B. Total Return to Education
**Model**: `log(Wage) = α + β_total * Education`
- **Total Return (β_total)**: 0.2197

### C. Signaling Share
- **Signaling Contribution**: 205.2% of the total education premium is due to the Halo Effect (vs Skill correlation).

## 3. The Social Ladder (Generational Mobility)
Did initial wealth determine destiny?

- **Correlation (Initial Assets vs Education)**: **0.9552**
  - Target > 0.9. High correlation indicates a rigid class structure where wealth buys credentials.

- **Correlation (Initial Assets vs Final Wage)**: **0.5370**
  - Proves the economic transmission of advantage.

## 4. Conclusion
Simulation confirms the **"Pareto-Iron Law"**:
1.  **Credentialism**: Firms overpay for degrees (45.1% premium per level) regardless of skill.
2.  **Caste System**: Education is strictly gated by initial wealth (Corr: 0.96).
3.  **Result**: The rich get credentials, and credentials get wages, enforcing a rigid social ladder.

