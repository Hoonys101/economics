import logging
from _typeshed import Incomplete
from modules.finance.api import ICentralBank, OMOInstructionDTO as OMOInstructionDTO
from simulation.models import Order as Order, Transaction as Transaction
from simulation.systems.api import IMintingAuthority as IMintingAuthority
from simulation.systems.settlement_system import SettlementSystem as SettlementSystem
from typing import Any

logger: Incomplete

class CentralBankSystem(IMintingAuthority, ICentralBank):
    """
    System wrapper for the Central Bank Agent to act as the Minting Authority.
    Handles Non-Zero-Sum transactions (money creation/destruction).
    Also handles Open Market Operations (OMO).
    """
    BOND_PAR_VALUE_PENNIES: int
    OMO_BUY_LIMIT_PRICE_PENNIES: int
    OMO_BUY_LIMIT_PRICE: float
    OMO_SELL_LIMIT_PRICE_PENNIES: int
    OMO_SELL_LIMIT_PRICE: float
    central_bank: Incomplete
    settlement: Incomplete
    transactions: Incomplete
    security_market_id: Incomplete
    logger: Incomplete
    def __init__(self, central_bank_agent: Any, settlement_system: SettlementSystem, transactions: list[Any], security_market_id: str = 'security_market', logger: logging.Logger | None = None) -> None: ...
    @property
    def id(self) -> int: ...
    def execute_open_market_operation(self, instruction: OMOInstructionDTO) -> list[Order]:
        """
        Takes an instruction and creates market orders to fulfill it.
        """
    def process_omo_settlement(self, transaction: Transaction) -> None:
        """
        Callback for SettlementSystem to notify the Central Bank about
        a completed OMO transaction.
        """
    def mint_and_transfer(self, target_agent: Any, amount: int, memo: str) -> bool:
        """
        Creates money (minting) and transfers it to the target agent.
        """
    def transfer_and_burn(self, source_agent: Any, amount: int, memo: str) -> bool:
        """
        Transfers money from the source agent to the Central Bank and 'burns' it (contraction).
        """
    def check_and_provide_liquidity(self, bank_agent: Any, amount_needed: int) -> bool:
        """
        Checks if the bank has sufficient liquidity for a critical transaction.
        If not, provides emergency liquidity via minting (Lender of Last Resort).
        """
