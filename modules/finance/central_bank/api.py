# --- modules/finance/central_bank/api.py ---
from __future__ import annotations
from typing import Protocol, TypedDict, Literal, List, TYPE_CHECKING
from abc import abstractmethod

if TYPE_CHECKING:
    # This service is expected to be defined in a government module,
    # managing the issuance and market for government securities.
    # This is a forward reference to avoid circular imports.
    from modules.government.treasury.api import ITreasuryService, BondDTO

# ==============================================================================
# Data Transfer Objects (DTOs)
# ==============================================================================

class PolicyRateDTO(TypedDict):
    """
    Represents the central bank's policy interest rate.
    This is a pure data object for inter-system communication.
    """
    rate: float
    effective_tick: int
    decision_tick: int

class OpenMarketOperationResultDTO(TypedDict):
    """
    Summarizes the outcome of an open market operation, ensuring a clear
    record of the transaction for auditing and analysis.
    """
    success: bool
    operation_type: Literal["purchase", "sale"]
    bonds_transacted_count: int
    cash_transferred: float
    message: str

# ==============================================================================
# Exceptions
# ==============================================================================

class InvalidPolicyRateError(Exception):
    """Raised when an attempt is made to set an invalid policy rate (e.g., negative)."""
    pass

class TreasuryServiceError(Exception):
    """
    Raised when an interaction with the ITreasuryService fails, for example,
    if there are not enough bonds available for purchase.
    """
    pass

# ==============================================================================
# Interface
# ==============================================================================

class ICentralBank(Protocol):
    """
    Defines the contract for the Central Bank, responsible for monetary policy
    execution. Its primary levers are the policy rate and open market operations,
    which are used to influence the money supply and steer market rates.
    """

    @abstractmethod
    def set_policy_rate(self, rate: float) -> PolicyRateDTO:
        """
        Sets the main policy interest rate for the economy.

        This rate acts as a crucial benchmark for the entire financial system,
        heavily influencing inter-bank lending rates (e.g., in the call market)
        and subsequent commercial lending rates to firms and households.

        Args:
            rate: The new policy interest rate (e.g., 0.05 for 5%).

        Returns:
            A DTO confirming the new rate and the tick it becomes effective.

        Raises:
            InvalidPolicyRateError: If the provided rate is outside a valid range.
        """
        ...

    @abstractmethod
    def get_policy_rate(self) -> PolicyRateDTO:
        """
        Retrieves the current policy interest rate.

        Returns:
            A DTO containing the current rate information.
        """
        ...

    @abstractmethod
    def conduct_open_market_operation(
        self,
        treasury_service: "ITreasuryService",
        operation_type: Literal["purchase", "sale"],
        target_cash_amount: float
    ) -> OpenMarketOperationResultDTO:
        """
        Executes open market operations by buying or selling government bonds.

        - 'purchase': The central bank buys bonds from commercial banks,
                      injecting cash (reserves) into the banking system.
        - 'sale': The central bank sells bonds to commercial banks,
                  withdrawing cash (reserves) from the banking system.

        This is the primary mechanism for managing the level of reserves in the
        banking system to keep the inter-bank lending rate close to the policy rate.

        Args:
            treasury_service: The interface for accessing the government bond market.
            operation_type: The type of operation to execute ('purchase' or 'sale').
            target_cash_amount: The total cash value of bonds to be transacted.

        Returns:
            A DTO summarizing the result of the operation.

        Raises:
            TreasuryServiceError: If the treasury service cannot fulfill the request.
        """
        ...
