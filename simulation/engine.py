from __future__ import annotations
from typing import List, Dict, Any, Optional, TYPE_CHECKING
import logging

from modules.common.config_manager.api import ConfigManager
from simulation.db.repository import SimulationRepository
from simulation.dtos import GovernmentSensoryDTO
from simulation.metrics.economic_tracker import EconomicIndicatorTracker
from simulation.systems.tech.api import FirmTechInfoDTO, HouseholdEducationDTO

from simulation.world_state import WorldState
from simulation.orchestration.tick_orchestrator import TickOrchestrator
from modules.system.services.command_service import CommandService
from simulation.action_processor import ActionProcessor
from simulation.models import Transaction
from modules.simulation.api import EconomicIndicatorsDTO, SystemStateDTO
from modules.system.api import DEFAULT_CURRENCY, IGlobalRegistry, IAgentRegistry
from simulation.finance.api import ISettlementSystem

from simulation.db.logger import SimulationLogger
import simulation

logger = logging.getLogger(__name__)


class Simulation:
    """경제 시뮬레이션의 전체 흐름을 관리하고 조정하는 핵심 엔진 클래스. (Facade)"""

    def __init__(
        self,
        config_manager: ConfigManager,
        config_module: Any,
        logger: logging.Logger,
        repository: SimulationRepository,
        registry: IGlobalRegistry,
        settlement_system: ISettlementSystem,
        agent_registry: IAgentRegistry
    ) -> None:
        """
        초기화된 구성 요소들을 할당받습니다.
        실제 생성 로직은 SimulationInitializer에 의해 외부에서 수행됩니다.
        """
        self.world_state = WorldState(
            config_manager=config_manager,
            config_module=config_module,
            logger=logger,
            repository=repository
        )

        # Inject dependencies into WorldState
        self.world_state.global_registry = registry
        # SettlementSystem and AgentRegistry are typically accessed via Simulation or injected into components

        self.settlement_system = settlement_system
        self.world_state.settlement_system = settlement_system
        self.agent_registry = agent_registry

        self.action_processor = ActionProcessor(self.world_state)
        self.tick_orchestrator = TickOrchestrator(self.world_state, self.action_processor)

        # Initialize Command Service and Controls
        self.command_service = CommandService(registry, settlement_system, agent_registry)
        self.is_paused = False
        self.step_requested = False

        # Initialize SimulationLogger
        db_path = self.world_state.config_manager.get("simulation.database_name", "simulation_data.db")
        self.simulation_logger = SimulationLogger(db_path)
        self.simulation_logger.run_id = self.world_state.run_id
        # Expose via global module attribute for access by agents
        simulation.logger = self.simulation_logger

    def __getattr__(self, name: str) -> Any:
        return getattr(self.world_state, name)

    def __setattr__(self, name: str, value: Any) -> None:
        # Avoid infinite recursion for internal components
        if name in ["world_state", "tick_orchestrator", "action_processor", "simulation_logger", "command_service", "is_paused", "step_requested", "settlement_system", "agent_registry"]:
            super().__setattr__(name, value)
            return

        # Delegate to world_state if it has the attribute or if we are setting it dynamically
        if hasattr(self, "world_state"):
             setattr(self.world_state, name, value)
        else:
             super().__setattr__(name, value)

    def finalize_simulation(self):
        """시뮬레이션 종료 시 Repository 연결을 닫고, 시뮬레이션 종료 시간을 기록합니다."""
        if self.world_state.persistence_manager:
            self.world_state.persistence_manager.flush_buffers(self.world_state.time)
        
        self.world_state.repository.runs.update_simulation_run_end_time(self.world_state.run_id)
        self.world_state.repository.close()
        self.simulation_logger.close()
        self.world_state.logger.info("Simulation finalized and Repository connection closed.")

        # Release application-level lock if exists
        if hasattr(self, "_lock_file") and self._lock_file:
            try:
                self._lock_file.close() # Closing the file releases the lock
                self.world_state.logger.info("Released simulation.lock")
            except Exception as e:
                self.world_state.logger.error(f"Failed to release simulation.lock: {e}")

    def _process_commands(self) -> None:
        """Processes all pending commands from the world state command queue."""
        # Drain the thread-safe queue
        commands = []
        if self.world_state.command_queue:
            while not self.world_state.command_queue.empty():
                try:
                    commands.append(self.world_state.command_queue.get_nowait())
                except Exception:
                    break

        god_commands = []
        for cmd in commands:
            # Polymorphic handling (Legacy CockpitCommand vs New GodCommandDTO)
            c_type = getattr(cmd, "command_type", getattr(cmd, "type", None))

            # Handle System Control Commands locally
            if c_type == "PAUSE":
                self.is_paused = True
                logger.info("System PAUSED via command.")
            elif c_type == "RESUME":
                self.is_paused = False
                logger.info("System RESUMED via command.")
            elif c_type == "PAUSE_STATE":
                # New DTO style: new_value determines state
                val = getattr(cmd, "new_value", True)
                self.is_paused = bool(val)
                logger.info(f"System Pause State set to {self.is_paused}")
            elif c_type == "STEP":
                self.step_requested = True
                logger.info("Step requested.")
            elif c_type == "TRIGGER_EVENT" and getattr(cmd, "parameter_key", "") == "STEP":
                 self.step_requested = True
                 logger.info("Step requested via TRIGGER_EVENT.")
            else:
                # Forward God Commands (SET_PARAM, INJECT_*, etc.) to TickOrchestrator
                god_commands.append(cmd)

        # Forward God Commands to TickOrchestrator via WorldState
        if god_commands:
            self.world_state.god_command_queue.extend(god_commands)
            logger.debug(f"Forwarded {len(god_commands)} commands to TickOrchestrator.")

    def run_tick(self, injectable_sensory_dto: Optional[GovernmentSensoryDTO] = None) -> None:
        self._process_commands()

        if self.is_paused:
            if self.step_requested:
                self.step_requested = False
            else:
                return

        self.tick_orchestrator.run_tick(injectable_sensory_dto)
        
        # Log macro snapshot for ThoughtStream analysis
        snapshot = self.get_economic_indicators()
        system_state = self.get_system_state()
        self.simulation_logger.log_snapshot(
            tick=self.world_state.time,
            snapshot_data={
                "gdp": snapshot.gdp,
                "m2": self.world_state.calculate_total_money(),
                "cpi": snapshot.cpi,
                "transaction_count": len(self.world_state.transactions)
            }
        )
        
        # DIRECTIVE ALPHA OPTIMIZER: Conditional Flush
        if self.world_state.time % self.batch_save_interval == 0:
            self.simulation_logger.flush()

    def get_all_agents(self) -> List[Any]:
        """시뮬레이션에 참여하는 모든 활성 에이전트(가계, 기업, 은행 등)를 반환합니다."""
        return self.world_state.get_all_agents()

    def get_economic_indicators(self) -> EconomicIndicatorsDTO:
        """
        Retrieves the current market snapshot containing economic indicators.
        Exposes a public interface for observers (satisfies ISimulationState).
        Formerly get_market_snapshot.
        """
        # Retrieve raw data from orchestrator
        market_data = self.tick_orchestrator.prepare_market_data()

        # Calculate CPI (Average Price Level)
        total_price = 0.0
        count = 0
        goods_market = market_data.get("goods_market", {})

        for key, value in goods_market.items():
            if key.endswith("_current_sell_price") and isinstance(value, (int, float)) and value > 0:
                total_price += value
                count += 1

        cpi = total_price / count if count > 0 else 0.0

        # Construct and return formal DTO
        return EconomicIndicatorsDTO(
            gdp=market_data.get("total_production", 0.0),
            cpi=cpi
        )

    def get_system_state(self) -> SystemStateDTO:
        """
        Retrieves internal system state for phenomena analysis.
        Implements ISimulationState.get_system_state.
        """
        bank_reserves = 0.0
        bank_deposits = 0.0

        # Access Bank via world_state
        if self.world_state.bank:
            if hasattr(self.world_state.bank, "get_balance"):
                bank_reserves = self.world_state.bank.get_balance(DEFAULT_CURRENCY)
            else:
                bank_reserves = getattr(self.world_state.bank, "assets", 0.0)
            # Bank deposits are stored in 'deposits' dict
            if hasattr(self.world_state.bank, "deposits"):
                bank_deposits = sum(d.amount for d in self.world_state.bank.deposits.values())

        last_fiscal_tick = -1
        if self.world_state.government:
            last_fiscal_tick = getattr(self.world_state.government, "last_fiscal_activation_tick", -1)

        circuit_breaker = False
        if self.world_state.stock_market:
            # Placeholder until StockMarket implements explicit circuit breaker state
            circuit_breaker = getattr(self.world_state.stock_market, "is_circuit_breaker_active", False)

        base_rate = 0.05
        if self.world_state.central_bank:
            base_rate = getattr(self.world_state.central_bank, "base_rate", 0.05)

        return SystemStateDTO(
            is_circuit_breaker_active=circuit_breaker,
            bank_total_reserves=bank_reserves,
            bank_total_deposits=bank_deposits,
            fiscal_policy_last_activation_tick=last_fiscal_tick,
            central_bank_base_rate=base_rate
        )

    # --- Backward Compatibility Methods ---

    def _prepare_market_data(self, tracker: EconomicIndicatorTracker) -> Dict[str, Any]:
        """Legacy wrapper for TickOrchestrator.prepare_market_data"""
        # Note: Tracker argument is ignored as orchestrator uses internal state
        return self.tick_orchestrator.prepare_market_data()

    def _calculate_total_money(self) -> float:
        """Legacy wrapper for WorldState.calculate_total_money"""
        return self.world_state.calculate_total_money()

    def _process_transactions(self, transactions: List[Transaction]) -> None:
        """Legacy wrapper for ActionProcessor.process_transactions"""
        # We need to reconstruct the callback.
        # Note: self.tracker comes from world_state via __getattr__
        market_data_cb = lambda: self._prepare_market_data(self.tracker).get("goods_market", {})
        self.action_processor.process_transactions(transactions, market_data_cb)

    def _process_stock_transactions(self, transactions: List[Transaction]) -> None:
        """Legacy wrapper for ActionProcessor.process_stock_transactions"""
        self.action_processor.process_stock_transactions(transactions)
