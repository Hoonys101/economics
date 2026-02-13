from typing import List, Tuple, TYPE_CHECKING
import logging
from simulation.dtos import AgentStateData, TransactionData, EconomicIndicatorData, MarketHistoryData
from simulation.core_agents import Household
from simulation.firms import Firm
from modules.system.api import DEFAULT_CURRENCY

if TYPE_CHECKING:
    from simulation.world_state import WorldState
    from simulation.models import Transaction

logger = logging.getLogger(__name__)

class AnalyticsSystem:
    """
    Service responsible for gathering and aggregating simulation data for persistence.
    TD-272: Decouples aggregation logic from PersistenceManager.
    """

    def __init__(self):
        pass

    def aggregate_tick_data(self, world_state: "WorldState") -> Tuple[List[AgentStateData], List[TransactionData], EconomicIndicatorData, List[MarketHistoryData]]:
        """
        Aggregates data from the world state into DTOs for persistence.
        """
        run_id = world_state.run_id
        time = world_state.time

        # 1. Agent States
        agent_states: List[AgentStateData] = []

        # We iterate over world_state.agents instead of simulation.agents (which is same)
        for agent in world_state.agents.values():
            if not getattr(agent, "is_active", False):
                continue

            # Base DTO construction
            # Use getattr for safety, though BaseAgent should have these
            assets = agent.get_assets_by_currency() if hasattr(agent, 'get_assets_by_currency') else {DEFAULT_CURRENCY: 0.0}

            agent_dto = AgentStateData(
                run_id=run_id,
                time=time,
                agent_id=agent.id,
                agent_type="",
                assets=assets,
                is_active=agent.is_active,
                generation=getattr(agent, "generation", 0),
            )

            if isinstance(agent, Household):
                agent_dto.agent_type = "household"
                # Phase 9.1 Refactor: Use snapshot DTO for safe observation
                snapshot = agent.create_snapshot_dto()
                
                # SnapshotDTO uses full names: econ_state, bio_state
                agent_dto.is_employed = snapshot.econ_state.is_employed
                agent_dto.employer_id = snapshot.econ_state.employer_id

                # Needs
                agent_dto.needs_survival = snapshot.bio_state.needs.get("survival", 0)
                agent_dto.needs_labor = snapshot.bio_state.needs.get("labor_need", 0)

                # Inventory (Using public protocol)
                agent_dto.inventory_food = agent.get_quantity("food")

                # Time Allocation - world_state.household_time_allocation should also come from DTO if possible
                # For now keeping it as it's a world state property, but checking if it's in snapshot
                time_leisure = world_state.household_time_allocation.get(agent.id, 0.0)

                # Config access via snapshot/agent
                shopping_hours = getattr(agent.config, "SHOPPING_HOURS", 2.0)
                hours_per_tick = getattr(agent.config, "HOURS_PER_TICK", 24.0)

                agent_dto.time_leisure = time_leisure
                agent_dto.time_worked = max(0.0, hours_per_tick - time_leisure - shopping_hours)

            elif isinstance(agent, Firm):
                agent_dto.agent_type = "firm"
                # Phase 9.1 Refactor: Use state DTO for safe observation
                state_dto = agent.get_state_dto()
                
                agent_dto.inventory_food = agent.get_quantity("food")
                agent_dto.current_production = state_dto.production.current_production
                agent_dto.num_employees = len(state_dto.hr.employees)
                
                # Metadata extraction
                agent_dto.generation = getattr(state_dto, "generation", 0)

            else:
                # Other agents (Bank, Gov, etc)
                agent_dto.agent_type = agent.__class__.__name__.lower()

            agent_states.append(agent_dto)

        # 2. Transactions
        transaction_dtos: List[TransactionData] = []
        for tx in world_state.transactions:
            if tx.buyer_id is None or tx.seller_id is None:
                logger.error(
                    f"ANALYTICS_SKIP | Skipping transaction with NULL ID. "
                    f"Buyer: {tx.buyer_id}, Seller: {tx.seller_id}, Item: {tx.item_id}",
                    extra={"tick": time, "tags": ["analytics", "skip"]}
                )
                continue

            tx_dto = TransactionData(
                run_id=run_id,
                time=time,
                buyer_id=tx.buyer_id,
                seller_id=tx.seller_id,
                item_id=tx.item_id,
                quantity=tx.quantity,
                price=tx.price,
                currency=getattr(tx, 'currency', DEFAULT_CURRENCY),
                market_id=tx.market_id,
                transaction_type=tx.transaction_type,
            )
            transaction_dtos.append(tx_dto)

        # 3. Economic Indicators
        indicator_dto = None
        if world_state.tracker:
            tracker_indicators = world_state.tracker.get_latest_indicators()

            # Recalculate some aggregates if needed or rely on tracker.
            # PersistenceManager logic:
            # Recalculate some aggregates via snapshots
            total_labor_income = 0.0
            total_capital_income = 0.0
            
            for h in world_state.households:
                # Access via snapshot for purity
                if hasattr(h, 'create_snapshot_dto'):
                    snap = h.create_snapshot_dto()
                    total_labor_income += snap.econ_state.labor_income_this_tick_pennies / 100.0
                    total_capital_income += snap.econ_state.capital_income_this_tick_pennies / 100.0

            # Flatten assets for DB
            hh_assets = tracker_indicators.get("total_household_assets", 0.0)
            firm_assets = tracker_indicators.get("total_firm_assets", 0.0)

            hh_assets_val = hh_assets.get(DEFAULT_CURRENCY, 0.0) if isinstance(hh_assets, dict) else float(hh_assets)
            firm_assets_val = firm_assets.get(DEFAULT_CURRENCY, 0.0) if isinstance(firm_assets, dict) else float(firm_assets)

            indicator_dto = EconomicIndicatorData(
                run_id=run_id,
                time=time,
                unemployment_rate=tracker_indicators.get("unemployment_rate"),
                avg_wage=tracker_indicators.get("avg_wage"),
                food_avg_price=tracker_indicators.get("food_avg_price"),
                food_trade_volume=tracker_indicators.get("food_trade_volume"),
                avg_goods_price=tracker_indicators.get("avg_goods_price"),
                total_production=tracker_indicators.get("total_production", 0.0),
                total_consumption=tracker_indicators.get("total_consumption", 0.0),
                total_household_assets=hh_assets_val,
                total_firm_assets=firm_assets_val,
                avg_survival_need=tracker_indicators.get("avg_survival_need", 0.0),
                total_labor_income=total_labor_income,
                total_capital_income=total_capital_income,
            )

        # 4. Market History (Placeholder - if implemented elsewhere, we can aggregate here)
        market_history: List[MarketHistoryData] = []
        # Logic to gather market stats if needed
        # For now return empty list as per PersistenceManager state

        return agent_states, transaction_dtos, indicator_dto, market_history
