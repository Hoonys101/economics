from __future__ import annotations
from typing import List, Any, Callable, TYPE_CHECKING
import logging

from simulation.models import Transaction
from simulation.core_agents import Household
from simulation.firms import Firm

if TYPE_CHECKING:
    from simulation.world_state import WorldState

logger = logging.getLogger(__name__)

class ActionProcessor:
    """
    Processes actions and transactions in the simulation.
    Decomposed from Simulation engine.
    """

    def __init__(self, world_state: WorldState):
        self.world_state = world_state

    def process_transactions(
        self,
        transactions: List[Transaction],
        market_data_callback: Callable[[], Any]
    ) -> None:
        """
        Delegates transaction processing to the TransactionProcessor system.
        """
        if self.world_state.transaction_processor:
            self.world_state.transaction_processor.process(
                transactions=transactions,
                agents=self.world_state.agents,
                government=self.world_state.government,
                current_time=self.world_state.time,
                market_data_callback=market_data_callback
            )
        else:
            logger.error("TransactionProcessor is not initialized in WorldState.")

    def process_stock_transactions(self, transactions: List[Transaction]) -> None:
        """Process stock transactions."""
        # Use local references for speed/clarity
        agents = self.world_state.agents
        stock_market = self.world_state.stock_market
        time = self.world_state.time

        for tx in transactions:
            buyer_id = tx.buyer_id
            seller_id = tx.seller_id
            buyer = agents.get(buyer_id)
            seller = agents.get(seller_id)

            # Correct firm_id parsing from stock_{id}
            try:
                firm_id = int(tx.item_id.split("_")[1])
            except (IndexError, ValueError):
                continue

            if buyer and seller:
                cost = tx.price * tx.quantity

                # Buyer: Update assets and Portfolio
                buyer.assets -= cost
                if hasattr(buyer, "portfolio"):
                    buyer.portfolio.add(firm_id, tx.quantity, tx.price)
                    # Sync legacy dict
                    buyer.shares_owned[firm_id] = buyer.portfolio.holdings[firm_id].quantity

                # Seller: Update assets
                seller.assets += cost

                # Update treasury shares if firm is the seller (SEO)
                if isinstance(seller, Firm) and seller.id == firm_id:
                    seller.treasury_shares -= tx.quantity
                elif hasattr(seller, "portfolio"):
                    # Secondary market trade
                    seller.portfolio.remove(firm_id, tx.quantity)

                # Sync Legacy Dictionaries for Seller
                if hasattr(seller, "shares_owned"):
                    if hasattr(seller, "portfolio") and firm_id in seller.portfolio.holdings:
                        seller.shares_owned[firm_id] = seller.portfolio.holdings[firm_id].quantity
                    elif firm_id in seller.shares_owned:
                        del seller.shares_owned[firm_id]

                # Synchronize Market Shareholder Registry (CRITICAL for Dividends)
                if stock_market:
                    # Sync Buyer
                    if hasattr(buyer, "portfolio") and firm_id in buyer.portfolio.holdings:
                         stock_market.update_shareholder(buyer.id, firm_id, buyer.portfolio.holdings[firm_id].quantity)

                    # Sync Seller
                    if hasattr(seller, "portfolio") and firm_id in seller.portfolio.holdings:
                        stock_market.update_shareholder(seller.id, firm_id, seller.portfolio.holdings[firm_id].quantity)
                    else:
                        stock_market.update_shareholder(seller.id, firm_id, 0.0)

                self.world_state.logger.info(
                    f"STOCK_TX | Buyer: {buyer.id}, Seller: {seller.id}, Firm: {firm_id}, Qty: {tx.quantity}, Price: {tx.price}",
                    extra={"tick": time, "tags": ["stock_market", "transaction"]}
                )
