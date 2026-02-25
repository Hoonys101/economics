from __future__ import annotations
from typing import List, Optional, TYPE_CHECKING, Any, Dict
import logging

from simulation.dtos.api import SimulationState, GovernmentSensoryDTO
from simulation.orchestration.phases import (
    Phase0_PreSequence, Phase_Production, Phase1_Decision, Phase2_Matching,
    Phase3_Transaction, Phase_Bankruptcy, Phase_HousingSaga, Phase_Consumption, Phase5_PostSequence,
    Phase_BankAndDebt, Phase_FirmProductionAndSalaries, Phase_GovernmentPrograms, Phase_TaxationIntents
)
from simulation.orchestration.phases.system_commands import Phase_SystemCommands
from simulation.orchestration.phases.politics import Phase_Politics
from simulation.orchestration.utils import prepare_market_data
from simulation.orchestration.phases_recovery import Phase_SystemicLiquidation
from simulation.orchestration.phases.scenario_analysis import Phase_ScenarioAnalysis
from simulation.orchestration.phases.metrics import Phase0_PreTickMetrics, Phase6_PostTickMetrics
from simulation.orchestration.phases.god_commands import Phase_GodCommands
from modules.system.api import DEFAULT_CURRENCY
from modules.government.politics_system import PoliticsSystem
from modules.system.command_pipeline.api import CommandBatchDTO

if TYPE_CHECKING:
    from simulation.world_state import WorldState
    from simulation.action_processor import ActionProcessor
    from simulation.orchestration.api import IPhaseStrategy
    from modules.system.command_pipeline.api import ICommandIngressService
    from modules.system.services.command_service import CommandService

logger = logging.getLogger(__name__)

