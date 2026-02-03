# Spec: H1-Housing-V2 (The Great Housewarming)

- **Mission**: `Phase 32: The Great Housewarming`. Modernize the housing credit pipeline by resolving documented technical debt (TD-065), implementing macro-prudential regulations, and ensuring all transactions are atomic and auditable to prevent M2 leaks.
- **Architectural Mandate**: This specification details the extraction of "Orphaned Logic" from the `DecisionUnit` into a stateless `HousingPlanner`, integrating with the `SettlementSystem` for transactional integrity.

---

## 1. API Definition (`modules/market/housing_planner_api.py`)

### DTOs

```python
from typing import TypedDict, List, Optional, Literal
from modules.household.dtos import HouseholdStateDTO
from modules.housing.dtos import HousingMarketSnapshotDTO
from modules.finance.dtos import LoanMarketSnapshotDTO # Added for credit assessment

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

class HousingOfferRequestDTO(TypedDict):
    """
    Input for the HousingPlanner, containing all necessary state for a decision.
    """
    household_state: HouseholdStateDTO
    housing_market_snapshot: HousingMarketSnapshotDTO
    loan_market_snapshot: LoanMarketSnapshotDTO # To assess credit availability

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
```

### Interfaces

```python
from abc import ABC, abstractmethod
from .dtos import HousingOfferRequestDTO, HousingDecisionDTO, HousingBubbleMetricsDTO

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

## 2. Logic Specification (Pseudo-code)

### 2.1. `HousingPlanner.evaluate_housing_options`

The core logic remains consistent with `spec_td065`, but is now guaranteed to be stateless.

```pseudocode
FUNCTION evaluate_housing_options(request: HousingOfferRequestDTO):
    // 1. Unpack DTOs
    household = request.household_state
    housing_market = request.housing_market_snapshot
    loan_market = request.loan_market_snapshot

    // 2. Assess affordability based on potential credit
    // Pre-flight check against market-wide credit conditions
    max_loan_estimate = estimate_max_loan(household, loan_market.interest_rate)

    // 3. Evaluate "Buy" Option
    affordable_properties = []
    FOR property IN housing_market.properties_for_sale:
        IF property.price <= household.assets.cash + max_loan_estimate:
            property.score = calculate_buy_score(property, household)
            affordable_properties.append(property)

    // ... (Rent evaluation logic remains the same)

    // 4. Decide and prepare Mortgage Application
    best_buy_option = get_best(affordable_properties)
    IF best_buy_option:
        offer_price = determine_offer_price(best_buy_option)
        down_payment = min(household.assets.cash, offer_price * config.MIN_DOWN_PAYMENT_PCT)
        loan_amount = offer_price - down_payment

        // **CRITICAL**: Create the DTO for the loan market
        mortgage_app = CREATE MortgageApplicationDTO(
            applicant_id=household.id,
            principal=loan_amount,
            purpose="MORTGAGE",
            property_id=best_buy_option.id,
            property_value=best_buy_option.price, # Use market price for LTV
            applicant_income=household.income,
            applicant_existing_debt=household.liabilities.total_debt
        )

        RETURN HousingDecisionDTO(
            decision_type="MAKE_OFFER",
            target_property_id=best_buy_option.id,
            offer_price=offer_price,
            mortgage_application=mortgage_app
        )

    // ... (Fallback to Rent or Stay)
```

### 2.2. `LoanMarket.evaluate_mortgage_application` (Macro-Prudential Regulation)

This new logic will be implemented inside the `LoanMarket` to enforce system-wide rules.

```pseudocode
FUNCTION evaluate_mortgage_application(application: MortgageApplicationDTO):
    // 1. Calculate Loan-to-Value (LTV)
    ltv = application.principal / application.property_value
    IF ltv > config.MAX_LTV_RATIO:
        log_rejection(application.applicant_id, "LTV EXCEEDED")
        RETURN False

    // 2. Calculate Debt-to-Income (DTI)
    // Includes principal and interest on the *new* loan
    estimated_monthly_payment = calculate_payment(application.principal, config.CENTRAL_BANK_RATE)
    total_monthly_debt = estimated_monthly_payment + (application.applicant_existing_debt / 12)
    dti = total_monthly_debt / (application.applicant_income / 12)
    IF dti > config.MAX_DTI_RATIO:
        log_rejection(application.applicant_id, "DTI EXCEEDED")
        RETURN False

    // 3. If all checks pass, approve the loan
    log_approval(application.applicant_id)
    RETURN True
