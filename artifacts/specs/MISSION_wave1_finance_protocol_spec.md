file: modules/finance/api.py
```python
from __future__ import annotations
from typing import Protocol, Dict, List, Any, Optional, TypedDict, Literal, Tuple, runtime_checkable, TYPE_CHECKING, Union, Callable
from dataclasses import dataclass, field
import abc
from abc import ABC, abstractmethod
from uuid import UUID
from modules.finance.dtos import MoneyDTO, MultiCurrencyWalletDTO, LoanApplicationDTO, LoanDTO, DepositDTO
from modules.system.api import MarketContextDTO, DEFAULT_CURRENCY, CurrencyCode
from modules.simulation.api import AgentID, AnyAgentID

if TYPE_CHECKING:
    from modules.simulation.api import IGovernment, EconomicIndicatorsDTO
    from simulation.dtos.api import GovernmentSensoryDTO
    from simulation.models import Order, Transaction
    from modules.common.dtos import Claim
    from modules.finance.wallet.api import IWallet
    from modules.hr.api import IHRService

# Forward reference for type hinting - REMOVED concrete class references per TD-PROTO-MONETARY
# class Firm: pass 
# class Household: pass 

@runtime_checkable
class IConfig(Protocol):
    """Protocol for configuration module."""
    def get(self, key: str, default: Any = None) -> Any: ...

@runtime_checkable
class IFinancialEntity(Protocol):
    """
    Standard interface for any entity capable of holding and transferring financial value.
    Replaces legacy `hasattr` checks and standardizes on integer pennies.
    """
    id: AgentID # Added ID for identification

    @property
    def balance_pennies(self) -> int:
        """Returns the balance in the default currency (pennies)."""
        ...

    def deposit(self, amount_pennies: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        """Deposits funds into the entity's wallet."""
        ...

    def withdraw(self, amount_pennies: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        """Withdraws funds from the entity's wallet."""
        ...

@runtime_checkable
class IPortfolioHolder(Protocol):
    """
    Protocol for entities that hold an investment portfolio.
    Used by MonetaryTransactionHandler to avoid concrete class coupling.
    """
    @property
    def portfolio(self) -> Any: # Should return IPortfolio
        ...

@runtime_checkable
class IIssuer(Protocol):
    """
    Protocol for entities that issue stock (Firms).
    Handles Treasury Share logic (Buybacks/Issuance).
    """
    id: AgentID
    
    @property
    def treasury_shares(self) -> float:
        ...
    
    @treasury_shares.setter
    def treasury_shares(self, value: float) -> None:
        ...

    @property
    def total_shares(self) -> float:
        """Represents Total Outstanding Shares (excluding Treasury)."""
        ...

    @total_shares.setter
    def total_shares(self, value: float) -> None:
        ...

@runtime_checkable
class IPropertyOwner(Protocol):
    """
    Protocol for entities that can own Real Estate.
    """
    id: AgentID
    
    @property
    def owned_properties(self) -> List[int]:
        ...

    def add_property(self, property_id: int) -> None:
        ...
    
    def remove_property(self, property_id: int) -> None:
        ...

@runtime_checkable
class IFinancialFirm(IFinancialEntity, Protocol):
    """
    Interface for a Firm entity used in financial analysis (e.g., Solvency).
    Ensures strict typing for solvency checks and financial reporting.
    """
    id: AgentID

    @property
    def age(self) -> int:
        ...

    @age.setter
    def age(self, value: int) -> None:
        ...

    @property
    def capital_stock_pennies(self) -> int:
        ...

    @property
    def inventory_value_pennies(self) -> int:
        ...

    @property
    def monthly_wage_bill_pennies(self) -> int:
        ...

    @property
    def total_debt_pennies(self) -> int:
        ...

    @property
    def retained_earnings_pennies(self) -> int:
        ...

    @property
    def average_profit_pennies(self) -> int:
        ...

@runtime_checkable
class IFinanceDepartment(Protocol):
    """
    Interface for a Firm's financial operations, designed for a multi-currency environment.
    MIGRATION: All monetary values are integers (pennies).
    """

    @property @abstractmethod
    def balance(self) -> Dict[CurrencyCode, int]:
        ...

    @abstractmethod
    def get_balance(self, currency: CurrencyCode) -> int:
        ...

    @abstractmethod
    def deposit(self, amount: int, currency: CurrencyCode):
        ...

    @abstractmethod
    def withdraw(self, amount: int, currency: CurrencyCode):
        ...

    @abstractmethod
    def get_financial_snapshot(self) -> Dict[str, Union[MoneyDTO, MultiCurrencyWalletDTO, float]]:
        ...

    @abstractmethod
    def calculate_valuation(self, market_context: MarketContextDTO) -> MoneyDTO:
        ...

    @abstractmethod
    def generate_financial_transactions(
        self,
        government: Any,
        all_households: List[Any],
        current_time: int,
        market_context: MarketContextDTO
    ) -> List[Any]: 
        ...

    @abstractmethod
    def set_dividend_rate(self, new_rate: float) -> None:
        ...

    @abstractmethod
    def pay_ad_hoc_tax(self, amount: int, currency: CurrencyCode, reason: str, government: Any, current_time: int) -> None:
        ...

@dataclass
class BondDTO:
    id: str
    issuer: str
    face_value: int
    yield_rate: float
    maturity_date: int

@dataclass(frozen=True)
class BailoutCovenant:
    dividends_allowed: bool = False
    executive_bonus_allowed: bool = False
    min_employment_level: Optional[int] = None

@dataclass
class BailoutLoanDTO:
    firm_id: AgentID
    amount: int
    interest_rate: float
    covenants: BailoutCovenant

@dataclass(frozen=True)
class GrantBailoutCommand:
    firm_id: AgentID
    amount: float
    interest_rate: float
    covenants: BailoutCovenant

@dataclass(frozen=True)
class SettlementOrder:
    sender_id: AgentID
    receiver_id: AgentID
    amount_pennies: int
    currency: CurrencyCode
    memo: str
    transaction_type: str 

@dataclass(frozen=True)
class PortfolioAsset:
    asset_type: str 
    asset_id: str 
    quantity: float

@dataclass(frozen=True)
class PortfolioDTO:
    assets: List[PortfolioAsset]

@dataclass(frozen=True)
class TaxCollectionResult:
    success: bool
    amount_collected: int
    tax_type: str
    payer_id: AgentID
    payee_id: AgentID
    error_message: Optional[str]

@dataclass(frozen=True)
class LoanInfoDTO:
    loan_id: str
    borrower_id: int 
    original_amount: float
    outstanding_balance: float
    interest_rate: float
    origination_tick: int
    due_tick: int
    lender_id: Optional[int] = None
    term_ticks: Optional[int] = None
    status: str = "ACTIVE"

@dataclass(frozen=True)
class DebtStatusDTO:
    borrower_id: int
    total_outstanding_debt: float
    loans: List[LoanInfoDTO]
    is_insolvent: bool
    next_payment_due: Optional[float]
    next_payment_due_tick: Optional[int]

class InsufficientFundsError(Exception):
    def __init__(self, message: str, required: Optional[MoneyDTO] = None, available: Optional[MoneyDTO] = None):
        self.required = required
        self.available = available
        if required and available:
             msg = f"{message} Required: {required['amount_pennies']} pennies {required['currency']}, Available: {available['amount_pennies']} pennies {available['currency']}"
        else:
             msg = message
        super().__init__(msg)

class LoanNotFoundError(Exception):
    pass

class LoanRepaymentError(Exception):
    pass

class LoanRollbackError(Exception):
    pass

@dataclass(frozen=True)
class BorrowerProfileDTO:
    borrower_id: AgentID 
    gross_income: float
    existing_debt_payments: float
    collateral_value: float
    credit_score: Optional[float] = None
    employment_status: str = "UNKNOWN"
    preferred_lender_id: Optional[int] = None

@dataclass(frozen=True)
class CreditAssessmentResultDTO:
    is_approved: bool
    max_loan_amount: int
    reason: Optional[str] 

@dataclass(frozen=True)
class LienDTO:
    loan_id: str
    lienholder_id: AgentID 
    principal_remaining: int
    lien_type: Literal["MORTGAGE", "TAX_LIEN", "JUDGEMENT_LIEN"]

@dataclass(frozen=True)
class MortgageApplicationDTO:
    applicant_id: int
    requested_principal: float
    purpose: str
    property_id: int
    property_value: float
    applicant_monthly_income: float
    existing_monthly_debt_payments: float
    loan_term: int

@runtime_checkable
class ICreditScoringService(Protocol):
    @abc.abstractmethod
    def assess_creditworthiness(self, profile: BorrowerProfileDTO, requested_loan_amount: int) -> CreditAssessmentResultDTO:
        ...

@dataclass(frozen=True)
class EquityStake:
    shareholder_id: AgentID
    ratio: float 

@dataclass(frozen=True)
class LiquidationContext:
    current_tick: int
    hr_service: Optional[IHRService] = None
    tax_service: Optional[Any] = None 
    shareholder_registry: Optional[IShareholderRegistry] = None

@runtime_checkable
class ILiquidatable(Protocol):
    id: AgentID

    def liquidate_assets(self, current_tick: int) -> Dict[CurrencyCode, int]:
        ...

    def get_all_claims(self, ctx: LiquidationContext) -> List[Claim]:
        ...

    def get_equity_stakes(self, ctx: LiquidationContext) -> List[EquityStake]:
        ...

@runtime_checkable
class IFinancialAgent(Protocol):
    id: AgentID

    def get_liquid_assets(self, currency: CurrencyCode = "USD") -> float:
        ...

    def get_total_debt(self) -> float:
        ...

    def _deposit(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        ...

    def _withdraw(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        ...

    def get_balance(self, currency: CurrencyCode = DEFAULT_CURRENCY) -> int:
        ...

    def get_all_balances(self) -> Dict[CurrencyCode, int]:
        ...

    @property
    def total_wealth(self) -> int:
        ...

@runtime_checkable
class IBankService(Protocol):
    def get_interest_rate(self) -> float: ...

    def grant_loan(self, borrower_id: int, amount: float, interest_rate: float, due_tick: int) -> Optional[Tuple[LoanInfoDTO, Any]]: ...

    def stage_loan(self, borrower_id: int, amount: float, interest_rate: float, due_tick: Optional[int], borrower_profile: Optional[BorrowerProfileDTO]) -> Optional[LoanInfoDTO]: ...

    def repay_loan(self, loan_id: str, amount: float) -> bool: ...

@runtime_checkable
class IBank(IBankService, IFinancialAgent, Protocol):
    base_rate: float

    @abc.abstractmethod
    def get_customer_balance(self, agent_id: AgentID) -> int:
        ...

    @abc.abstractmethod
    def get_debt_status(self, borrower_id: AgentID) -> DebtStatusDTO:
        ...

    @abc.abstractmethod
    def terminate_loan(self, loan_id: str) -> Optional["Transaction"]:
        ...

    @abc.abstractmethod
    def withdraw_for_customer(self, agent_id: AgentID, amount: int) -> bool:
        ...

    @abc.abstractmethod
    def get_total_deposits(self) -> int:
        ...

    @abc.abstractmethod
    def close_account(self, agent_id: AgentID) -> int:
        ...

    @abc.abstractmethod
    def repay_loan(self, loan_id: str, amount: int) -> int:
        ...

    @abc.abstractmethod
    def receive_repayment(self, borrower_id: AgentID, amount: int) -> int:
        ...

    # TD-INT-BANK-ROLLBACK: Strict Rollback Interface
    @abc.abstractmethod
    def rollback_transaction(self, transaction_id: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Strictly defined rollback method to replace hasattr/dynamic checks.
        """
        ...

@runtime_checkable
class IFiscalMonitor(Protocol):
    def get_debt_to_gdp_ratio(self, government: "IGovernment", indicators: "EconomicIndicatorsDTO") -> float: ...

@runtime_checkable
class IGovernmentFinance(IFinancialAgent, Protocol):
    total_debt: int
    sensory_data: Optional[GovernmentSensoryDTO]

@runtime_checkable
class ISettlementSystem(Protocol):
    def transfer(
        self,
        debit_agent: IFinancialAgent,
        credit_agent: IFinancialAgent,
        amount: int,
        memo: str,
        debit_context: Optional[Dict[str, Any]] = None,
        credit_context: Optional[Dict[str, Any]] = None,
        tick: int = 0,
        currency: CurrencyCode = DEFAULT_CURRENCY
    ) -> Optional[ITransaction]:
        ...

    def get_balance(self, agent_id: AgentID, currency: CurrencyCode = DEFAULT_CURRENCY) -> int:
        ...

    def get_account_holders(self, bank_id: int) -> List[int]:
        ...

    def get_agent_banks(self, agent_id: AgentID) -> List[int]:
        ...

    def register_account(self, bank_id: int, agent_id: int) -> None:
        ...

    def deregister_account(self, bank_id: int, agent_id: int) -> None:
        ...

    def remove_agent_from_all_accounts(self, agent_id: int) -> None:
        ...

@runtime_checkable
class IMonetaryAuthority(ISettlementSystem, Protocol):
    def create_and_transfer(
        self,
        source_authority: IFinancialAgent,
        destination: IFinancialAgent,
        amount: int,
        reason: str,
        tick: int,
        currency: CurrencyCode = DEFAULT_CURRENCY
    ) -> Optional[ITransaction]:
        ...

    def transfer_and_destroy(
        self,
        source: IFinancialAgent,
        sink_authority: IFinancialAgent,
        amount: int,
        reason: str,
        tick: int,
        currency: CurrencyCode = DEFAULT_CURRENCY
    ) -> Optional[ITransaction]:
        ...

    def mint_and_distribute(self, target_agent_id: int, amount: int, tick: int = 0, reason: str = "god_mode_injection") -> bool:
        ...

    def audit_total_m2(self, expected_total: Optional[int] = None) -> bool:
        ...

    def record_liquidation(
        self,
        agent: IFinancialAgent,
        inventory_value: int,
        capital_value: int,
        recovered_cash: int,
        reason: str,
        tick: int,
        government_agent: Optional[IFinancialAgent] = None
    ) -> None:
        ...

@runtime_checkable
class IFinanceSystem(Protocol):
    def evaluate_solvency(self, firm: IFinancialFirm, current_tick: int) -> bool:
        ...

    def issue_treasury_bonds(self, amount: int, current_tick: int) -> List[BondDTO]:
        ...

    def issue_treasury_bonds_synchronous(self, issuer: Any, amount_to_raise: int, current_tick: int) -> Tuple[bool, List["Transaction"]]:
        ...

    def register_bond(self, bond: BondDTO, owner_id: AgentID) -> None:
        ...

    def collect_corporate_tax(self, firm: IFinancialAgent, tax_amount: int) -> bool:
        ...

    def request_bailout_loan(self, firm: IFinancialFirm, amount: int) -> Optional[GrantBailoutCommand]:
        ...

    def service_debt(self, current_tick: int) -> List["Transaction"]:
        ...

    def process_loan_application(
        self,
        borrower_id: AgentID,
        amount: int,
        borrower_profile: BorrowerProfileDTO,
        current_tick: int
    ) -> Tuple[Optional[LoanInfoDTO], List["Transaction"]]:
        ...

    def get_customer_balance(self, bank_id: AgentID, customer_id: AgentID) -> int:
        ...

    def get_customer_debt_status(self, bank_id: AgentID, customer_id: AgentID) -> List[LoanInfoDTO]:
        ...

    def close_deposit_account(self, bank_id: AgentID, agent_id: AgentID) -> int:
        ...

    def record_loan_repayment(self, loan_id: str, amount: int) -> int:
        ...

    def repay_any_debt(self, borrower_id: AgentID, amount: int) -> int:
        ...

@dataclass(frozen=True)
class OMOInstructionDTO:
    operation_type: Literal['purchase', 'sale']
    target_amount: int

@runtime_checkable
class IMonetaryOperations(Protocol):
    def execute_open_market_operation(self, instruction: OMOInstructionDTO) -> List["Order"]:
        ...

@runtime_checkable
class ICentralBank(IMonetaryOperations, Protocol):
    id: AgentID

    def process_omo_settlement(self, transaction: "Transaction") -> None:
        ...

@dataclass(frozen=True)
class SagaStateDTO:
    saga_id: UUID
    state: str
    payload: Dict[str, Any]
    created_at: int
    updated_at: int

class IRealEstateRegistry(ABC):
    @abstractmethod
    def is_under_contract(self, property_id: int) -> bool:
        ...

    @abstractmethod
    def set_under_contract(self, property_id: int, saga_id: UUID) -> bool:
        ...

    @abstractmethod
    def release_contract(self, property_id: int, saga_id: UUID) -> bool:
        ...

    @abstractmethod
    def add_lien(self, property_id: int, loan_id: str, lienholder_id: AgentID, principal: int) -> Optional[str]:
        ...

    @abstractmethod
    def remove_lien(self, property_id: int, lien_id: str) -> bool:
        ...

    @abstractmethod
    def transfer_ownership(self, property_id: int, new_owner_id: AgentID) -> bool:
        ...

class ISagaRepository(ABC):
    @abstractmethod
    def find_active_saga_for_property(self, property_id: int) -> Optional[SagaStateDTO]:
        ...

@runtime_checkable
class IPortfolioHandler(Protocol):
    def get_portfolio(self) -> PortfolioDTO:
        ...

    def receive_portfolio(self, portfolio: PortfolioDTO) -> None:
        ...

    def clear_portfolio(self) -> None:
        ...

@runtime_checkable
class IHeirProvider(Protocol):
    def get_heir(self) -> Any: 
        ...

@runtime_checkable
class ICreditFrozen(Protocol):
    @property
    def credit_frozen_until_tick(self) -> int:
        ...

    @credit_frozen_until_tick.setter
    def credit_frozen_until_tick(self, value: int) -> None:
        ...

class ITaxService(ABC):
    @abstractmethod
    def calculate_liquidation_tax_claims(self, firm: IFinancialFirm) -> List[Claim]:
        ...

@dataclass(frozen=True)
class ShareholderData:
    agent_id: AgentID
    firm_id: AgentID
    quantity: float

@runtime_checkable
class IShareholderView(Protocol):
    id: AgentID
    is_active: bool
    def get_book_value_per_share(self) -> float: ...

@runtime_checkable
class IShareholderRegistry(Protocol):
    def register_shares(self, firm_id: AgentID, agent_id: AgentID, quantity: float) -> None:
        ...
    def get_shareholders_of_firm(self, firm_id: AgentID) -> List[ShareholderData]:
        ...
    def get_total_shares(self, firm_id: AgentID) -> float:
        ...

@runtime_checkable
class ILoanManager(Protocol):
    def submit_loan_application(self, application: LoanApplicationDTO) -> str: ...
    def process_applications(self) -> None: ...
    def service_loans(self, current_tick: int, payment_callback: Callable[[AgentID, int], bool]) -> List[Any]:
        ...
    def get_loan_by_id(self, loan_id: str) -> Optional[LoanDTO]: ...
    def get_loans_for_agent(self, agent_id: AgentID) -> List[LoanDTO]: ...
    def repay_loan(self, loan_id: str, amount: int) -> bool: ...

@runtime_checkable
class IDepositManager(Protocol):
    def create_deposit(self, owner_id: AgentID, amount: int, interest_rate: float, currency: CurrencyCode = DEFAULT_CURRENCY) -> str: ...
    def get_balance(self, agent_id: AgentID) -> int: ...
    def get_deposit_dto(self, agent_id: AgentID) -> Optional[DepositDTO]: ...
    def calculate_interest(self, current_tick: int) -> List[Tuple[AgentID, int]]:
        ...
    def withdraw(self, agent_id: AgentID, amount: int) -> bool: ...
    def get_total_deposits(self) -> int: ...

@dataclass(frozen=True)
class SolvencyCheckInputDTO:
    entity_id: str
    total_assets: float
    total_liabilities: float

@dataclass(frozen=True)
class SolvencyCheckOutputDTO:
    entity_id: str
    is_solvent: bool
    net_worth: float
    debt_to_asset_ratio: float 

@runtime_checkable
class SolvencyEngine(Protocol):
    def check(self, inputs: SolvencyCheckInputDTO) -> SolvencyCheckOutputDTO:
        ...

@runtime_checkable
class IIncomeTracker(Protocol):
    def add_labor_income(self, amount: int) -> None:
        ...

@runtime_checkable
class IConsumptionTracker(Protocol):
    def add_consumption_expenditure(self, amount: int, item_id: Optional[str] = None) -> None:
        ...

@runtime_checkable
class IEconomicMetricsService(Protocol):
    def record_withdrawal(self, amount_pennies: int) -> None:
        ...

class IPanicRecorder(Protocol):
    def record_withdrawal(self, amount_pennies: int) -> None: ...

@runtime_checkable
class ISalesTracker(Protocol):
    sales_volume_this_tick: float
    def record_sale(self, item_id: str, quantity: float, current_tick: int) -> None: ...

@runtime_checkable
class IRevenueTracker(Protocol):
    def record_revenue(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None: ...

@runtime_checkable
class IExpenseTracker(Protocol):
    """Protocol for tracking expenses. TD-SYS-ACCOUNTING-GAP"""
    def record_expense(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None: ...

@runtime_checkable
class IConsumer(Protocol):
    def consume(self, item_id: str, quantity: float, current_tick: int) -> None: ...
    def record_consumption(self, quantity: float, is_food: bool = False) -> None: ...

@runtime_checkable
class ISolvencyChecker(Protocol):
    def check_solvency(self, government: Any) -> None: ...

@runtime_checkable
class ILoanRepayer(Protocol):
    def repay_loan(self, loan_id: str, amount: int) -> int: ...
```

