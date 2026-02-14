from typing import List

from modules.household.api import ICrisisEngine, PanicSellingInputDTO, PanicSellingResultDTO
from simulation.models import Order

class CrisisEngine(ICrisisEngine):
    """
    Stateless engine for handling household crisis situations (e.g. panic selling).
    """

    def evaluate_distress(self, input_dto: PanicSellingInputDTO) -> PanicSellingResultDTO:
        orders: List[Order] = []

        # Panic Sell Stocks
        # Iterate over portfolio holdings
        for firm_id, share in input_dto.portfolio_holdings.items():
            # Check quantity safely
            quantity = getattr(share, 'quantity', 0.0)

            if quantity > 0:
                stock_order = Order(
                    agent_id=input_dto.owner_id,
                    side="SELL",
                    item_id=f"stock_{firm_id}",
                    quantity=quantity,
                    price_limit=0.0, # Market sell
                    market_id="stock_market"
                )
                orders.append(stock_order)

        # Panic Sell Inventory (Placeholder for future logic as per original code)
        for item_id, qty in input_dto.inventory.items():
            if qty > 0:
                # Currently no mechanism to sell back consumer goods effectively
                pass

        return PanicSellingResultDTO(orders=orders)
