from __future__ import annotations
from collections import Counter, defaultdict
from typing import List, Dict, Any, Optional

from modules.government.political.api import (
    IPoliticalOrchestrator,
    VoteRecordDTO,
    LobbyingEffortDTO,
    PoliticalClimateDTO
)
from modules.system.constants import ID_PUBLIC_MANAGER, ID_GOVERNMENT

class PoliticalOrchestrator(IPoliticalOrchestrator):
    """
    Manages the political lifecycle: Voting, Lobbying, and Mandate calculation.
    """

    def __init__(self):
        self._vote_buffer: List[VoteRecordDTO] = []
        self._lobbying_buffer: List[LobbyingEffortDTO] = []

    def register_vote(self, vote: VoteRecordDTO) -> None:
        """
        Ingests a single vote from a household.
        Should be called during the 'Political Phase' of the tick.
        """
        self._vote_buffer.append(vote)

    def register_lobbying(self, effort: LobbyingEffortDTO) -> None:
        """
        Ingests a verified lobbying effort.
        """
        self._lobbying_buffer.append(effort)

    def calculate_political_climate(self, current_tick: int) -> PoliticalClimateDTO:
        """
        Aggregates all registered votes and lobbying efforts to produce a
        snapshot of the political climate (Approval, Pressures).
        """
        total_weight = 0.0
        weighted_approval_sum = 0.0

        # weighted grievance counts
        weighted_grievance_counts: Dict[str, float] = defaultdict(float)

        # 1. Process Votes
        for vote in self._vote_buffer:
            weight = vote.political_weight
            if not isinstance(weight, (int, float)):
                weight = 1.0 # Defensive fallback for tests/mocks

            total_weight += weight
            weighted_approval_sum += (vote.approval_value * weight)
            if vote.primary_grievance and vote.primary_grievance != "NONE":
                weighted_grievance_counts[vote.primary_grievance] += weight

        overall_approval = weighted_approval_sum / total_weight if total_weight > 0 else 0.5

        # Sort grievances by weighted count
        sorted_grievances = sorted(weighted_grievance_counts.items(), key=lambda item: item[1], reverse=True)
        top_grievances = [g[0] for g in sorted_grievances[:5]]

        # 2. Process Lobbying
        pressure_map: Dict[str, float] = defaultdict(float)
        for lobby in self._lobbying_buffer:
            # Pressure = Money * Direction
            pressure = lobby.investment_pennies * lobby.desired_shift
            pressure_map[lobby.target_policy] += pressure

        return PoliticalClimateDTO(
            tick=current_tick,
            overall_approval_rating=overall_approval,
            party_support_breakdown={}, # Placeholder for V2
            top_grievances=top_grievances,
            lobbying_pressure=dict(pressure_map)
        )

    def reset_cycle(self) -> None:
        """Clears votes and lobbying efforts for the next accumulation cycle."""
        self._vote_buffer.clear()
        self._lobbying_buffer.clear()

    def validate_transfer_targets(self, payer_id: Any, payee_id: Any) -> bool:
        """
        Validates the participants of a political transfer (e.g. Lobbying).
        Ensures the payee is a valid government entity (ID_PUBLIC_MANAGER or ID_GOVERNMENT).
        """
        valid_payees = [ID_PUBLIC_MANAGER, ID_GOVERNMENT, "GOVERNMENT_TREASURY"]

        if payee_id not in valid_payees:
            # Check if it matches ID_PUBLIC_MANAGER int/str
            try:
                if int(payee_id) in [ID_PUBLIC_MANAGER, ID_GOVERNMENT]:
                    return True
            except (ValueError, TypeError):
                pass
            return False
        return True
