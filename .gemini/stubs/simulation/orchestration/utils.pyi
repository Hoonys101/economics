from simulation.core_agents import Household as Household
from simulation.dtos.api import SimulationState as SimulationState
from simulation.firms import Firm as Firm
from simulation.markets.order_book_market import OrderBookMarket as OrderBookMarket
from typing import Any

def prepare_market_data(state: SimulationState) -> dict[str, Any]:
    """Prepares market data for agent decisions."""
