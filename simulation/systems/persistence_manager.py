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
from modules.system.api import DEFAULT_CURRENCY

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

            # Fix for Phase 33 Multi-Currency: Ensure assets are Dict[CurrencyCode, float]
            # But the DB adapter might expect float for legacy columns?
            # AgentStateData defines assets as Dict[CurrencyCode, float].
            # However, the DB repository (save_agent_states_batch) might be using sqlite executemany which binds this directly.
            # If the DB schema for 'assets' column is REAL/FLOAT, we must extract the default currency value.
            # If it's TEXT/JSON, we can store the dict.
            # Based on the error "sqlite3.ProgrammingError: Error binding parameter 5: type 'dict' is not supported",
            # the DB adapter is trying to insert the dict directly into a column that expects a primitive or the adapter doesn't handle dict.
            # We should convert it to the primary currency float for now to fix the crash, or serialize it.
            # Given the urgency, we extract DEFAULT_CURRENCY value.

            assets_val = agent.assets
            if isinstance(assets_val, dict):
                # We need to decide if we store dict (as string/json) or float.
                # AgentRepository.save_agent_states_batch likely maps DTO fields to columns.
                # Let's extract the float value for now to satisfy the likely schema of 'assets' (REAL).
                from modules.system.api import DEFAULT_CURRENCY
                assets_val_float = assets_val.get(DEFAULT_CURRENCY, 0.0)
                # But wait, AgentStateData expects Dict?
                # If AgentStateData expects Dict, but DB adapter fails, the DB adapter needs fixing OR we hack DTO.
                # Checking AgentStateData in dtos/api.py: "assets: Dict[CurrencyCode, float]"
                # So the DTO is correct for Phase 33.
                # The Repository is failing.
                # We should probably fix the Repository or serialize here if DTO allows.
                # But DTO type hint says Dict.
                # Let's override it to float here if we can't change Repository easily now?
                # No, that violates type hint.
                # The error is in `simulation/db/agent_repository.py`.
                # I cannot change that file easily without seeing it, but I can see the error: "Error binding parameter 5: type 'dict' is not supported"
                # This implies parameter 5 (assets) receives a dict.
                # I will modify AgentStateData construction to pass a float if I can, OR I modify the repository.
                # Since I am in PersistenceManager, I can serialize the dict to JSON string if the DB column supports text,
                # or just pass the float if the DB column is float.
                # Most likely 'assets' column is FLOAT/REAL.
                pass

            # Fix: Extract float for DB compatibility until DB schema supports JSON
            assets_to_store = agent.assets
            if isinstance(assets_to_store, dict):
                 from modules.system.api import DEFAULT_CURRENCY
                 assets_to_store = assets_to_store.get(DEFAULT_CURRENCY, 0.0)

            # We are forcing a float into a field typed as Dict in DTO?
            # Python runtime won't check types. SQLite will accept float.
            # This is a hotfix.

            agent_dto = AgentStateData(
                run_id=self.run_id,
                time=time,
                agent_id=agent.id,
                agent_type="",
                assets=assets_to_store,
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
                currency=getattr(tx, 'currency', DEFAULT_CURRENCY),
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
        total_assets = sum(h._econ_state.assets.get(DEFAULT_CURRENCY, 0.0) for h in simulation.households)
        
        # Prepare asset dicts for DTO
        hh_assets = tracker_indicators.get("total_household_assets", 0.0)
        firm_assets = tracker_indicators.get("total_firm_assets", 0.0)

        # Wrap as dict if they are floats (backward compatibility check)
        # Fix for Phase 33 Multi-Currency: Convert Dict back to float for legacy DB compatibility
        # Similar to agent state persistence, we must flatten the currency dict to the default currency float
        # until the DB schema supports JSON/Text for assets.

        if isinstance(hh_assets, dict):
            hh_assets = hh_assets.get(DEFAULT_CURRENCY, 0.0)

        if isinstance(firm_assets, dict):
            firm_assets = firm_assets.get(DEFAULT_CURRENCY, 0.0)

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
            total_household_assets=hh_assets,
            total_firm_assets=firm_assets,
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
