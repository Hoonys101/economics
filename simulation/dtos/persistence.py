from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

from modules.household.dtos import HouseholdSnapshotDTO
from modules.firm.api import FirmSnapshotDTO

@dataclass
class HouseholdPersistenceDTO:
    """
    Persistence wrapper for Household agents.
    Includes the immutable Snapshot DTO plus any transient state not captured by it
    but required for full "Warm-Start" restoration.
    """
    snapshot: HouseholdSnapshotDTO

    # Transient / Internal State extensions
    distress_tick_counter: int = 0
    credit_frozen_until_tick: int = 0

@dataclass
class FirmPersistenceDTO:
    """
    Persistence wrapper for Firm agents.
    """
    snapshot: FirmSnapshotDTO

    # Transient / Internal State extensions
    credit_frozen_until_tick: int = 0
    market_insight: float = 0.5 # Missing from FirmSnapshotDTO
    sales_volume_this_tick: float = 0.0 # Missing from FirmSnapshotDTO
