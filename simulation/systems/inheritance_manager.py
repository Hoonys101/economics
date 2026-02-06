import logging
from typing import Optional, Dict, List, Any, TYPE_CHECKING
from simulation.core_agents import Household
from simulation.agents.government import Government
from simulation.models import Order, Transaction
from simulation.portfolio import Portfolio
from modules.system.api import DEFAULT_CURRENCY

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
        cash = cash_raw
        if isinstance(cash_raw, dict):
            cash = cash_raw.get(DEFAULT_CURRENCY, 0.0)
        cash = round(cash, 2)

        self.logger.info(
            f"INHERITANCE_START | Processing death for Household {deceased.id}. Assets: {cash:.2f}",
            extra={"agent_id": deceased.id, "tags": ["inheritance", "death"]}
        )

        deceased_units = [u for u in simulation.real_estate_units if u.owner_id == deceased.id]
        real_estate_value = sum(u.estimated_value for u in deceased_units)
        real_estate_value = round(real_estate_value, 2)

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

        stock_value = round(stock_value, 2)
        total_wealth = round(cash + real_estate_value + stock_value, 2)

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
                    proceeds = round(share.quantity * price, 2)

                    # TD-232: Use TransactionProcessor for atomic execution + side effects
                    tx = Transaction(
                        buyer_id=government.id,
                        seller_id=deceased.id,
                        item_id=f"stock_{firm_id}",
                        quantity=share.quantity,
                        price=price,
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
                seller_id=government.id, # Payee
                item_id="inheritance_tax",
                quantity=1.0,
                price=tax_to_pay,
                market_id="system",
                transaction_type="tax",
                time=current_tick
            )
            results = simulation.transaction_processor.execute(simulation, [tx])
            if results and results[0].success:
                transactions.append(tx)
                cash -= tax_to_pay

        # B. Heirs & Escheatment
        heirs = []
        for child_id in deceased._bio_state.children_ids:
            child = simulation.agents.get(child_id)
            if child and child._bio_state.is_active:
                heirs.append(child)

        if not heirs:
            # Escheatment (To Gov)
            if cash > 0:
                # TD-232: Escheatment via TransactionProcessor
                # Note: EscheatmentHandler transfers ALL assets.
                # Since we already paid tax, remaining cash is escheated.
                tx = Transaction(
                    buyer_id=deceased.id,
                    seller_id=government.id,
                    item_id="escheatment",
                    quantity=1.0,
                    price=cash, # Used for record, handler takes all
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
            if cash > 0:
                tx = Transaction(
                    buyer_id=deceased.id,
                    seller_id=-1, # System distribution (Fixed NOT NULL constraint)
                    item_id="estate_distribution",
                    quantity=1.0,
                    price=cash, # Informational
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
         )