file: design/3_work_artifacts/specs/wave1_finance_protocol_spec.md
```markdown
# Mission Spec: Wave 1 - Financial Protocol Enforcement

## 1. Overview
- **Goal**: Harden the financial system by enforcing protocols, removing concrete class dependencies in `MonetaryTransactionHandler`, and ensuring reciprocal accounting.
- **Scope**: `MonetaryTransactionHandler`, `accounting.py`, `IBank` interface.
- **Key Resolutions**: 
  - `TD-PROTO-MONETARY` (Remove `isinstance(Firm/Household)`)
  - `TD-INT-BANK-ROLLBACK` (Strict `rollback_transaction` interface)
  - `TD-SYS-ACCOUNTING-GAP` (Buyer expense tracking)

## 2. Architecture & Design

### 2.1. Protocol-Driven Handler (`MonetaryTransactionHandler`)
The handler currently imports `Firm` and `Household` to distinguish behavior (specifically Treasury Shares). We will replace this with the following Protocols defined in `modules/finance/api.py`:

- **`IIssuer`**: Entities that issue stock (Firms).
  - `treasury_shares: float` (Getter/Setter)
  - `total_shares: float` (Outstanding Shares Getter/Setter)
- **`IPortfolioHolder` / `IInvestor`**: Entities that hold other assets.
  - `portfolio: Portfolio` (Access to holdings)
- **`IPropertyOwner`**: Entities that own Real Estate.
  - `add_property(id)`, `remove_property(id)`

#### Refactoring Logic Table
| Logic | Old Check | New Protocol Check |
| :--- | :--- | :--- |
| **Buy/Sell Treasury Shares** | `isinstance(agent, Firm) and agent.id == firm_id` | `isinstance(agent, IIssuer) and agent.id == firm_id` |
| **Buy/Sell Portfolio Asset** | `isinstance(agent, IInvestor)` | `isinstance(agent, IPortfolioHolder)` |
| **Real Estate Owner** | `isinstance(agent, IPropertyOwner)` | `isinstance(agent, IPropertyOwner)` |

### 2.2. Accounting Reciprocity (`TD-SYS-ACCOUNTING-GAP`)
Current `SettlementSystem` triggers `record_revenue` on the seller but often ignores the buyer side.
- **Change**: `SettlementSystem.transfer` (and derivatives) must check if `debit_agent` implements `IExpenseTracker`.
- **Logic**: 
  ```python
  if isinstance(debit_agent, IExpenseTracker):
      debit_agent.record_expense(amount, currency)
  ```

### 2.3. Strict Bank Rollback (`TD-INT-BANK-ROLLBACK`)
- **Change**: Add `rollback_transaction` to `IBank` protocol.
- **Enforcement**: Remove any code doing `if hasattr(bank, 'rollback_transaction'): ...` and rely on the Protocol.

## 3. Implementation Plan (Pseudo-code)

### 3.1. `modules/finance/api.py` Updates
(See Output Block for Full API Draft)
- Define `IIssuer`, `IPortfolioHolder`, `IPropertyOwner`, `IExpenseTracker`.
- Add `rollback_transaction` to `IBank`.

### 3.2. `simulation/systems/handlers/monetary_handler.py` Refactor

```python
from modules.finance.api import IIssuer, IPortfolioHolder, IPropertyOwner, IFinancialEntity

