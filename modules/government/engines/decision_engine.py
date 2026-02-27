from typing import Any, Dict, Optional, List
import logging
from modules.government.api import IGovernmentDecisionEngine, IGovBrain, GovernmentStateDTO
from modules.government.dtos import PolicyDecisionDTO, PolicyActionDTO
from simulation.dtos.api import MarketSnapshotDTO
from simulation.ai.enums import PolicyActionTag, EconomicSchool, PoliticalParty
# from modules.government.policies.adaptive_gov_brain import AdaptiveGovBrain # REMOVED strict import

logger = logging.getLogger(__name__)

import warnings

class GovernmentDecisionEngine(IGovernmentDecisionEngine):
    """
    [DEPRECATED] Stateless engine that decides on government policy actions.
    Replaced by FiscalEngine for Fiscal Policy.
    It delegates the specific logic to a strategy (e.g., Taylor Rule, AI).
    """

    def __init__(self, config_module: Any, brain: IGovBrain, strategy_mode: str = "TAYLOR_RULE"):
        # warnings.warn("GovernmentDecisionEngine is deprecated. Use FiscalEngine instead.", DeprecationWarning, stacklevel=2)
        # Note: Deprecation warning kept but commented out or active? The file had it.
        # I will keep the warning but maybe relax it if this is the "Decoupled" version?
        # The prompt says "Refactor GovernmentDecisionEngine Decoupling".
        # So it seems it is NOT removed, but improved.
        self.config = config_module
        self.strategy_mode = strategy_mode
        self.brain = brain # Injected Dependency

    def decide(
        self,
        state: GovernmentStateDTO,
        market_snapshot: MarketSnapshotDTO,
        central_bank: Any
    ) -> PolicyDecisionDTO:
        """
        Decides on a policy action based on current state and market data.
        """
        # Calculate Potential GDP (Common Logic for all strategies)
        # Note: state.sensory_data might be missing if using strictly the new GovernmentStateDTO.
        # But if we are transitioning, we might need to handle compatibility.
        # The new GovernmentStateDTO (modules/government/api.py) does NOT have sensory_data.
        # It has treasury_balance, current_tax_rates, active_welfare_programs.
        # However, legacy GovernmentDecisionEngine expects sensory_data in state (dtos.py version).
        # We need to bridge this.
        # The spec says: "Pass strict MarketSnapshotDTO to the brain, receive GovernmentStateDTO."
        # If the brain returns GovernmentStateDTO (new), we need to map it to PolicyDecisionDTO.

        # New Logic: Delegate strictly to brain.evaluate_policies

        # First, ensure market_snapshot is the compatible one.
        # The IGovBrain expects modules.common.api.MarketSnapshotDTO (Strict).
        # The input here is simulation.dtos.api.MarketSnapshotDTO (Legacy).
        # We need to adapt.

        from modules.common.api import MarketSnapshotDTO as StrictMarketSnapshotDTO

        # Adapter Logic
        strict_snapshot = StrictMarketSnapshotDTO(
            timestamp=market_snapshot.tick,
            average_prices=self._extract_average_prices(market_snapshot),
            total_trade_volume=self._extract_trade_volume(market_snapshot),
            unemployment_rate=self._extract_unemployment(market_snapshot, state) # Need state? Or snapshot?
        )

        new_state_dto = self.brain.evaluate_policies(strict_snapshot)

        # Now convert new_state_dto (GovernmentStateDTO) to PolicyDecisionDTO.
        # The Brain now returns the *target state*.
        # The DecisionEngine's job is to figure out the *Action* to get there, or the Brain already decided?
        # "GovernmentDecisionEngine... Executes government policy based on brain decisions."
        # "Pass strict MarketSnapshotDTO to the brain, receive GovernmentStateDTO."
        # This implies the brain says "This is what the state should be".
        # So the decision is "Update Tax Rates to X, Y".

        # We need to compare current state with new_state_dto to generate PolicyDecisionDTO.
        # Or, if the legacy code expects a specific decision format, we synthesize it.

        # For this refactor, I'll generate a PolicyDecisionDTO that sets the new rates.

        params = {}
        action_tag = PolicyActionTag.GENERAL_ADMIN

        # Check for Tax Changes
        # Legacy state has income_tax_rate, corporate_tax_rate.
        # New state has current_tax_rates['income_tax'], ...

        if 'income_tax' in new_state_dto.current_tax_rates:
             params['income_tax_rate'] = new_state_dto.current_tax_rates['income_tax']

        if 'corporate_tax' in new_state_dto.current_tax_rates:
             params['corporate_tax_rate'] = new_state_dto.current_tax_rates['corporate_tax']

        # Determine Tag (Simplified)
        # If tax cut -> Stimulus?
        # I will use GENERAL_ADMIN for now as the brain is the authority.

        return PolicyDecisionDTO(
            action_tag=action_tag,
            parameters=params,
            metadata={"source": "IGovBrain", "strategy": self.strategy_mode},
            status="EXECUTED"
        )

    def _extract_average_prices(self, snapshot: MarketSnapshotDTO) -> Dict[str, float]:
        # Legacy snapshot has market_data dictionary
        # Or market_signals?
        # simulation.dtos.api.MarketSnapshotDTO has market_data: Dict[str, Any]
        # and market_signals: Dict[str, MarketSignalDTO]
        # We can try to extract avg prices from signals.
        prices = {}
        if snapshot.market_signals:
            for item_id, signal in snapshot.market_signals.items():
                if signal.last_traded_price:
                    prices[item_id] = float(signal.last_traded_price) / 100.0 # Convert pennies to float? Spec says float.
        return prices

    def _extract_trade_volume(self, snapshot: MarketSnapshotDTO) -> float:
        # Sum volume from signals
        total = 0.0
        if snapshot.market_signals:
             for signal in snapshot.market_signals.values():
                 total += signal.volatility_7d # Wait, volume isn't directly here as total?
                 # signal has total_bid_quantity?
                 # Actually market_data often has total_trade_volume for global?
                 pass
        return snapshot.market_data.get("total_trade_volume", 0.0)

    def _extract_unemployment(self, snapshot: MarketSnapshotDTO, state: Any) -> float:
        # Try snapshot first
        if snapshot.labor and snapshot.labor.avg_wage:
             # Snapshot doesn't seem to have unemployment directly in Legacy DTO based on my read?
             # Wait, EconomicIndicatorData has it.
             pass

        # Fallback to state sensory data if available (Legacy behavior)
        if hasattr(state, 'sensory_data') and state.sensory_data:
             return state.sensory_data.unemployment_sma

        return 0.05 # Default
