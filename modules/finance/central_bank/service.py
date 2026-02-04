from __future__ import annotations
from typing import Callable, Literal
from modules.finance.central_bank.api import (
    ICentralBank,
    PolicyRateDTO,
    OpenMarketOperationResultDTO,
    InvalidPolicyRateError,
    TreasuryServiceError
)
from modules.government.treasury.api import ITreasuryService
from modules.system.constants import ID_CENTRAL_BANK
from modules.system.api import CurrencyCode, DEFAULT_CURRENCY

class CentralBankService:
    """
    Implementation of ICentralBank.
    Manages monetary policy (policy rate) and open market operations.
    """

    def __init__(self, agent_id: int = ID_CENTRAL_BANK, tick_provider: Callable[[], int] = lambda: 0):
        self.agent_id = agent_id
        self.tick_provider = tick_provider
        self._policy_rate: float = 0.05  # Default initial rate
        self._last_decision_tick: int = 0

    def set_policy_rate(self, rate: float) -> PolicyRateDTO:
        """
        Sets the main policy interest rate for the economy.
        """
        if rate < 0:
            raise InvalidPolicyRateError(f"Policy rate cannot be negative: {rate}")

        self._policy_rate = rate
        current_tick = self.tick_provider()
        self._last_decision_tick = current_tick

        return {
            "rate": self._policy_rate,
            "effective_tick": current_tick + 1,  # Assumes effective next tick
            "decision_tick": current_tick
        }

    def get_policy_rate(self) -> PolicyRateDTO:
        """
        Retrieves the current policy interest rate.
        """
        return {
            "rate": self._policy_rate,
            "effective_tick": self._last_decision_tick + 1,
            "decision_tick": self._last_decision_tick
        }

    def conduct_open_market_operation(
        self,
        treasury_service: ITreasuryService,
        operation_type: Literal["purchase", "sale"],
        target_cash_amount: float,
        currency: CurrencyCode = DEFAULT_CURRENCY
    ) -> OpenMarketOperationResultDTO:
        """
        Executes open market operations by buying or selling government bonds.
        Delegates to the TreasuryService to execute the actual market transaction.
        """

        result = None
        if operation_type == "purchase":
            # Central Bank BUYS bonds (injects cash)
            result = treasury_service.execute_market_purchase(
                buyer_id=self.agent_id,
                target_cash_amount=target_cash_amount,
                currency=currency
            )
        elif operation_type == "sale":
            # Central Bank SELLS bonds (withdraws cash)
            result = treasury_service.execute_market_sale(
                seller_id=self.agent_id,
                target_cash_amount=target_cash_amount,
                currency=currency
            )
        else:
             # Should be unreachable if type checked, but good to have
             raise ValueError(f"Invalid operation type: {operation_type}")

        if not result["success"]:
            raise TreasuryServiceError(f"Treasury operation failed: {result['message']}")

        return {
            "success": True,
            "operation_type": operation_type,
            "bonds_transacted_count": result["bonds_exchanged"],
            "cash_transferred": result["cash_exchanged"],
            "message": result["message"]
        }
