from modules.system.api import TransactionMetadataDTO
import logging
from typing import Optional, Dict, List, Any, TYPE_CHECKING
from simulation.models import Order, Transaction
from simulation.portfolio import Portfolio
from modules.system.api import DEFAULT_CURRENCY
from modules.system.constants import ID_SYSTEM

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from simulation.dtos.api import SimulationState
    from simulation.core_agents import Household
    from simulation.agents.government import Government
    from modules.lifecycle.api import ISuccessionContext

class InheritanceManager:
    """
    Phase 22 (WO-049): Legacy Protocol
    Handles Death, Valuation, Taxation (Liquidation), and Transfer.
    Ensures 'Zero Leak' and atomic settlement via SettlementSystem.
    """
    def __init__(self, config_module: Any, context: Optional["IPopulationContext"] = None):
        self.config_module = config_module
        self.logger = logging.getLogger("simulation.systems.inheritance_manager")
        self.world_state = context

    def process_death(self, deceased: "Household", context: "ISuccessionContext") -> List[Transaction]:
        """
        Executes the inheritance pipeline using SuccessionContext (Atomic).

        Args:
            deceased: The agent who died.
            context: Access to specific state subset via ISuccessionContext

        Returns:
            List[Transaction]: Ordered list of executed transaction receipts.
        """
        transactions: List[Transaction] = []
        current_tick = context.current_tick
        gov_id = context.government_id

        # 1. Valuation & Asset Gathering
        # ------------------------------------------------------------------
        # NEW: Shared Wallet Protection (WO-IMPL-SCENARIO-MIGRATION)
        # If the deceased shares a wallet owned by someone else (e.g. Spouse),
        # we treat their personal cash holdings as their SHARE of the joint balance.
        # This prevents draining the survivor's funds (if owner is survivor)
        # while still ensuring the deceased's share is taxed/used for debt.
        joint_share_ratio = getattr(self.config_module, "JOINT_ACCOUNT_SHARE", 0.5)
        is_shared_wallet = False
        if hasattr(deceased, '_econ_state') and hasattr(deceased._econ_state, 'wallet'):
             if getattr(deceased._econ_state.wallet, 'owner_id', None) != deceased.id:
                 is_shared_wallet = True
                 self.logger.info(f"INHERITANCE_PROTECT | Agent {deceased.id} is guest in wallet owned by {getattr(deceased._econ_state.wallet, 'owner_id', 'Unknown')}. Using {joint_share_ratio:.0%} share.")

        if is_shared_wallet:
             # Calculate share from wallet balance
             wallet_balance = deceased._econ_state.wallet.get_balance(DEFAULT_CURRENCY)
             cash = float(wallet_balance) * joint_share_ratio
        else:
            cash_raw = getattr(deceased._econ_state, 'assets', 0.0)
            if isinstance(cash_raw, dict):
                cash = float(cash_raw.get(DEFAULT_CURRENCY, 0.0))
            else:
                cash = float(cash_raw)
            cash = round(cash, 2)

        self.logger.info(
            f"INHERITANCE_START | Processing death for Household {deceased.id}. Assets: {cash:.2f}",
            extra={"agent_id": deceased.id, "tags": ["inheritance", "death"]}
        )

        deceased_units = context.get_real_estate_units(deceased.id)
        real_estate_value = sum(getattr(u, 'estimated_value', 0.0) for u in deceased_units)
        real_estate_value = round(real_estate_value, 2)

        portfolio_holdings = getattr(deceased._econ_state.portfolio, 'holdings', {}).copy() # dict of firm_id -> Share
        stock_value = 0.0
        current_prices = {}
        for firm_id, share in portfolio_holdings.items():
            price = context.get_stock_price(firm_id)
            if price <= 0:
                price = getattr(share, 'acquisition_price', 0.0)
            price = round(price, 2)
            current_prices[firm_id] = price
            stock_value += getattr(share, 'quantity', 0.0) * price

        stock_value = round(stock_value, 2)
        total_wealth = round(cash + real_estate_value + stock_value, 2)

        # 1.5 Debt Repayment (Phase 4.1)
        # ------------------------------------------------------------------
        debt_status = context.get_debt_status(deceased.id)
        if getattr(debt_status, 'total_outstanding_pennies', 0) > 0:
            for loan in debt_status.loans:
                outstanding = getattr(loan, 'outstanding_balance', 0)
                loan_id = getattr(loan, 'loan_id', "unknown_loan")
                if outstanding > 0 and cash > 0:
                    repay_amount = min(cash, outstanding)
                    repay_pennies = int(repay_amount) # Convert back to pennies

                    if repay_pennies > 0:
                        # Create Repayment Transaction
                        tx = Transaction(
                            buyer_id=deceased.id,
                            seller_id=ID_SYSTEM, # Simplified for mock resilience, properly the Bank
                            item_id=loan_id,
                            quantity=1,
                            price=repay_amount,
                            total_pennies=repay_pennies,
                            market_id="financial",
                            transaction_type="loan_repayment",
                            time=current_tick
                        )
                        results = context.execute_transactions([tx])
                        if results and getattr(results[0], 'success', False):
                            transactions.append(tx)
                            cash -= repay_amount
                            self.logger.info(f"DEBT_REPAID | Repaid {repay_amount} on loan {loan_id}")

        # 2. Liquidation for Tax (if needed)
        # ------------------------------------------------------------------
        tax_rate = getattr(self.config_module, "INHERITANCE_TAX_RATE", 0.4)
        deduction = getattr(self.config_module, "INHERITANCE_DEDUCTION", 10000.0)
        taxable_base = max(0.0, total_wealth - deduction)
        tax_amount = round(taxable_base * tax_rate, 2)

        if cash < tax_amount:
            # Need to liquidate assets to pay tax.
            # We liquidate to Government (Simulated Buyback) for simplicity and speed (Atomic).

            needed = tax_amount - cash

            # A. Stock Liquidation
            if needed > 0 and stock_value > 0:
                for firm_id, share in list(portfolio_holdings.items()):
                    price = current_prices.get(firm_id, 0.0)

                    # Portfolio holdings could be integers/floats directly in some mock setups
                    # Let's ensure we extract quantity correctly even if share isn't a complex object
                    if hasattr(share, 'quantity'):
                        qty = share.quantity
                    else:
                        qty = float(share) if isinstance(share, (int, float)) else 0.0

                    proceeds = round(qty * price, 2)

                    # TD-232: Use TransactionProcessor for atomic execution + side effects
                    tx = Transaction(
                        buyer_id=government.id,
                        seller_id=deceased.id,
                        item_id=f"stock_{firm_id}",
                        quantity=share.quantity,
                        price=price,
                        total_pennies=int(proceeds * 100),
                        market_id="stock_market",
                        transaction_type="asset_liquidation",
                        time=current_tick,
                        metadata=TransactionMetadataDTO(original_metadata={"executed": False})
                    )

                    results = simulation.transaction_processor.execute(simulation, [tx])

                    if results and results[0].success:
                        # Success - proceeds have been transferred and assets moved by Handler
                        if firm_id in portfolio_holdings:
                             del portfolio_holdings[firm_id] # Keep local copy in sync

                        # Mark as executed for reporting
                        tx.metadata["executed"] = True
                        transactions.append(tx)

                        cash += proceeds
                        needed -= proceeds
                        if needed <= 0:
                            break

            # B. Real Estate Liquidation
            if needed > 0 and real_estate_value > 0:
                fire_sale_ratio = 0.9
                for unit in list(deceased_units):
                    sale_price = round(unit.estimated_value * fire_sale_ratio, 2)

                    # TD-232: Use TransactionProcessor
                    tx = Transaction(
                        buyer_id=government.id,
                        seller_id=deceased.id,
                        item_id=f"real_estate_{unit.id}",
                        quantity=1.0,
                        price=sale_price,
                        total_pennies=int(sale_price * 100),
                        market_id="real_estate_market",
                        transaction_type="asset_liquidation",
                        time=current_tick,
                        metadata=TransactionMetadataDTO(original_metadata={"executed": False})
                    )

                    results = simulation.transaction_processor.execute(simulation, [tx])

                    if results and results[0].success:
                        deceased_units.remove(unit)
                        tx.metadata["executed"] = True
                        transactions.append(tx)

                        cash += sale_price
                        needed -= sale_price
                        if needed <= 0:
                            break

        # 3. TD-232: Removed explicit Settlement Account creation.
        # Assets remain on Deceased agent until moved by TransactionProcessor.

        # 4. Plan Distribution & Execution
        # ------------------------------------------------------------------

        # A. Tax
        tax_to_pay = min(cash, tax_amount)
        if tax_to_pay > 0:
            tx = Transaction(
                buyer_id=deceased.id, # Payer
                seller_id=gov_id, # Payee
                item_id="inheritance_tax",
                quantity=1.0,
                price=tax_to_pay,
                total_pennies=int(tax_to_pay * 100),
                market_id="system",
                transaction_type="tax",
                time=current_tick
            )
            results = context.execute_transactions([tx])
            if results and getattr(results[0], 'success', False):
                transactions.append(tx)
                cash -= tax_to_pay

        # B. Heirs & Escheatment
        heirs = context.get_active_heirs(getattr(deceased._bio_state, 'children_ids', []))

        if not heirs:
            # Escheatment (To Gov)
            if cash > 0:
                # TD-232: Escheatment via TransactionProcessor
                # Note: EscheatmentHandler transfers ALL assets.
                # Since we already paid tax, remaining cash is escheated.
                tx = Transaction(
                    buyer_id=deceased.id,
                    seller_id=gov_id,
                    item_id="escheatment",
                    quantity=1.0,
                    price=cash, # Used for record, handler takes all
                    total_pennies=int(cash * 100),
                    market_id="system",
                    transaction_type="escheatment",
                    time=current_tick
                )
                results = context.execute_transactions([tx])
                if results and getattr(results[0], 'success', False):
                    transactions.append(tx)

            # Escheat remaining Real Estate (Execute Synchronously)
            for unit in deceased_units:
                 tx = Transaction(
                        buyer_id=gov_id,
                        seller_id=deceased.id,
                        item_id=f"real_estate_{getattr(unit, 'id', 'unknown')}",
                        quantity=1.0,
                        price=0.0,
                        total_pennies=0,
                        market_id="real_estate_market",
                        transaction_type="asset_transfer",
                        time=current_tick,
                        metadata=TransactionMetadataDTO(original_metadata={"executed": False})
                     )

                 results = context.execute_transactions([tx])
                 if results and getattr(results[0], 'success', False):
                     if hasattr(tx, 'metadata') and hasattr(tx.metadata, 'original_metadata'):
                         tx.metadata.original_metadata["executed"] = True
                     transactions.append(tx)

        else:
            # Distribute to Heirs
            # Cash & Portfolio via InheritanceHandler (Single Transaction)
            if cash > 0:
                tx = Transaction(
                    buyer_id=deceased.id,
                    seller_id=ID_SYSTEM, # System distribution (Fixed COLLISION with PublicManager -1)
                    item_id="estate_distribution",
                    quantity=1.0,
                    price=cash, # Informational
                    total_pennies=int(cash * 100),
                    market_id="system",
                    transaction_type="inheritance_distribution",
                    time=current_tick,
                    metadata=TransactionMetadataDTO(original_metadata={"heir_ids": [h.id for h in heirs]})
                )
                results = context.execute_transactions([tx])
                if results and getattr(results[0], 'success', False):
                    transactions.append(tx)

            # Distribute Real Estate (Round Robin - Synchronous)
            count = len(heirs)
            for i, unit in enumerate(deceased_units):
                recipient = heirs[i % count]

                tx = Transaction(
                        buyer_id=recipient.id,
                        seller_id=deceased.id,
                        item_id=f"real_estate_{getattr(unit, 'id', 'unknown')}",
                        quantity=1.0,
                        price=0.0,
                        total_pennies=0,
                        market_id="real_estate_market",
                        transaction_type="asset_transfer",
                        time=current_tick,
                        metadata=TransactionMetadataDTO(original_metadata={"executed": False})
                     )

                results = context.execute_transactions([tx])
                if results and getattr(results[0], 'success', False):
                    if hasattr(tx, 'metadata') and hasattr(tx.metadata, 'original_metadata'):
                        tx.metadata.original_metadata["executed"] = True
                    transactions.append(tx)

        # 5. TD-232: Removed execute_settlement as we dispatched transactions directly.

        # 6. TD-232: Removed verify_and_close as no Settlement Account was created.

        return transactions

    def _dict_to_transaction(self, tx_dict: dict) -> Transaction:
         # Deprecated but kept if needed by other methods not shown
         return Transaction(
             buyer_id=tx_dict["buyer_id"],
             seller_id=tx_dict["seller_id"],
             item_id=tx_dict["item_id"],
             quantity=tx_dict["quantity"],
             price=tx_dict["price"],
             market_id=tx_dict["market_id"],
             transaction_type=tx_dict["transaction_type"],
             time=tx_dict["time"],
             metadata=tx_dict["metadata"]
         , total_pennies=int(tx_dict["price"] * tx_dict["quantity"] * 100))