```

---

## 3. Integration Plan: Atomic "Seamless Payment" (TD-179)

The transaction must be atomic and complete before the `TickOrchestrator`'s M2 audit. This is achieved via the `SettlementSystem`.

1.  **`DecisionUnit` Orchestration**:
    - Constructs `HousingOfferRequestDTO`.
    - Invokes `housing_planner.evaluate_housing_options()`.
    - If `decision.decision_type == "MAKE_OFFER"`:
        - It generates **TWO** orders:
            1.  An `Order` for the `LoanMarket` containing the `MortgageApplicationDTO`.
            2.  A *conditional* `Order` for the `HousingMarket` to purchase the property. This order is contingent on loan approval.

2.  **Market Execution Phase**:
    - `LoanMarket` processes its order queue. It evaluates the application using `evaluate_mortgage_application` and, if approved, stages a credit creation event.
    - `HousingMarket` processes its order queue. It only matches a buy order if the associated loan was approved in the same tick.

3.  **Settlement Phase (Atomic Transfer)**:
    - Upon a successful match, the `HousingMarket` **does not** perform direct asset transfers.
    - Instead, it registers a multi-party transaction with the `SettlementSystem`.
    - The `SettlementSystem` will atomically execute the following in a single transaction:
        - **Debit**: Buyer's assets (down payment).
        - **Credit**: Seller's assets (full offer price).
        - **Credit**: Buyer's assets (loan principal from bank).
        - **Debit**: Bank's reserves (loan principal).
        - **State Change**: Transfer `property_id` from seller's ownership to buyer's.
        - **State Change**: Create `Mortgage` liability for the buyer.

4.  **`BubbleObservatory` Integration**:
    - A new system, `BubbleObservatory`, will be created in `modules/analysis/`.
    - It will be called by a new post-phase hook in the `TickOrchestrator`, after the M2 audit, to ensure it has the latest data.
    - It will collect data, construct the `HousingBubbleMetricsDTO`, and log it to a dedicated file (`logs/housing_bubble_monitor.csv`).

---

## 4. Verification Plan

### 4.1. `verify_mortgage_pipeline_integrity.py`
-   **Goal**: Prove the end-to-end transaction is atomic and adheres to regulations.
-   **Methodology**:
    1.  Setup a scenario with one credit-worthy household, one un-worthy household, and one property for sale.
    2.  Set `MAX_LTV_RATIO` and `MAX_DTI_RATIO` to strict values in `config`.
    3.  Run the simulation.
-   **Success Criteria (Assertions)**:
    1.  **ASSERT**: The credit-worthy household successfully purchases the house, owns the property, and has a `Mortgage` liability.
    2.  **ASSERT**: The un-worthy household's loan application is rejected, and no transaction occurs.
    3.  **ASSERT**: The final M2 delta in the government audit log is exactly zero (post-settlement). The loan itself is a balance sheet expansion, not an M2 increase.
    4.  **ASSERT**: Query the `SettlementSystem` log to confirm a multi-party transaction was used for the purchase.

### 4.2. `verify_bubble_observatory.py`
-   **Goal**: Ensure the monitoring system collects and logs data correctly.
-   **Methodology**: Run a 100-tick simulation where interest rates are artificially lowered to induce a housing boom.
-   **Success Criteria (Assertions)**:
    1.  **ASSERT**: The `logs/housing_bubble_monitor.csv` file is created and populated.
    2.  **ASSERT**: The `house_price_index` and `new_mortgage_volume` columns show a clear upward trend in the log file.

---

## 5. Risk & Impact Audit

-   **Risk: Transaction Saga Failure**: The primary risk is a failure in the multi-stage process (Offer -> Loan -> Settlement). A bug in any step could leave the system in an inconsistent state. The `SettlementSystem` is designed to mitigate this, but its invocation must be correct.
-   **Test Impact**: **HIGH**. As predicted in `spec_td065`, this refactor will break most existing tests for `Household` and `DecisionUnit`. A dedicated effort will be required to:
    1.  Rewrite `DecisionUnit` tests to mock the `IHousingPlanner` interface output (`HousingDecisionDTO`).
    2.  Create new integration tests for the full pipeline described in the verification plan.
-   **Dependencies**: This work is critically dependent on a functional `SettlementSystem` and `LoanMarket`.
-   **Configuration**: New parameters **must** be added to `config/economy_params.yaml` and loaded into the `SimulationConfig`:
    -   `MAX_LTV_RATIO` (e.g., `0.9`)
    -   `MAX_DTI_RATIO` (e.g., `0.45`)
    -   `MIN_DOWN_PAYMENT_PCT` (e.g., `0.1`)
-   **Circular Dependency**: The proposed one-way dependency (`DecisionUnit` -> `HousingPlanner`) avoids circular imports. The planner must remain stateless and have no knowledge of the `DecisionUnit`.
