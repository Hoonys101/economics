from typing import Any, Optional
import logging
from simulation.systems.api import IMintingAuthority
from simulation.systems.settlement_system import SettlementSystem

logger = logging.getLogger(__name__)

class CentralBankSystem(IMintingAuthority):
    """
    System wrapper for the Central Bank Agent to act as the Minting Authority.
    Handles Non-Zero-Sum transactions (money creation/destruction).
    """

    def __init__(self, central_bank_agent: Any, settlement_system: SettlementSystem, logger: Optional[logging.Logger] = None):
        self.central_bank = central_bank_agent
        self.settlement = settlement_system
        self.logger = logger if logger else logging.getLogger(__name__)

    def mint_and_transfer(self, target_agent: Any, amount: float, memo: str) -> bool:
        """
        Creates money (by withdrawing from Central Bank which can go negative)
        and transfers it to the target agent.
        """
        # Central Bank is the only entity allowed to have negative cash (Fiat Issuer)
        # We use standard settlement transfer from Central Bank to Target.
        success = self.settlement.transfer(
            debit_agent=self.central_bank,
            credit_agent=target_agent,
            amount=amount,
            memo=f"MINT:{memo}"
        )

        if success:
            if hasattr(target_agent, "total_money_issued"): # Only for relevant agents if needed
                 target_agent.total_money_issued += amount

            self.logger.info(
                f"MINT_SUCCESS | Minted {amount:.2f} to {target_agent.id}. Memo: {memo}",
                extra={"agent_id": target_agent.id, "amount": amount, "memo": memo}
            )
        else:
            self.logger.error(
                f"MINT_FAIL | Failed to mint {amount:.2f} to {target_agent.id}. Memo: {memo}",
                 extra={"agent_id": target_agent.id, "amount": amount, "memo": memo}
            )

        return success

    def transfer_and_burn(self, source_agent: Any, amount: float, memo: str) -> bool:
        """
        Transfers money from the source agent to the Central Bank and 'burns' it
        (effectively removing it from circulation by crediting the CB).
        """
        success = self.settlement.transfer(
            debit_agent=source_agent,
            credit_agent=self.central_bank,
            amount=amount,
            memo=f"BURN:{memo}"
        )

        if success:
             self.logger.info(
                f"BURN_SUCCESS | Burned {amount:.2f} from {source_agent.id}. Memo: {memo}",
                extra={"agent_id": source_agent.id, "amount": amount, "memo": memo}
            )
        else:
             self.logger.error(
                f"BURN_FAIL | Failed to burn {amount:.2f} from {source_agent.id}. Memo: {memo}",
                 extra={"agent_id": source_agent.id, "amount": amount, "memo": memo}
            )

        return success
