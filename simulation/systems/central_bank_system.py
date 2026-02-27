from typing import Any, Optional, List
import logging
from simulation.systems.api import IMintingAuthority
from simulation.systems.settlement_system import SettlementSystem
from modules.finance.api import ICentralBank, OMOInstructionDTO
from simulation.models import Order, Transaction
from modules.system.api import DEFAULT_CURRENCY

logger = logging.getLogger(__name__)

class CentralBankSystem(IMintingAuthority, ICentralBank):
    """
    System wrapper for the Central Bank Agent to act as the Minting Authority.
    Handles Non-Zero-Sum transactions (money creation/destruction).
    Also handles Open Market Operations (OMO).
    Refactored to return transactions (Bubble-up) instead of injecting them into a global list.
    """

    # OMO Configuration Constants
    BOND_PAR_VALUE_PENNIES = 10000
    OMO_BUY_LIMIT_PRICE_PENNIES = 11000
    OMO_BUY_LIMIT_PRICE = 110.0
    OMO_SELL_LIMIT_PRICE_PENNIES = 9000
    OMO_SELL_LIMIT_PRICE = 90.0

    # LLR Configuration
    LLR_LIQUIDITY_BUFFER_RATIO = 1.1

    def __init__(self, central_bank_agent: Any, settlement_system: SettlementSystem, security_market_id: str='security_market', logger: Optional[logging.Logger]=None):
        # NOTE: 'transactions' argument removed to enforce State Purity.
        self.central_bank = central_bank_agent
        self.settlement = settlement_system
        self.security_market_id = security_market_id
        self.logger = logger if logger else logging.getLogger(__name__)
        self._id = central_bank_agent.id if hasattr(central_bank_agent, 'id') else -2

    @property
    def id(self) -> int:
        return self._id

    def execute_open_market_operation(self, instruction: OMOInstructionDTO) -> List[Order]:
        """
        Takes an instruction and creates market orders to fulfill it.
        """
        orders = []
        op_type = instruction.operation_type
        amount = instruction.target_amount

        par_value_pennies = self.BOND_PAR_VALUE_PENNIES

        if op_type == 'purchase':
            limit_price_pennies = self.OMO_BUY_LIMIT_PRICE_PENNIES
            limit_price = self.OMO_BUY_LIMIT_PRICE
            quantity = amount // par_value_pennies

            if quantity > 0:
                order = Order(agent_id=self.id, side='buy', item_id='government_bond', quantity=quantity, price_pennies=limit_price_pennies, price_limit=limit_price, market_id=self.security_market_id)
                orders.append(order)
                self.logger.info(f'OMO: Placing BUY order for {quantity} bonds (Target: {amount}).')

        elif op_type == 'sale':
            limit_price_pennies = self.OMO_SELL_LIMIT_PRICE_PENNIES
            limit_price = self.OMO_SELL_LIMIT_PRICE
            quantity = amount // par_value_pennies

            if quantity > 0:
                order = Order(agent_id=self.id, side='sell', item_id='government_bond', quantity=quantity, price_pennies=limit_price_pennies, price_limit=limit_price, market_id=self.security_market_id)
                orders.append(order)
                self.logger.info(f'OMO: Placing SELL order for {quantity} bonds (Target: {amount}).')
        return orders

    def process_omo_settlement(self, transaction: Transaction) -> None:
        """
        Callback for SettlementSystem to notify the Central Bank about
        a completed OMO transaction.
        """
        if transaction.transaction_type == 'omo_purchase':
            self.logger.info(f'OMO_PURCHASE_SETTLED | CB Bought {transaction.quantity} bonds for {transaction.price}. Money Injected (Minted).')
        elif transaction.transaction_type == 'omo_sale':
            self.logger.info(f'OMO_SALE_SETTLED | CB Sold {transaction.quantity} bonds for {transaction.price}. Money Drained (Burned).')

    def mint_and_transfer(self, target_agent: Any, amount: int, memo: str) -> Optional[Transaction]:
        """
        Creates money (minting) and transfers it to the target agent.
        Returns the Transaction object if successful, None otherwise.
        """
        tx = self.settlement.create_and_transfer(
            source_authority=self.central_bank,
            destination=target_agent,
            amount=int(amount),
            reason=f'MINT:{memo}',
            tick=getattr(target_agent, 'time', 0)
        )
        if tx:
            # Removed self.transactions.append(tx)

            # TODO: Refactor direct property modification for encapsulation
            if hasattr(target_agent, 'total_money_issued'):
                target_agent.total_money_issued += amount

            self.logger.info(f'MINT_SUCCESS | Minted {amount} to {target_agent.id}. Memo: {memo}', extra={'agent_id': target_agent.id, 'amount': amount, 'memo': memo})
            return tx
        else:
            self.logger.error(f'MINT_FAIL | Failed to mint {amount} to {target_agent.id}. Memo: {memo}', extra={'agent_id': target_agent.id, 'amount': amount, 'memo': memo})
            return None

    def transfer_and_burn(self, source_agent: Any, amount: int, memo: str) -> Optional[Transaction]:
        """
        Transfers money from the source agent to the Central Bank and 'burns' it (contraction).
        Returns the Transaction object if successful, None otherwise.
        """
        tx = self.settlement.transfer_and_destroy(
            source=source_agent,
            sink_authority=self.central_bank,
            amount=int(amount),
            reason=f'BURN:{memo}',
            tick=getattr(source_agent, 'time', 0)
        )
        if tx:
            # Removed self.transactions.append(tx)

            self.logger.info(f'BURN_SUCCESS | Burned {amount} from {source_agent.id}. Memo: {memo}', extra={'agent_id': source_agent.id, 'amount': amount, 'memo': memo})
            return tx
        else:
            self.logger.error(f'BURN_FAIL | Failed to burn {amount} from {source_agent.id}. Memo: {memo}', extra={'agent_id': source_agent.id, 'amount': amount, 'memo': memo})
            return None

    def check_and_provide_liquidity(self, bank_agent: Any, amount_needed: int) -> Optional[Transaction]:
        """
        Checks if the bank has sufficient liquidity.
        If not, provides emergency liquidity via minting (LLR).
        Returns the Transaction if liquidity was provided, None otherwise.
        """
        if not hasattr(bank_agent, 'get_balance'):
            return None

        current_balance = bank_agent.get_balance(DEFAULT_CURRENCY)
        threshold = int(amount_needed * self.LLR_LIQUIDITY_BUFFER_RATIO)

        if current_balance < threshold:
            shortfall = threshold - current_balance
            if shortfall > 0:
                self.logger.info(f"LLR_TRIGGERED | Bank {bank_agent.id} low liquidity: {current_balance} < {threshold}. Injecting {shortfall}.")
                return self.mint_and_transfer(bank_agent, shortfall, "LLR_LIQUIDITY_INJECTION")

        return None
