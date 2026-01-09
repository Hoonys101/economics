from typing import List, override
import logging

from simulation.markets.order_book_market import OrderBookMarket
from simulation.models import Order, Transaction

logger = logging.getLogger(__name__)

class HousingMarket(OrderBookMarket):
    """
    Subclass of OrderBookMarket specifically for Real Estate transactions.

    This class explicitly allows orders where the buyer might not have sufficient assets
    at the time of order placement (insolvent orders), because funding (mortgage)
    is arranged atomically at transaction time.

    While the base OrderBookMarket currently doesn't check solvency on placement,
    this subclass solidifies the intent and protects against future base class changes.
    """

    def __init__(self, market_id: str = "real_estate", logger: logging.Logger = None):
        super().__init__(market_id=market_id, logger=logger)

    @override
    def place_order(self, order: Order, current_time: int):
        """
        Overrides place_order to explicitly allow orders without pre-check of assets.
        In base class, there is no check, but we document this behavior here.
        """
        # Just call super, but conceptually we are acknowledging "unsafe" placement
        # pending mortgage approval at match time.
        super().place_order(order, current_time)
