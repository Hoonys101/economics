from _typeshed import Incomplete
from dataclasses import asdict as asdict
from modules.market.housing_planner_api import HousingDecisionDTO as HousingPurchaseDecisionDTO
from simulation.core_agents import Household as Household
from simulation.engine import Simulation as Simulation
from simulation.models import Order as Order
from typing import Any
from uuid import UUID as UUID

logger: Incomplete

class HousingSystem:
    """
    Phase 22.5: Housing Market System
    Handles rent collection, maintenance, mortgages, foreclosures, and transactions.
    Refactored for strict protocol enforcement (Wave 1.1).
    """
    config: Incomplete
    pending_sagas: list[dict[str, Any]]
    def __init__(self, config_module: Any) -> None: ...
    def process_housing(self, simulation: Simulation):
        """
        Processes mortgage payments, maintenance costs, rent collection, and eviction/foreclosure checks.
        Consolidated from Simulation._process_housing (Line 1221 in engine.py).
        Also flushes queued housing transactions to SettlementSystem.
        """
    def initiate_purchase(self, decision: HousingPurchaseDecisionDTO, buyer_id: int):
        """
        Starts a new housing transaction saga.
        Called by DecisionUnit (or via orchestration).
        """
    def apply_homeless_penalty(self, simulation: Simulation):
        """
        Applies survival penalties to homeless agents.
        """