class MonetaryTransactionHandler(ITransactionHandler):
    def handle(self, tx: Transaction, buyer: IFinancialEntity, seller: IFinancialEntity, context: TransactionContext) -> bool:
        # ... logic ...
        self._apply_asset_liquidation_effects(tx, buyer, seller, context)
        return True

    def _handle_stock_side_effect(self, tx, buyer, seller, context):
        firm_id = extract_firm_id(tx.item_id)
        
        # 1. Handle Seller (Source of Stock)
        if isinstance(seller, IIssuer) and seller.id == firm_id:
            # Treasury Share Logic: Seller is the Issuer (Buyback -> Treasury)
            # Wait, if Seller is Issuer, it is SELLING its own stock (Issuance/Re-issuance)
            seller.treasury_shares = max(0, seller.treasury_shares - tx.quantity)
            # Outstanding shares increase? 
            # Logic: Treasury Shares are "Inventory". If sold, they enter circulation.
            seller.total_shares += tx.quantity 
        elif isinstance(seller, IPortfolioHolder):
            seller.portfolio.remove(firm_id, tx.quantity)
            
        # 2. Handle Buyer (Destination of Stock)
        if isinstance(buyer, IIssuer) and buyer.id == firm_id:
            # Buyback Logic: Issuer is BUYING its own stock
            buyer.treasury_shares += tx.quantity
            buyer.total_shares -= tx.quantity # Outstanding shares decrease
        elif isinstance(buyer, IPortfolioHolder):
            price = calculate_price(tx)
            buyer.portfolio.add(firm_id, tx.quantity, price)
