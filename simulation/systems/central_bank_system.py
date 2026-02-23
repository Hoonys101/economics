from typing import Any, Optional, List
import logging
from simulation.systems.api import IMintingAuthority
from simulation.systems.settlement_system import SettlementSystem
from modules.finance.api import ICentralBank, OMOInstructionDTO
from simulation.models import Order, Transaction
logger = logging.getLogger(__name__)

class CentralBankSystem(IMintingAuthority, ICentralBank):
    """
    System wrapper for the Central Bank Agent to act as the Minting Authority.
    Handles Non-Zero-Sum transactions (money creation/destruction).
    Also handles Open Market Operations (OMO).
    """

    def __init__(self, central_bank_agent: Any, settlement_system: SettlementSystem, transactions: List[Any], security_market_id: str='security_market', logger: Optional[logging.Logger]=None):
        self.central_bank = central_bank_agent
        self.settlement = settlement_system
        self.transactions = transactions
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
        op_type = instruction['operation_type']
        amount = instruction['target_amount']
        if op_type == 'purchase':
            order = Order(agent_id=self.id, side='buy', item_id='government_bond', quantity=amount, price_pennies=int(9999 * 100), price_limit=9999, market_id=self.security_market_id)
            orders.append(order)
            self.logger.info(f'OMO: Placing BUY order for {amount} bonds.')
        elif op_type == 'sale':
            order = Order(agent_id=self.id, side='sell', item_id='government_bond', quantity=amount, price_pennies=int(0 * 100), price_limit=0, market_id=self.security_market_id)
            orders.append(order)
            self.logger.info(f'OMO: Placing SELL order for {amount} bonds.')
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

    def mint_and_transfer(self, target_agent: Any, amount: float, memo: str) -> bool:
        """
        Creates money (by withdrawing from Central Bank which can go negative)
        and transfers it to the target agent.
        """
        tx = self.settlement.transfer(debit_agent=self.central_bank, credit_agent=target_agent, amount=amount, memo=f'MINT:{memo}')
        if tx:
            # Capture the transaction for the global ledger
            self.transactions.append(tx)

            if hasattr(target_agent, 'total_money_issued'):
                target_agent.total_money_issued += amount

            self.logger.info(f'MINT_SUCCESS | Minted {amount:.2f} to {target_agent.id}. Memo: {memo}', extra={'agent_id': target_agent.id, 'amount': amount, 'memo': memo})
            return True
        else:
            self.logger.error(f'MINT_FAIL | Failed to mint {amount:.2f} to {target_agent.id}. Memo: {memo}', extra={'agent_id': target_agent.id, 'amount': amount, 'memo': memo})
            return False

    def transfer_and_burn(self, source_agent: Any, amount: float, memo: str) -> bool:
        """
        Transfers money from the source agent to the Central Bank and 'burns' it
        (effectively removing it from circulation by crediting the CB).
        """
        tx = self.settlement.transfer(debit_agent=source_agent, credit_agent=self.central_bank, amount=amount, memo=f'BURN:{memo}')
        if tx:
            # Capture the transaction for the global ledger
            self.transactions.append(tx)

            self.logger.info(f'BURN_SUCCESS | Burned {amount:.2f} from {source_agent.id}. Memo: {memo}', extra={'agent_id': source_agent.id, 'amount': amount, 'memo': memo})
            return True
        else:
            self.logger.error(f'BURN_FAIL | Failed to burn {amount:.2f} from {source_agent.id}. Memo: {memo}', extra={'agent_id': source_agent.id, 'amount': amount, 'memo': memo})
            return False

    def check_and_provide_liquidity(self, bank_agent: Any, amount_needed: int) -> bool:
        """
        Checks if the bank has sufficient liquidity for a critical transaction.
        If not, provides emergency liquidity via minting (Lender of Last Resort).
        """
        # 1. Check current balance
        if not hasattr(bank_agent, 'get_balance'):
            return False

        # Use DEFAULT_CURRENCY from imports
        from modules.system.api import DEFAULT_CURRENCY
        current_balance = bank_agent.get_balance(DEFAULT_CURRENCY)

        # 2. Determine Threshold (e.g. 110% of needed amount to avoid edge cases)
        threshold = int(amount_needed * 1.1)

        if current_balance < threshold:
            shortfall = threshold - current_balance
            if shortfall > 0:
                self.logger.info(f"LLR_TRIGGERED | Bank {bank_agent.id} low liquidity: {current_balance} < {threshold}. Injecting {shortfall}.")
                # 3. Mint and Transfer
                return self.mint_and_transfer(bank_agent, shortfall, "LLR_LIQUIDITY_INJECTION")

        return False