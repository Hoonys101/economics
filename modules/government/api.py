from __future__ import annotations
from typing import Protocol
from modules.government.dtos import (
    FiscalPolicyDTO,
    MonetaryPolicyDTO,
    GovernmentStateDTO
)
from simulation.dtos.api import MarketSnapshotDTO

class IFiscalPolicyManager(Protocol):
    """Interface for managing the government's fiscal policy."""

    def determine_fiscal_stance(self, market_snapshot: "MarketSnapshotDTO") -> FiscalPolicyDTO:
        """Adjusts tax brackets based on economic conditions."""
        ...

    def calculate_tax_liability(self, policy: FiscalPolicyDTO, income: float) -> float:
        """Calculates the tax owed based on a progressive bracket system."""
        ...

class IMonetaryPolicyManager(Protocol):
    """Interface for managing the government's monetary policy (Central Bank)."""

    def determine_monetary_stance(self, market_snapshot: "MarketSnapshotDTO") -> MonetaryPolicyDTO:
        """Adjusts the target interest rate based on a Taylor-like rule."""
        ...

class Government(Protocol):
    """Facade for the government agent."""
    state: GovernmentStateDTO

    def make_policy_decision(self, market_snapshot: "MarketSnapshotDTO") -> None:
        ...
