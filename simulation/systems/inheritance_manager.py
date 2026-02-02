import logging
from typing import Optional, Dict, List, Any
from simulation.core_agents import Household
from simulation.agents.government import Government
from simulation.models import Order, Transaction
from simulation.portfolio import Portfolio

logger = logging.getLogger(__name__)

class InheritanceManager:
    """
    Phase 22 (WO-049): Legacy Protocol
    Handles Death, Valuation, Taxation (Liquidation), and Transfer.
    Ensures 'Zero Leak' and atomic settlement.
    """
    def __init__(self, config_module: Any):
        self.config_module = config_module
        self.logger = logging.getLogger("simulation.systems.inheritance_manager")

    def process_death(self, deceased: Household, government: Government, simulation: Any) -> List[Transaction]:
        """
        Executes the inheritance pipeline using Transactions.

        Args:
            deceased: The agent who died.
            government: The entity collecting tax.
            simulation: Access to markets/registry for valuation.

        Returns:
            List[Transaction]: Ordered list of transactions to be queued for next tick.
        """
        transactions: List[Transaction] = []
        current_tick = simulation.time

        self.logger.info(
            f"INHERITANCE_START | Processing death for Household {deceased.id}. Assets: {deceased._econ_state.assets:.2f}",
            extra={"agent_id": deceased.id, "tags": ["inheritance", "death"]}
        )

        # 1. Valuation (Read-only)
        cash = round(deceased._econ_state.assets, 2)
        real_estate_value = 0.0
        deceased_units = [u for u in simulation.real_estate_units if u.owner_id == deceased.id]
        for unit in deceased_units:
            real_estate_value += unit.estimated_value
        real_estate_value = round(real_estate_value, 2)

        stock_value = 0.0
        current_prices = {}
        if simulation.stock_market:
            for firm_id, share in deceased._econ_state.portfolio.holdings.items():
                price = simulation.stock_market.get_daily_avg_price(firm_id)
                if price <= 0:
                    price = share.acquisition_price
                # Round price to prevent dust
                price = round(price, 2)
                current_prices[firm_id] = price
                stock_value += share.quantity * price

        stock_value = round(stock_value, 2)
        total_wealth = round(cash + real_estate_value + stock_value, 2)

        # 2. Calculate Tax
        tax_rate = getattr(self.config_module, "INHERITANCE_TAX_RATE", 0.4)
        deduction = getattr(self.config_module, "INHERITANCE_DEDUCTION", 10000.0)
        taxable_base = max(0.0, total_wealth - deduction)
        tax_amount = round(taxable_base * tax_rate, 2)

        self.logger.info(
            f"ESTATE_VALUATION | Agent {deceased.id}: Cash={cash:.2f}, RE={real_estate_value:.2f}, Stock={stock_value:.2f} -> Total={total_wealth:.2f}. Tax={tax_amount:.2f}",
            extra={"agent_id": deceased.id, "total_wealth": total_wealth, "tax_amount": tax_amount}
        )

        # 3. Liquidation Transactions (if Cash < Tax)
        if deceased._econ_state.assets < tax_amount:
            # A. Stock Liquidation
            if stock_value > 0:
                for firm_id, share in deceased._econ_state.portfolio.holdings.items():
                    price = current_prices.get(firm_id, 0.0)
                    proceeds = round(share.quantity * price, 2) # Just for logging/logic if needed

                    tx = Transaction(
                        buyer_id=government.id,
                        seller_id=deceased.id,
                        item_id=f"stock_{firm_id}",
                        quantity=share.quantity,
                        price=price, # Unit price (already rounded above)
                        market_id="stock_market",
                        transaction_type="asset_liquidation",
                        time=current_tick
                    )
                    transactions.append(tx)

            # B. Real Estate Liquidation
            fire_sale_ratio = 0.9
            for unit in deceased_units:
                sale_price = round(unit.estimated_value * fire_sale_ratio, 2)
                tx = Transaction(
                    buyer_id=government.id,
                    seller_id=deceased.id,
                    item_id=f"real_estate_{unit.id}",
                    quantity=1.0,
                    price=sale_price,
                    market_id="real_estate_market",
                    transaction_type="asset_liquidation",
                    time=current_tick
                )
                transactions.append(tx)

        # 4. Tax Transaction
        # We cap tax paid at total wealth, but physically we can only pay with cash available at the moment of processing.
        # But TransactionProcessor will execute Liquidation first (which gives cash), then Tax.
        # So 'actual_tax_paid' here is the INTENT amount.
        # If liquidation yields less than expected, Tax tx might fail if we ask for too much.
        # But we can't know exact yield if market prices change (though here we use fixed price liquidation to Gov).
        # So yield is deterministic: 'price' in liquidation tx.

        # Safe Cap: We use tax_amount. If agent doesn't have it, Tax Handler (FinancialHandler) should handle partial or fail.
        # But FinancialHandler usually fails if insufficient funds.
        # To avoid failure, we might need to be conservative.
        # However, for now, we request the calculated tax amount.

        if tax_amount > 0:
            tx = Transaction(
                buyer_id=deceased.id,
                seller_id=government.id,
                item_id="inheritance_tax",
                quantity=1.0,
                price=tax_amount, # Use the rounded tax amount
                market_id="system",
                transaction_type="tax",
                time=current_tick
            )
            transactions.append(tx)

        # 5. Distribution / Escheatment
        heirs = []
        for child_id in deceased._bio_state.children_ids:
            child = simulation.agents.get(child_id)
            if child and child._bio_state.is_active:
                heirs.append(child)

        if not heirs:
            # Escheatment
            # We don't know exact remaining cash after tax because Liquidation happens in between.
            # So we use a special transaction type "escheatment" which EscheatmentHandler handles by taking ALL current assets.
            # So price is symbolic or estimated.

            # Escheatment of Cash
            tx_cash = Transaction(
                buyer_id=deceased.id,
                seller_id=government.id,
                item_id="escheatment_cash",
                quantity=1.0,
                price=0.0, # Handled by handler taking balance
                market_id="system",
                transaction_type="escheatment",
                time=current_tick
            )
            transactions.append(tx_cash)
            
            # Stock Escheatment (if not liquidated)
            # If we didn't liquidate (because assets >= tax), we escheat stocks now.
            if deceased._econ_state.assets >= tax_amount:
                 for firm_id, share in deceased._econ_state.portfolio.holdings.items():
                    tx = Transaction(
                        buyer_id=government.id,
                        seller_id=deceased.id,
                        item_id=f"stock_{firm_id}",
                        quantity=share.quantity,
                        price=0.0,
                        market_id="stock_market",
                        transaction_type="asset_transfer",
                        time=current_tick
                    )
                    transactions.append(tx)

                 for unit in deceased_units:
                     tx = Transaction(
                        seller_id=deceased.id,
                        buyer_id=government.id,
                        item_id=f"real_estate_{unit.id}",
                        quantity=1.0,
                        price=0.0,
                        market_id="real_estate_market",
                        transaction_type="asset_transfer",
                        time=current_tick
                     )
                     transactions.append(tx)

        else:
            # Distribution to Heirs
            # InheritanceHandler will calculate exact split of remaining assets.
            tx_dist = Transaction(
                buyer_id=deceased.id, # Source
                seller_id=heirs[0].id, # Representative? Or ignore.
                item_id="inheritance_distribution",
                quantity=1.0,
                price=0.0, # Handled by handler
                market_id="system",
                transaction_type="inheritance_distribution",
                time=current_tick,
                metadata={"heir_ids": [h.id for h in heirs]}
            )
            transactions.append(tx_dist)

        return transactions