class TickOrchestrator:
    def __init__(self, world_state: WorldState, action_processor: ActionProcessor,
                 command_ingress: ICommandIngressService, command_service: CommandService):
        self.world_state = world_state
        self.action_processor = action_processor
        self.command_ingress = command_ingress
        self.command_service = command_service

        # Initialize Politics System (Phase 4.4)
        config_src = getattr(world_state, 'config_manager', getattr(world_state, 'config_module', None))
        self.politics_system = PoliticsSystem(config_src)
        world_state.politics_system = self.politics_system

        # Initialize phases with dependencies
        self.phases: List[IPhaseStrategy] = [
            Phase0_PreTickMetrics(world_state), # STABILIZE_COCKPIT: Extracted Metrics
            Phase0_PreSequence(world_state),
            Phase_GodCommands(world_state, command_service), # STABILIZE_COCKPIT: God Commands
            Phase_SystemCommands(world_state), # TD-255: Cockpit Interventions
            Phase_Production(world_state),
            Phase1_Decision(world_state),
            Phase_Bankruptcy(world_state),
            Phase_HousingSaga(world_state),
            Phase_SystemicLiquidation(world_state),
            Phase_Politics(world_state),
            Phase2_Matching(world_state),

            # --- Decomposed Phase 3 ---
            Phase_BankAndDebt(world_state),
            Phase_FirmProductionAndSalaries(world_state),
            Phase_GovernmentPrograms(world_state),
            Phase_TaxationIntents(world_state),
            Phase3_Transaction(world_state),

            Phase_Consumption(world_state),
            Phase5_PostSequence(world_state),
            Phase6_PostTickMetrics(world_state), # STABILIZE_COCKPIT: Extracted Metrics
            Phase_ScenarioAnalysis(world_state)
        ]

    def run_tick(self, injectable_sensory_dto: Optional[GovernmentSensoryDTO] = None) -> None:
        state = self.world_state

        # Increment time
        state.time += 1
        state.logger.info(
            f"--- Starting Tick {state.time} ---",
            extra={"tick": state.time, "tags": ["tick_start"]},
        )

        # TD-177: Ensure flow counters are reset at the start of the tick
        if state.government and hasattr(state.government, "reset_tick_flow"):
            state.government.reset_tick_flow()

        # LIFECYCLE FIX: Process Inter-Tick Queue
        if state.inter_tick_queue:
            count = len(state.inter_tick_queue)
            state.logger.info(f"LIFECYCLE_QUEUE | Promoting {count} transactions from inter-tick queue.")
            state.transactions.extend(state.inter_tick_queue)
            state.inter_tick_queue.clear()

        # 1. Ingest Commands from Unified Pipeline
        command_batch = self.command_ingress.drain_for_tick(state.time)

        # 2. Create the comprehensive state DTO for this tick
        sim_state = self._create_simulation_state_dto(injectable_sensory_dto, command_batch)

        # 3. Execute all phases in sequence
        for phase in self.phases:
            sim_state = phase.execute(sim_state)
            self._drain_and_sync_state(sim_state)

        # 4. Final persistence and cleanup
        self._finalize_tick(sim_state)

        state.logger.info(
            f"--- Ending Tick {state.time} ---",
            extra={"tick": state.time, "tags": ["tick_end"]},
        )

    def _create_simulation_state_dto(self, injectable_sensory_dto: Optional[GovernmentSensoryDTO],
                                     command_batch: Optional[CommandBatchDTO] = None) -> SimulationState:
        state = self.world_state

        return SimulationState(
            time=state.time,
            households=state.households,
            firms=state.firms,
            agents=state.agents,
            markets=state.markets,
            primary_government=state.government,
            bank=state.bank,
            central_bank=state.central_bank,
            escrow_agent=getattr(state, "escrow_agent", None),
            stock_market=getattr(state, "stock_market", None),
            stock_tracker=getattr(state, "stock_tracker", None),
            goods_data=state.goods_data,
            market_data={},
            config_module=state.config_module,
            tracker=state.tracker,
            logger=state.logger,
            ai_training_manager=state.ai_training_manager,
            ai_trainer=state.ai_trainer,
            settlement_system=state.settlement_system,
            taxation_system=state.taxation_system,
            currency_holders=state.currency_holders,
            next_agent_id=state.next_agent_id,
            real_estate_units=state.real_estate_units,
            injectable_sensory_dto=injectable_sensory_dto,
            inactive_agents=state.inactive_agents,
            stress_scenario_config=state.stress_scenario_config,
            transaction_processor=getattr(state, "transaction_processor", None),
            saga_orchestrator=state.saga_orchestrator,
            monetary_ledger=state.monetary_ledger,
            shareholder_registry=state.shareholder_registry,
            command_batch=command_batch, # STABILIZE_COCKPIT: Unified Batch
            housing_service=getattr(state, "housing_service", None),
            registry=getattr(state, "registry", None),
            effects_queue=[],
            inter_tick_queue=[],
            transactions=[],
            currency_registry_handler=state,
            politics_system=self.politics_system
        )

    def _drain_and_sync_state(self, sim_state: SimulationState):
        ws = self.world_state
        ws.next_agent_id = sim_state.next_agent_id

        if sim_state.effects_queue:
            ws.effects_queue.extend(sim_state.effects_queue)
            sim_state.effects_queue.clear()

        if sim_state.inter_tick_queue:
            ws.inter_tick_queue.extend(sim_state.inter_tick_queue)
            sim_state.inter_tick_queue.clear()

        if sim_state.transactions:
            ws.transactions.extend(sim_state.transactions)
            sim_state.transactions.clear()

        if ws.agents is not sim_state.agents:
            raise RuntimeError("CRITICAL: 'agents' collection was re-assigned in a phase. Use in-place modification.")

        ws.inactive_agents.update(sim_state.inactive_agents)

    def _finalize_tick(self, sim_state: SimulationState):
        state = self.world_state

        # TD-160: Clear world_state transactions to prevent memory leak
        state.transactions.clear()

        # LIFECYCLE_PULSE: Reset tick-level counters
        if state.lifecycle_manager and hasattr(state.lifecycle_manager, "reset_agents_tick_state"):
            state.lifecycle_manager.reset_agents_tick_state(state)

        # Note: M2 Check and Panic Index moved to Phase6_PostTickMetrics

    def prepare_market_data(self) -> Dict[str, Any]:
        """
        Legacy/External access to market data preparation.
        """
        sim_state = self._create_simulation_state_dto(None, None)
        return prepare_market_data(sim_state)
