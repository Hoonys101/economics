from __future__ import annotations
from typing import List, Optional, TYPE_CHECKING, Any, Dict
import logging

from simulation.dtos.api import SimulationState, GovernmentSensoryDTO
from simulation.orchestration.phases import (
    Phase0_PreSequence, Phase_Production, Phase1_Decision, Phase2_Matching,
    Phase3_Transaction, Phase_Bankruptcy, Phase_HousingSaga, Phase_Consumption, Phase5_PostSequence,
    Phase_BankAndDebt, Phase_FirmProductionAndSalaries, Phase_GovernmentPrograms, Phase_TaxationIntents
)
from simulation.orchestration.phases.intercept import Phase0_Intercept
from simulation.orchestration.phases.system_commands import Phase_SystemCommands
from simulation.orchestration.phases.politics import Phase_Politics
from simulation.orchestration.utils import prepare_market_data
from simulation.orchestration.phases_recovery import Phase_SystemicLiquidation
from simulation.orchestration.phases.scenario_analysis import Phase_ScenarioAnalysis
from modules.system.api import DEFAULT_CURRENCY
from modules.government.politics_system import PoliticsSystem

if TYPE_CHECKING:
    from simulation.world_state import WorldState
    from simulation.action_processor import ActionProcessor
    from simulation.orchestration.api import IPhaseStrategy

logger = logging.getLogger(__name__)

