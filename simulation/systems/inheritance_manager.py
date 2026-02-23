import logging
from typing import Optional, Dict, List, Any, TYPE_CHECKING
from simulation.core_agents import Household
from simulation.agents.government import Government
from simulation.models import Order, Transaction
from simulation.portfolio import Portfolio
from modules.system.api import DEFAULT_CURRENCY
from modules.system.constants import ID_SYSTEM

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from simulation.dtos.api import SimulationState

class InheritanceManager:
    """
    Phase 22 (WO-049): Legacy Protocol
    Handles Death, Valuation, Taxation (Liquidation), and Transfer.
    Ensures 'Zero Leak' and atomic settlement via SettlementSystem.
    """
    def __init__(self, config_module: Any):
        self.config_module = config_module
        self.logger = logging.getLogger("simulation.systems.inheritance_manager")

    def process_death(self, deceased: Household, government: Government, simulation: "SimulationState") -> List[Transaction]:
        """
        Executes the inheritance pipeline using SettlementSystem (Atomic).

        Args:
            deceased: The agent who died.
            government: The entity collecting tax.
            simulation: Access to markets/registry for valuation and settlement_system.

        Returns:
            List[Transaction]: Ordered list of executed transaction receipts.
        """
        transactions: List[Transaction] = []
        current_tick = simulation.time
        # settlement_system = simulation.settlement_system # TD-232: Removed direct dependency

        # 1. Valuation & Asset Gathering
        # ------------------------------------------------------------------
        cash_raw = deceased._econ_state.assets

        # Check if assets are in Pennies (int) or Dollars (float/legacy dict)
        is_pennies = False
        cash = 0.0 # Float fallback
        cash_pennies = 0

        if isinstance(cash_raw, dict):
            # EconStateDTO returns { "USD": int_pennies }
            cash_val = cash_raw.get(DEFAULT_CURRENCY, 0)
            if isinstance(cash_val, int):
                is_pennies = True
                cash_pennies = cash_val
            else:
                cash = float(cash_val)
                cash_pennies = int(round(cash * 100))
        elif isinstance(cash_raw, int):
            is_pennies = True
            cash_pennies = cash_raw
        else:
             cash = float(cash_raw)
             cash_pennies = int(round(cash * 100))

        cash_display = cash_pennies / 100.0

        self.logger.info(
            f"INHERITANCE_START | Processing death for Household {deceased.id}. Assets: {cash_display:.2f}",
            extra={"agent_id": deceased.id, "tags": ["inheritance", "death"]}
        )

        deceased_units = [u for u in simulation.real_estate_units if u.owner_id == deceased.id]
        real_estate_value = sum(u.estimated_value for u in deceased_units)
        real_estate_pennies = int(round(real_estate_value * 100))

        portfolio_holdings = deceased._econ_state.portfolio.holdings.copy() # dict of firm_id -> Share
        stock_value = 0.0
        current_prices = {}
        if simulation.stock_market:
            for firm_id, share in portfolio_holdings.items():
                price = simulation.stock_market.get_daily_avg_price(firm_id)
                if price <= 0:
                    price = share.acquisition_price
                price = round(price, 2)
                current_prices[firm_id] = price
                stock_value += share.quantity * price

        stock_pennies = int(round(stock_value * 100))

        total_wealth_pennies = cash_pennies + real_estate_pennies + stock_pennies

        # 1.5 Debt Repayment (Phase 4.1)
        # ------------------------------------------------------------------
        bank = getattr(simulation, 'bank', None)
        if bank and hasattr(bank, 'get_debt_status'):
            debt_status = bank.get_debt_status(deceased.id)
            if debt_status.total_outstanding_pennies > 0:
                for loan in debt_status.loans:
                    # LoanDTO uses float dollars for outstanding_balance usually (Legacy), but we try to be penny safe.
                    loan_balance_pennies = int(round(loan.outstanding_balance * 100))

                    if loan_balance_pennies > 0 and cash_pennies > 0:
                        repay_pennies = min(cash_pennies, loan_balance_pennies)
                        repay_amount = repay_pennies / 100.0

                        if repay_pennies > 0:
                            # Create Repayment Transaction
                            tx = Transaction(
                                buyer_id=deceased.id,
                                seller_id=bank.id,
                                item_id=loan.loan_id,
                                quantity=1,
                                price=repay_amount,
                                total_pennies=repay_pennies,
                                market_id="financial",
                                transaction_type="loan_repayment",
                                time=current_tick
                            )
                            results = simulation.transaction_processor.execute(simulation, [tx])
                            if results and results[0].success:
                                transactions.append(tx)
                                cash_pennies -= repay_pennies
                                self.logger.info(f"DEBT_REPAID | Repaid {repay_amount} on loan {loan.loan_id}")

        # 2. Liquidation for Tax (if needed)
        # ------------------------------------------------------------------
        tax_rate = getattr(self.config_module, "INHERITANCE_TAX_RATE", 0.4)
        deduction = getattr(self.config_module, "INHERITANCE_DEDUCTION", 10000.0)

        # Calculate tax in pennies
        deduction_pennies = int(round(deduction * 100))
        taxable_base_pennies = max(0, total_wealth_pennies - deduction_pennies)
        tax_amount_pennies = int(round(taxable_base_pennies * tax_rate))

        if cash_pennies < tax_amount_pennies:
            # Need to liquidate assets to pay tax.
            needed_pennies = tax_amount_pennies - cash_pennies

            # A. Stock Liquidation
            if needed_pennies > 0 and stock_pennies > 0:
                for firm_id, share in list(portfolio_holdings.items()):
                    price = current_prices.get(firm_id, 0.0)
                    proceeds = round(share.quantity * price, 2)
                    proceeds_pennies = int(round(proceeds * 100))

                    # TD-232: Use TransactionProcessor for atomic execution + side effects
                    tx = Transaction(
                        buyer_id=government.id,
                        seller_id=deceased.id,
                        item_id=f"stock_{firm_id}",
                        quantity=share.quantity,
                        price=price,
                        total_pennies=proceeds_pennies,
                        market_id="stock_market",
                        transaction_type="asset_liquidation",
                        time=current_tick,
                        metadata={"executed": False}
                    )

                    results = simulation.transaction_processor.execute(simulation, [tx])

                    if results and results[0].success:
                        # Success - proceeds have been transferred and assets moved by Handler
                        if firm_id in portfolio_holdings:
                             del portfolio_holdings[firm_id] # Keep local copy in sync

                        # Mark as executed for reporting
                        tx.metadata["executed"] = True
                        transactions.append(tx)

                        cash_pennies += proceeds_pennies
                        needed_pennies -= proceeds_pennies
                        if needed_pennies <= 0:
                            break

            # B. Real Estate Liquidation
            if needed_pennies > 0 and real_estate_pennies > 0:
                fire_sale_ratio = 0.9
                for unit in list(deceased_units):
                    sale_price = round(unit.estimated_value * fire_sale_ratio, 2)
                    sale_price_pennies = int(round(sale_price * 100))

                    # TD-232: Use TransactionProcessor
                    tx = Transaction(
                        buyer_id=government.id,
                        seller_id=deceased.id,
                        item_id=f"real_estate_{unit.id}",
                        quantity=1.0,
                        price=sale_price,
                        total_pennies=sale_price_pennies,
                        market_id="real_estate_market",
                        transaction_type="asset_liquidation",
                        time=current_tick,
                        metadata={"executed": False}
                    )

                    results = simulation.transaction_processor.execute(simulation, [tx])

                    if results and results[0].success:
                        deceased_units.remove(unit)
                        tx.metadata["executed"] = True
                        transactions.append(tx)

                        cash_pennies += sale_price_pennies
                        needed_pennies -= sale_price_pennies
                        if needed_pennies <= 0:
                            break

        # 3. TD-232: Removed explicit Settlement Account creation.
        # Assets remain on Deceased agent until moved by TransactionProcessor.

        # 4. Plan Distribution & Execution
        # ------------------------------------------------------------------

        # A. Tax
        tax_to_pay_pennies = min(cash_pennies, tax_amount_pennies)
        if tax_to_pay_pennies > 0:
            tx = Transaction(
                buyer_id=deceased.id, # Payer
                seller_id=government.id, # Payee
                item_id="inheritance_tax",
                quantity=1.0,
                price=tax_to_pay_pennies / 100.0,
                total_pennies=tax_to_pay_pennies,
                market_id="system",
                transaction_type="tax",
                time=current_tick
            )
            results = simulation.transaction_processor.execute(simulation, [tx])
            if results and results[0].success:
                transactions.append(tx)
                cash_pennies -= tax_to_pay_pennies

        # B. Heirs & Escheatment
        heirs = []
        for child_id in deceased._bio_state.children_ids:
            child = simulation.agents.get(child_id)
            if child and child._bio_state.is_active:
                heirs.append(child)

        if not heirs:
            # Escheatment (To Gov)
            if cash_pennies > 0:
                # TD-232: Escheatment via TransactionProcessor
                # Note: EscheatmentHandler transfers ALL assets.
                # Since we already paid tax, remaining cash is escheated.
                tx = Transaction(
                    buyer_id=deceased.id,
                    seller_id=government.id,
                    item_id="escheatment",
                    quantity=1.0,
                    price=cash_pennies / 100.0, # Used for record, handler takes all
                    total_pennies=cash_pennies,
                    market_id="system",
                    transaction_type="escheatment",
                    time=current_tick
                )
                results = simulation.transaction_processor.execute(simulation, [tx])
                if results and results[0].success:
                    transactions.append(tx)

            # Escheat remaining Real Estate (Execute Synchronously)
            for unit in deceased_units:
                 tx = Transaction(
                        buyer_id=government.id,
                        seller_id=deceased.id,
                        item_id=f"real_estate_{unit.id}",
                        quantity=1.0,
                        price=0.0,
                        total_pennies=0,
                        market_id="real_estate_market",
                        transaction_type="asset_transfer",
                        time=current_tick,
                        metadata={"executed": False}
                     )

                 results = simulation.transaction_processor.execute(simulation, [tx])
                 if results and results[0].success:
                     tx.metadata["executed"] = True
                     transactions.append(tx)

        else:
            # Distribute to Heirs
            # Cash & Portfolio via InheritanceHandler (Single Transaction)
            if cash_pennies > 0:
                tx = Transaction(
                    buyer_id=deceased.id,
                    seller_id=ID_SYSTEM, # System distribution (Fixed COLLISION with PublicManager -1)
                    item_id="estate_distribution",
                    quantity=1.0,
                    price=cash_pennies / 100.0, # Informational
                    total_pennies=cash_pennies,
                    market_id="system",
                    transaction_type="inheritance_distribution",
                    time=current_tick,
                    metadata={"heir_ids": [h.id for h in heirs]}
                )
                results = simulation.transaction_processor.execute(simulation, [tx])
                if results and results[0].success:
                    transactions.append(tx)

            # Distribute Real Estate (Round Robin - Synchronous)
            count = len(heirs)
            for i, unit in enumerate(deceased_units):
                recipient = heirs[i % count]

                tx = Transaction(
                        buyer_id=recipient.id,
                        seller_id=deceased.id,
                        item_id=f"real_estate_{unit.id}",
                        quantity=1.0,
                        price=0.0,
                        total_pennies=0,
                        market_id="real_estate_market",
                        transaction_type="asset_transfer",
                        time=current_tick,
                        metadata={"executed": False}
                     )

                results = simulation.transaction_processor.execute(simulation, [tx])
                if results and results[0].success:
                    tx.metadata["executed"] = True
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
