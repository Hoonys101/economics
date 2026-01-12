# Tech Debt Ledger - Project Jules (Sociologist Track)

## 1. Hardcoded Halo Effect
- **Location**: `simulation/firms.py` (`Firm.update_needs`)
- **Description**: The "Halo Effect" (Credential Premium) is implemented as a hardcoded multiplier (`1 + education * HALO_EFFECT`) applied to the wage *after* skill calculation.
- **Why it's Debt**: In a realistic simulation, this premium should emerge from imperfect information (firms using degree as a proxy for skill) rather than a magic bonus. The current implementation breaks the marginal product of labor theory by explicitly overpaying.
- **Remediation**: Implement an "Interview" system where firms estimate skill with error, and education reduces that error, leading to risk-averse hiring of educated agents.

## 2. Deterministic Class Caste
- **Location**: `simulation/core_agents.py` (`Household.__init__`)
- **Description**: Education Level is strictly determined by `initial_assets` using `EDUCATION_WEALTH_THRESHOLDS`.
- **Why it's Debt**: This removes agency. Agents cannot "save up" for education later in life. It forces a caste system at birth for the sake of the experiment.
- **Remediation**: Implement a dynamic Education Market where agents can purchase degrees (Human Capital investment) at any age.

## 3. Industrial Revolution Stress Test Config
- **Location**: `scripts/experiments/education_roi_analysis.py`
- **Description**: The experiment uses "Utopia/Dystopia" parameters (Massive Firm Capital, desperate Households) to force labor market liquidity.
- **Why it's Debt**: The resulting economy is not in equilibrium and relies on infinite firm buffers.
- **Remediation**: Tune the core `config.py` parameters to achieve organic full employment without massive injections.
