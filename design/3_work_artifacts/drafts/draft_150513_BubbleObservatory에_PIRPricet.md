# Spec: Add PIR Monitoring to BubbleObservatory

## 1. Overview

This specification outlines the addition of a Price-to-Income Ratio (PIR) metric to the `BubbleObservatory`. The goal is to enhance market stability monitoring by tracking housing affordability.

- **PIR Calculation**: The ratio of average house price to average annual household income will be calculated each tick.
- **DTO Update**: The `HousingBubbleMetricsDTO` will be updated with a new `pir` field.
- **Alarming**: A `WARNING` level log will be triggered if the PIR exceeds a threshold of `20.0`.
- **Logging**: The calculated PIR will be persisted to `logs/housing_bubble_monitor.csv`.

---

## 2. 🚨 Risk & Impact Audit (Pre-flight Check)

This change incorporates findings from the automated pre-flight audit.

- **❌ Critical Risk (Breaking Change)**: The addition of the `pir` field to `HousingBubbleMetricsDTO` is a **breaking API change**. All modules and tests that instantiate or validate this DTO **must** be updated. Failure to do so will result in test failures and potential runtime errors.

- **⚠️ High Risk (God Class Dependency)**: To calculate an economy-wide PIR, the implementation must access the global agent list via `self.simulation.agents`. This reinforces a dependency on the `Simulation` God Class. This is deemed a necessary dependency to achieve an accurate metric, as opposed to relying on incomplete data from recent transactions.

- **⚠️ Medium Risk (SRP Violation)**: The `BubbleObservatory` is currently responsible for both metric collection and CSV logging. Adding PIR calculation and alarming logic further consolidates responsibilities within this single class. To maintain consistency with the existing module structure, this new logic will be added here, but it contributes to existing technical debt regarding the Single Responsibility Principle.

---

## 3. Interface Specification (DTO Update)

The `HousingBubbleMetricsDTO` in `modules/market/housing_planner_api.py` will be modified to include the new `pir` field.

**File**: `modules/market/housing_planner_api.py`
```python
from typing import TypedDict, List, Optional, Literal
from abc import ABC, abstractmethod

# Import external DTOs
# Note: Adjust imports based on actual file structure
from modules.household.dtos import HouseholdStateDTO
from modules.system.api import HousingMarketSnapshotDTO

class LoanMarketSnapshotDTO(TypedDict):
    """
    Snapshot of the loan market conditions.
    """
    interest_rate: float
    max_ltv: float
    max_dti: float

# Renamed from LoanApplicationDTO for clarity as per Phase 32 spec
class MortgageApplicationDTO(TypedDict):
    """
    Represents a formal mortgage application sent to the LoanMarket.
    This is the primary instrument for the new credit pipeline.
    """
    applicant_id: int
    principal: float
    purpose: Literal["MORTGAGE"]
    property_id: int
    property_value: float # Market value for LTV calculation
    applicant_income: float # For DTI calculation
    applicant_existing_debt: float # For DTI calculation
    loan_term: int # Added to support calculation (implied in logic)

class HousingOfferRequestDTO(TypedDict):
    """
    Input for the HousingPlanner, containing all necessary state for a decision.
    """
    household_state: HouseholdStateDTO
    housing_market_snapshot: HousingMarketSnapshotDTO
    loan_market_snapshot: LoanMarketSnapshotDTO # To assess credit availability
    applicant_current_debt: float # Total outstanding debt
    applicant_annual_income: float # Estimated annual income

class HousingDecisionDTO(TypedDict):
    """
    Output of the HousingPlanner, detailing the agent's next action.
    This DTO is a command, not a state update.
    """
    decision_type: Literal["MAKE_OFFER", "RENT", "STAY"]
    target_property_id: Optional[int]
    offer_price: Optional[float]
    mortgage_application: Optional[MortgageApplicationDTO]

class HousingBubbleMetricsDTO(TypedDict):
    """
    Data structure for monitoring housing market stability.
    """
    tick: int
    house_price_index: float
    m2_growth_rate: float
    new_mortgage_volume: float
    average_ltv: float
    average_dti: float
    pir: float # Price-to-Income Ratio

# --- Interfaces ---

class IHousingPlanner(ABC):
    """
    Stateless interface for making housing decisions. Extracts orphaned logic
    from the old DecisionUnit.
    """
    @abstractmethod
    def evaluate_housing_options(self, request: HousingOfferRequestDTO) -> HousingDecisionDTO:
        """
        Analyzes the market and agent's finances to recommend a housing action.
        This method MUST NOT mutate state.
        """
        ...

class ILoanMarket(ABC):
    """
    Expanded interface for the LoanMarket to include regulatory checks.
    """
    @abstractmethod
    def evaluate_mortgage_application(self, application: MortgageApplicationDTO) -> bool:
        """
        Performs hard LTV/DTI checks. Returns True if approved, False if rejected.
        """
        ...

    @abstractmethod
    def stage_mortgage(self, application: MortgageApplicationDTO) -> Optional[dict]:
         """
         Stages a mortgage (creates loan record) without disbursing funds.
         Returns LoanInfoDTO (as dict) if successful, None otherwise.
         """
         ...

class IBubbleObservatory(ABC):
    """
    Interface for the new market monitoring system.
    """
    @abstractmethod
    def collect_metrics(self) -> HousingBubbleMetricsDTO:
        """
        Collects and returns key indicators of a housing bubble.
        """
        ...
```

