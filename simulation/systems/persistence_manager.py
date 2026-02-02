from __future__ import annotations
import logging
from typing import TYPE_CHECKING, List, Dict, Any
from simulation.dtos import (
    AgentStateData,
    TransactionData,
    EconomicIndicatorData,
    MarketHistoryData,
)
from simulation.core_agents import Household
from simulation.firms import Firm

if TYPE_CHECKING:
    from simulation.engine import Simulation
    from simulation.models import Transaction

logger = logging.getLogger(__name__)

class PersistenceManager:
    """
    Phase 22.5: Persistence Manager System
    Handles DB state buffering, calculation of aggregate indicators for persistence, 
    and batch flushing to simulation repository.
    """

    def __init__(self, run_id: int, config_module: Any, repository: Any):
        self.run_id = run_id
        self.config = config_module
        self.repository = repository
        
        # Internal Buffers
        self.agent_state_buffer: List[AgentStateData] = []
        self.transaction_buffer: List[TransactionData] = []
        self.economic_indicator_buffer: List[EconomicIndicatorData] = []
        self.market_history_buffer: List[MarketHistoryData] = []

    def buffer_tick_state(self, simulation: "Simulation", transactions: List["Transaction"]):
        """
        Gathers and buffers agent states, transactions, and aggregate indicators for the current tick.
        """
        time = simulation.time
        
        # 1. Buffer agent states
        for agent in simulation.agents.values():
            if not getattr(agent, "is_active", False):
                continue

            agent_dto = AgentStateData(
                run_id=self.run_id,
                time=time,
                agent_id=agent.id,
                agent_type="",
                assets=agent.assets,
                is_active=agent.is_active,
                generation=getattr(agent, "generation", 0),
            )

            if isinstance(agent, Household):
                agent_dto.agent_type = "household"
                agent_dto.is_employed = agent.is_employed
                agent_dto.employer_id = agent.employer_id
                agent_dto.needs_survival = agent.needs.get("survival", 0)
                agent_dto.needs_labor = agent.needs.get("labor_need", 0)
                agent_dto.inventory_food = agent.inventory.get("food", 0)

                # Time Allocation Tracking
                time_leisure = simulation.household_time_allocation.get(agent.id, 0.0)
                shopping_hours = getattr(self.config, "SHOPPING_HOURS", 2.0)
                hours_per_tick = getattr(self.config, "HOURS_PER_TICK", 24.0)

                agent_dto.time_leisure = time_leisure
                agent_dto.time_worked = max(0.0, hours_per_tick - time_leisure - shopping_hours)

            elif isinstance(agent, Firm):
                agent_dto.agent_type = "firm"
                agent_dto.inventory_food = agent.inventory.get("food", 0)
                agent_dto.current_production = agent.current_production
                agent_dto.num_employees = len(agent.hr.employees)
            else:
                continue

            self.agent_state_buffer.append(agent_dto)

        # 2. Buffer transactions
        for tx in transactions:
            tx_dto = TransactionData(
                run_id=self.run_id,
                time=time,
                buyer_id=tx.buyer_id,
                seller_id=tx.seller_id,
                item_id=tx.item_id,
                quantity=tx.quantity,
                price=tx.price,
                market_id=tx.market_id,
                transaction_type=tx.transaction_type,
            )
            self.transaction_buffer.append(tx_dto)

        # 3. Buffer aggregate indicators
        tracker_indicators = simulation.tracker.get_latest_indicators()
        
        # Income Aggregation (Phase 14-1)
        total_labor_income = sum(getattr(h, "labor_income_this_tick", 0.0) for h in simulation.households)
        total_capital_income = sum(getattr(h, "capital_income_this_tick", 0.0) for h in simulation.households)

        # Calculate Wealth Distribution (Snapshot)
        total_assets = sum(h._econ_state.assets for h in simulation.households)
        
        indicator_dto = EconomicIndicatorData(
            run_id=self.run_id,
            time=time,
            unemployment_rate=tracker_indicators.get("unemployment_rate"),
            avg_wage=tracker_indicators.get("avg_wage"),
            food_avg_price=tracker_indicators.get("food_avg_price"),
            food_trade_volume=tracker_indicators.get("food_trade_volume"),
            avg_goods_price=tracker_indicators.get("avg_goods_price"),
            total_production=tracker_indicators.get("total_production", 0.0),
            total_consumption=tracker_indicators.get("total_consumption", 0.0),
            total_household_assets=tracker_indicators.get("total_household_assets", 0.0),
            total_firm_assets=tracker_indicators.get("total_firm_assets", 0.0),
            avg_survival_need=tracker_indicators.get("avg_survival_need", 0.0),
            total_labor_income=total_labor_income,
            total_capital_income=total_capital_income,
        )
        self.economic_indicator_buffer.append(indicator_dto)

    def flush_buffers(self, current_tick: int):
        """
        Periodically flushes buffered states to the database repository.
        """
        if not (self.agent_state_buffer or self.transaction_buffer or 
                self.economic_indicator_buffer or self.market_history_buffer):
            return

        logger.info(
            f"DB_FLUSH_START | Flushing buffers to DB at tick {current_tick}",
            extra={"tick": current_tick, "tags": ["db_flush"]}
        )

        if self.agent_state_buffer:
            self.repository.agents.save_agent_states_batch(self.agent_state_buffer)
            self.agent_state_buffer.clear()

        if self.transaction_buffer:
            self.repository.markets.save_transactions_batch(self.transaction_buffer)
            self.transaction_buffer.clear()

        if self.economic_indicator_buffer:
            self.repository.analytics.save_economic_indicators_batch(self.economic_indicator_buffer)
            self.economic_indicator_buffer.clear()

        if self.market_history_buffer:
            self.repository.markets.save_market_history_batch(self.market_history_buffer)
            self.market_history_buffer.clear()

        logger.info(
            f"DB_FLUSH_END | Finished flushing buffers to DB at tick {current_tick}",
            extra={"tick": current_tick, "tags": ["db_flush"]}
        )