```

## 4. Verification & Testing Strategy

### 4.1. Test Migration (CRITICAL)
- **Problem**: `MagicMock()` used in current tests will fail `isinstance(mock, IIssuer)` unless configured.
- **Action**: All tests in `tests/systems/test_monetary_handler.py` (and related) must be updated.
- **Pattern**:
  ```python
  # Old
  mock_firm = MagicMock()
  mock_firm.id = 1
  
  # New
  mock_firm = MagicMock(spec=IIssuer) # OR spec_set=True if actual class available
  mock_firm.id = 1
  mock_firm.treasury_shares = 100.0
  ```

### 4.2. New Test Cases
1. **`test_handle_treasury_buyback`**: Verify `IIssuer` logic when `buyer.id == firm_id`.
2. **`test_handle_treasury_issuance`**: Verify `IIssuer` logic when `seller.id == firm_id`.
3. **`test_accounting_reciprocity`**: Trigger a transfer and assert `buyer.record_expense` is called.
4. **`test_protocol_conformance`**: Use `assert_implements_protocol` on real `Firm` and `Bank` classes to ensure they match `api.py`.

### 4.3. Risk Assessment
- **Risk**: Circular dependency if `MonetaryHandler` imports `Firm` for type hints.
  - **Mitigation**: Strictly use `TYPE_CHECKING` blocks and `modules/finance/api.py`.
- **Risk**: "God Context" in tests.
  - **Mitigation**: Update `MockTransactionContext` to include `central_bank`, `settlement_system` stubs.

## 5. Mandatory Reporting
- **File**: `communications/insights/wave1-finance-protocol-spec.md`
- **Content**: Document the `IIssuer` logic decision and the removal of `Firm` imports.
```