# Spec: AdaptiveGovBrain (Political Decision Engine)

- **Version**: 1.0
- **Author**: Scribe (Administrative Assistant)
- **Related Ticket(s)**: TD-193

## 1. Overview

The `AdaptiveGovBrain` is a stateless, utility-driven decision engine responsible for proposing government policy actions. It operates on a **Propose-Filter-Execute** architecture, where it generates a list of potential policies, scores them based on a heuristic prediction of their outcome, and ranks them according to the ruling political party's ideology.

This engine is **not a predictive simulator**. It uses a simple, hard-coded heuristic "mental model" to estimate the impact of policies for decision-making purposes only. Its predictions do not reflect the complex dynamics of the main simulation.

## 2. Interfaces

### Input

1.  **`sensory_data: SensoryDTO`**: A snapshot of the current socio-economic state. This corresponds to `simulation.dtos.GovernmentStateDTO`.
    ```python
    @dataclass(frozen=True)
    class GovernmentStateDTO:
        # Simplified for spec
        approval_low_asset: float  # (0.0 to 1.0)
        approval_high_asset: float # (0.0 to 1.0)
        gini_index: float          # (0.0 to 1.0)
        gdp_growth_sma: float      # e.g., 0.02 for 2%
        ...
    ```
2.  **`ruling_party: PoliticalParty`**: An enum (`PoliticalParty.RED` or `PoliticalParty.BLUE`) indicating the current government's ideology.

### Output

-   **`List[PolicyActionDTO]`**: A list of potential policy actions, sorted in descending order of calculated utility.
    ```python
    @dataclass
    class PolicyActionDTO:
        name: str
        utility: float
        tag: PolicyActionTag
        action_type: str
        params: Dict[str, Any] = field(default_factory=dict)
    ```

## 3. Core Logic (Pseudo-code)

The main entry point is `propose_actions(sensory_data, ruling_party)`.

```plaintext
FUNCTION propose_actions(current_state, party):
  // 1. Generate all possible actions
  candidate_actions = _generate_candidates()
  scored_actions = []

  // 2. Score each candidate action
  FOR each action in candidate_actions:
    // 2a. Predict the outcome using a simple heuristic model
    predicted_state = _predict_outcome(current_state, action)

    // 2b. Calculate the utility of the predicted state based on party ideology
    predicted_utility = _calculate_utility(predicted_state, party)

    // 2c. Assign the score to the action
    action.utility = predicted_utility
    add action to scored_actions

  // 3. Sort actions by utility (highest first)
  SORT scored_actions descending by utility

  RETURN scored_actions
```

## 4. Action Space (`_generate_candidates`)

The engine evaluates a static set of possible actions.

| Name | `action_type` | `tag` | Parameters (`params`) |
| :--- | :--- | :--- | :--- |
| Fiscal Stimulus (Welfare+) | `ADJUST_WELFARE` | `KEYNESIAN_FISCAL` | `{"multiplier_delta": 0.1}` |
| Tax Cut (Corp) | `ADJUST_CORP_TAX` | `KEYNESIAN_FISCAL` | `{"rate_delta": -0.02}` |
| Tax Cut (Income) | `ADJUST_INCOME_TAX` | `KEYNESIAN_FISCAL` | `{"rate_delta": -0.02}` |
| Austerity (Welfare-) | `ADJUST_WELFARE` | `AUSTRIAN_AUSTERITY`| `{"multiplier_delta": -0.1}`|
| Tax Hike (Corp) | `ADJUST_CORP_TAX` | `AUSTRIAN_AUSTERITY`| `{"rate_delta": 0.02}` |
| Tax Hike (Income) | `ADJUST_INCOME_TAX`| `AUSTRIAN_AUSTERITY`| `{"rate_delta": 0.02}` |
| Maintain Course | `DO_NOTHING` | `GENERAL_ADMIN` | `{}` |

## 5. Heuristic Mental Model (`_predict_outcome`)

This model applies simple, hard-coded arithmetic adjustments to the current state to create a predicted future state.

| `action_type` | `params` | Predicted Effect on `SensoryDTO` |
| :--- | :--- | :--- |
| `ADJUST_WELFARE`| `delta > 0` (+0.1) | `approval_low_asset` += 0.05<br>`gini_index` -= 0.01<br>`gdp_growth_sma` -= 0.001 |
| | `delta < 0` (-0.1) | `approval_low_asset` -= 0.05<br>`gini_index` += 0.01<br>`gdp_growth_sma` += 0.001 |
| `ADJUST_CORP_TAX`| `delta < 0` (-0.02) | `approval_high_asset` += 0.04<br>`gdp_growth_sma` += 0.005<br>`gini_index` += 0.005 |
| | `delta > 0` (+0.02) | `approval_high_asset` -= 0.04<br>`gdp_growth_sma` -= 0.005<br>`gini_index` -= 0.005 |
| `ADJUST_INCOME_TAX`|`delta < 0` (-0.02) | `approval_low_asset` += 0.03<br>`approval_high_asset` += 0.02<br>`gdp_growth_sma` += 0.002 |
| | `delta > 0` (+0.02) | `approval_low_asset` -= 0.03<br>`approval_high_asset` -= 0.02<br>`gdp_growth_sma` -= 0.002 |
| `DO_NOTHING` | `{}` | No change to the input state. |

**Note:** All additions and subtractions are bounded between `0.0` and `1.0` for approval ratings and Gini index.

## 6. Party Utility Functions (`_calculate_utility`)

Each political party has a distinct utility function to score a given economic state.

-   **`PoliticalParty.RED` (Focus: Equality & Working Class)**
    ```
    U = (0.7 * state.approval_low_asset) + (0.3 * (1.0 - state.gini_index))
    ```

-   **`PoliticalParty.BLUE` (Focus: Growth & Asset Holders)**
    ```
    U = (0.6 * state.approval_high_asset) + (0.4 * state.gdp_growth_sma)
    ```