---

## 4. Logic Steps (Pseudo-code)

The following logic will be added to the `collect_metrics` method in `modules/analysis/bubble_observatory.py`.

```python
# In BubbleObservatory.collect_metrics()

# ... (after avg_price calculation)

# 4. Price-to-Income Ratio (PIR)
TICKS_PER_YEAR = getattr(self.simulation.config_module, 'TICKS_PER_YEAR', 100)
all_agents = self.simulation.agents.values()
household_incomes = [
    agent.current_wage * TICKS_PER_YEAR
    for agent in all_agents
    if hasattr(agent, 'current_wage') and agent.current_wage > 0
]

avg_annual_income = statistics.mean(household_incomes) if household_incomes else 0.0
pir = (avg_price / avg_annual_income) if avg_annual_income > 0 else 0.0

# PIR Alarm
if pir > 20.0:
    logger.warning(f"High PIR detected: {pir:.2f}. Avg House Price: {avg_price:.2f}, Avg Annual Income: {avg_annual_income:.2f}")

# ... (before creating HousingBubbleMetricsDTO)

metrics: HousingBubbleMetricsDTO = {
    "tick": tick,
    "house_price_index": avg_price,
    "m2_growth_rate": growth_rate,
    "new_mortgage_volume": new_mortgage_vol,
    "average_ltv": avg_ltv,
    "average_dti": avg_dti,
    "pir": pir # Add new metric
}

# ... (in CSV logging section)

# Update file header if it doesn't exist
# with "...,average_dti,pir\n"
# Update file write operation with
# f"...{avg_dti:.4f},{pir:.2f}\n"

```

---

## 5. Verification Plan

1.  **Update Dependent Tests**:
    - Identify all unit and integration tests that create or mock `HousingBubbleMetricsDTO`.
    - Update these tests to include the new `pir: float` field in the DTO object construction.

2.  **New Unit Tests for `BubbleObservatory`**:
    - **Test Case 1 (PIR Alarm)**: Create a scenario with high average house prices and low average household incomes, such that the calculated PIR is greater than 20.0. Assert that `logger.warning` is called with the expected message.
    - **Test Case 2 (Zero Income)**: Create a scenario with no households or households with zero income. Verify that `avg_annual_income` is 0 and `pir` is 0, and that no `ZeroDivisionError` is raised.
    - **Test Case 3 (Normal Conditions)**: Test with a standard set of agents and verify that the calculated PIR is a plausible floating-point number.

3.  **Integration Test (CSV Logging)**:
    - Run a short simulation.
    - Read the `logs/housing_bubble_monitor.csv` file.
    - Verify the header row contains the `pir` column.
    - Verify the data rows contain a numeric value for the `pir` column.