class TickOrchestrator:
    def __init__(self, world_state: WorldState, action_processor: ActionProcessor):
        self.world_state = world_state
        self.action_processor = action_processor

        # Initialize Politics System (Phase 4.4)
        # Robust access for tests that might only provide config_module
        config_src = getattr(world_state, 'config_manager', getattr(world_state, 'config_module', None))
        self.politics_system = PoliticsSystem(config_src)
        world_state.politics_system = self.politics_system

        # Initialize phases with dependencies
        self.phases: List[IPhaseStrategy] = [
            Phase0_Intercept(world_state), # FOUND-03: Phase 0 Intercept
            Phase0_PreSequence(world_state),
            Phase_SystemCommands(world_state), # TD-255: Cockpit Interventions
            Phase_Production(world_state),
            Phase1_Decision(world_state),
            Phase_Bankruptcy(world_state),           # Phase 4 (Spec): Lifecycle & Bankruptcy
            Phase_HousingSaga(world_state),          # Phase 4.1: Advance Housing Sagas
            Phase_SystemicLiquidation(world_state),  # Phase 4.5 (Spec): Systemic Liquidation
            Phase_Politics(world_state),             # Phase 4.4 (Spec): Political Orchestrator
            Phase2_Matching(world_state),            # Phase 5 (Spec): Matching

            # --- Decomposed Phase 3 ---
            Phase_BankAndDebt(world_state),
            Phase_FirmProductionAndSalaries(world_state),
            Phase_GovernmentPrograms(world_state),
            Phase_TaxationIntents(world_state),
            Phase3_Transaction(world_state),         # Transaction Processing & Cleanup

            Phase_Consumption(world_state),          # Late Lifecycle (Consumption Finalization)
            Phase5_PostSequence(world_state),
            Phase_ScenarioAnalysis(world_state)      # Phase 8: Telemetry & Verification (DATA-03)
        ]

    def run_tick(self, injectable_sensory_dto: Optional[GovernmentSensoryDTO] = None) -> None:
        state = self.world_state

        # Money Supply Verification (Tick 0)
        # This check is usually done before any activity starts
        if state.time == 0:
            # Ensure currency_holders is correct before baseline calculation
            # TD-030: Removed _rebuild_currency_holders. Initializer populates this.
            # self._rebuild_currency_holders(state)
            total_money = state.calculate_total_money()
            if isinstance(total_money, dict):
                state.baseline_money_supply = total_money.get(DEFAULT_CURRENCY, 0.0)
            else:
                state.baseline_money_supply = float(total_money)

            state.logger.info(
                f"MONEY_SUPPLY_BASELINE | Baseline Money Supply set to: {state.baseline_money_supply:.2f}",
                extra={"tick": state.time, "money_supply": state.baseline_money_supply}
            )

        # Increment time
        state.time += 1
        state.logger.info(
            f"--- Starting Tick {state.time} ---",
            extra={"tick": state.time, "tags": ["tick_start"]},
        )

        # TD-177: Ensure flow counters are reset at the start of the tick
        if state.government and hasattr(state.government, "reset_tick_flow"):
            state.government.reset_tick_flow()

        # LIFECYCLE FIX: Process Inter-Tick Queue (Lifecycle events from previous tick)
        if state.inter_tick_queue:
            count = len(state.inter_tick_queue)
            state.logger.info(f"LIFECYCLE_QUEUE | Promoting {count} transactions from inter-tick queue.")
            state.transactions.extend(state.inter_tick_queue)
            state.inter_tick_queue.clear()

        # 1. Create the comprehensive state DTO for this tick
        sim_state = self._create_simulation_state_dto(injectable_sensory_dto)

        # 2. Execute all phases in sequence
        for phase in self.phases:
            sim_state = phase.execute(sim_state)
            # TD-192: Immediately drain and sync state back to WorldState
            self._drain_and_sync_state(sim_state)

        # 4. Final persistence and cleanup
        self._finalize_tick(sim_state)

        state.logger.info(
            f"--- Ending Tick {state.time} ---",
            extra={"tick": state.time, "tags": ["tick_end"]},
        )

    def _create_simulation_state_dto(self, injectable_sensory_dto: Optional[GovernmentSensoryDTO]) -> SimulationState:
        state = self.world_state

        # Drain command queue
        commands_for_tick = list(state.system_commands)
        state.system_commands.clear()

        # drain god_command_queue atomically using popleft
        god_commands_for_tick = []
        while state.god_command_queue:
            god_commands_for_tick.append(state.god_command_queue.popleft())

        # PRODUCTION INTEGRATION: Drain external CommandQueue
        if state.command_queue:
            while not state.command_queue.empty():
                try:
                    # Using get_nowait to avoid blocking the engine
                    cmd = state.command_queue.get_nowait()
                    god_commands_for_tick.append(cmd)
                except Exception:
                    break

        # Ensure injectable_sensory_dto has valid current_gdp if provided
        # This is passed to government as sensory_data, which is then used by FinanceSystem
        # to calculate debt-to-GDP ratio via FiscalMonitor.
        # FiscalMonitor expects 'gdp' attribute, but GovernmentStateDTO has 'current_gdp'.
        # We need to bridge this gap either here or in FinanceSystem.
        # Since FiscalMonitor is shared, better to adapt the input in FinanceSystem.
        # However, we can also ensure current_gdp is populated here for clarity.

        return SimulationState(
            time=state.time,
            households=state.households,
            firms=state.firms,
            agents=state.agents,
            markets=state.markets,
            primary_government=state.government, # Renamed to primary_government
            governments=[state.government] if state.government else [], # TD-ARCH-GOV-MISMATCH: Populate list
            bank=state.bank,
            central_bank=state.central_bank,
            escrow_agent=getattr(state, "escrow_agent", None),
            stock_market=state.stock_market,
            stock_tracker=state.stock_tracker,
            goods_data=state.goods_data,
            market_data={}, # Will be populated in Phase 1 (and 0 for Gov)
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
            stress_scenario_config=state.stress_scenario_config, # Phase 28
            transaction_processor=getattr(state, "transaction_processor", None), # Added for compatibility
            saga_orchestrator=state.saga_orchestrator, # TD-253
            monetary_ledger=state.monetary_ledger,     # TD-253
            shareholder_registry=state.shareholder_registry, # TD-275
            system_commands=commands_for_tick, # TD-255
            god_command_snapshot=god_commands_for_tick, # Renamed to god_command_snapshot
            housing_service=getattr(state, "housing_service", None), # Phase 4.1 Fix
            registry=getattr(state, "registry", None),
            effects_queue=[], # TD-192: Init empty
            inter_tick_queue=[], # TD-192: Init empty
            transactions=[], # TD-192: Init empty
            currency_registry_handler=state, # Inject WorldState to handle strict registry updates
            politics_system=self.politics_system
        )

    def _drain_and_sync_state(self, sim_state: SimulationState):
        """
        Drains transient queues from SimulationState into WorldState and syncs scalars.
        This ensures changes from a phase are immediately persisted before the next phase runs.
        """
        ws = self.world_state

        # --- Sync Scalars ---
        ws.next_agent_id = sim_state.next_agent_id

        # --- Drain Transient Queues ---
        # The core of the solution: move items from the DTO's queue to the WorldState's
        # master queue for the tick, then clear the DTO's queue so it's fresh for the next phase.

        if sim_state.effects_queue:
            ws.effects_queue.extend(sim_state.effects_queue)
            sim_state.effects_queue.clear() # Prevent double-processing

        if sim_state.inter_tick_queue:
            ws.inter_tick_queue.extend(sim_state.inter_tick_queue)
            sim_state.inter_tick_queue.clear() # Prevent double-processing

        if sim_state.transactions:
            # TD-177: Structural Guarantee for M2 Integrity
            # Note: Monetary transactions are now processed in Phase_MonetaryProcessing.
            # However, for transactions generated in other phases, we might miss them if not careful.
            # BUT, Phase_MonetaryProcessing runs before Phase3_Transaction (processor).
            # If transactions are added late (e.g. in Phase3), they might not be counted in M2 Delta for *this* tick's logic
            # if that logic runs earlier. But M2 stats are usually calculated at end of tick or start of next.
            # The removal here is intentional as per WO-4.2B to align orchestrator.

            ws.transactions.extend(sim_state.transactions)
            sim_state.transactions.clear() # Prevent double-processing

        # --- Sync mutable collections by reference (ensure no re-assignment) ---
        # This acts as a safety check. If a phase violates the rule, this will raise an error.
        if ws.agents is not sim_state.agents:
            raise RuntimeError("CRITICAL: 'agents' collection was re-assigned in a phase. Use in-place modification.")

        # Update the inactive agents dictionary
        ws.inactive_agents.update(sim_state.inactive_agents)

    def _finalize_tick(self, sim_state: SimulationState):
        state = self.world_state

        # TD-160: Clear world_state transactions to prevent memory leak and double-processing
        # Persistence has already happened in Phase 5.
        state.transactions.clear()

        # LIFECYCLE_PULSE: Reset tick-level counters for all agents
        if state.lifecycle_manager and hasattr(state.lifecycle_manager, "reset_agents_tick_state"):
            state.lifecycle_manager.reset_agents_tick_state(state)

        # Money Supply Verification (Post-Tick) & M2 Leak Calculation
        m2_leak_delta = 0.0
        if state.time >= 1:
            # WO-220: Repair Currency Holders Sync
            # Rebuilds state.currency_holders from state.agents to ensure M2 integrity.
            # TD-030: Removed _rebuild_currency_holders to enforce StrictCurrencyRegistry.
            # LifecycleManager is now responsible for maintaining this list incrementally.
            # self._rebuild_currency_holders(state)

            total_hh = sum(h.get_assets_by_currency().get(DEFAULT_CURRENCY, 0.0) for h in state.households)
            total_firm = sum(f.get_assets_by_currency().get(DEFAULT_CURRENCY, 0.0) for f in state.firms)
            gov_assets = state.government.get_assets_by_currency().get(DEFAULT_CURRENCY, 0.0)
            cb_assets = state.central_bank.get_assets_by_currency().get(DEFAULT_CURRENCY, 0.0) if state.central_bank else 0.0
            bank_assets = state.bank.get_assets_by_currency().get(DEFAULT_CURRENCY, 0.0) if state.bank else 0.0

            state.logger.debug(f"M2_BREAKDOWN | HH: {total_hh:.2f}, Firms: {total_firm:.2f}, Gov: {gov_assets:.2f}, CB: {cb_assets:.2f}, Bank: {bank_assets:.2f}")

            current_money = state.calculate_total_money().get(DEFAULT_CURRENCY, 0.0)
            expected_money = state.baseline_money_supply
            if hasattr(state.government, "get_monetary_delta"):
                expected_money += state.government.get_monetary_delta(DEFAULT_CURRENCY)

            m2_leak_delta = current_money - expected_money

            msg = f"MONEY_SUPPLY_CHECK | Current: {current_money:.2f}, Expected: {expected_money:.2f}, Delta: {m2_leak_delta:.4f}"
            extra_data = {"tick": state.time, "current": current_money, "expected": expected_money, "delta": m2_leak_delta, "tags": ["money_supply"]}

            # Tight Tolerance: 0.1% to detect leaks early (Wave 5 Hardening)
            tolerance = max(10.0, expected_money * 0.001) # Min 0.10 USD
            if abs(m2_leak_delta) > tolerance:
                 state.logger.warning(msg, extra=extra_data)
            else:
                 state.logger.info(msg, extra=extra_data)

            # Update baseline for next tick to accumulate authorized changes
            # This ensures 'Expected' follows the authorized expansion path
            if hasattr(state.government, "get_monetary_delta"):
                authorized_delta = state.government.get_monetary_delta(DEFAULT_CURRENCY)
                state.baseline_money_supply += authorized_delta

            # Track Economics
            if state.tracker:
                # Calculate Monetary Base (M0) for tracking
                m0_dict = state.calculate_base_money()
                m0_pennies = m0_dict.get(DEFAULT_CURRENCY, 0)

                state.tracker.track(
                    time=state.time,
                    households=state.households,
                    firms=state.firms,
                    markets=state.markets,
                    money_supply=current_money,
                    m2_leak=m2_leak_delta,
                    monetary_base=float(m0_pennies)
                )

        # Phase 4.1: Market Panic Index Calculation (Architect Directive)
        total_deposits = 0
        if state.bank and hasattr(state.bank, "get_total_deposits_pennies"):
            total_deposits = state.bank.get_total_deposits_pennies()
        else:
            # Fallback: sum of all household and firm assets
            total_hh = sum(h.get_assets_by_currency().get(DEFAULT_CURRENCY, 0) for h in state.households)
            total_firm = sum(f.get_assets_by_currency().get(DEFAULT_CURRENCY, 0) for f in state.firms)
            total_deposits = int(total_hh + total_firm)

        try:
            is_positive_deposits = float(total_deposits) > 0
        except (TypeError, ValueError):
            is_positive_deposits = False

        if is_positive_deposits:
            try:
                # Handle MagicMock which returns Mock for attribute access
                raw_withdrawals = getattr(state, 'tick_withdrawal_pennies', 0)
                tick_withdrawals = float(raw_withdrawals)
                panic_index = tick_withdrawals / total_deposits
                state.market_panic_index = min(1.0, float(panic_index))
            except (TypeError, ValueError):
                state.market_panic_index = 0.0
        else:
            state.market_panic_index = 0.0

        state.logger.info(
            f"MARKET_PANIC_INDEX | Index: {state.market_panic_index:.4f}, Withdrawals: {getattr(state, 'tick_withdrawal_pennies', 0)}",
            extra={"tick": state.time, "panic_index": state.market_panic_index}
        )
        
        # Reset withdrawal counter for next tick
        if hasattr(state, 'tick_withdrawal_pennies'):
            state.tick_withdrawal_pennies = 0

    def prepare_market_data(self) -> Dict[str, Any]:
        """
        Legacy/External access to market data preparation.
        Delegates to the logic used in Phase 1.

        Used by: Simulation._prepare_market_data
        """
        # Create a proper SimulationState DTO to satisfy type requirements
        # passing None for injectable_sensory_dto as it's not needed for this legacy call
        sim_state = self._create_simulation_state_dto(None)
        return prepare_market_data(sim_state)
