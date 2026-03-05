# ROLE: Tier 1 (Universal)
# CRITICALITY: CRITICAL (HARD)
# GUIDELINE: HARD CONSTRAINT. Mandatory core contract.
# ==========================================
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Protocol, runtime_checkable
from dataclasses import dataclass, field

@dataclass(frozen=True)
class HouseholdAnalyticsDTO:
    """Read-only snapshot of a household's state for analytics purposes."""
    agent_id: int
    is_active: bool
    total_cash_pennies: int
    portfolio_value_pennies: int
    is_employed: bool
    trust_score: float
    survival_need: float
    consumption_expenditure_pennies: int
    food_expenditure_pennies: int
    labor_income_pennies: int
    education_level: float
    aptitude: float

@dataclass(frozen=True)
class FirmAnalyticsDTO:
    """Read-only snapshot of a firm's state for analytics purposes."""
    agent_id: int
    is_active: bool
    total_assets_pennies: int
    cash_balance_pennies: int
    current_production: float
    inventory_volume: float
    sales_volume: float

@dataclass(frozen=True)
class MarketAnalyticsDTO:
    """Read-only snapshot of market activity for analytics purposes."""
    market_id: str
    avg_price: float
    volume: float
    current_price: float

@dataclass(frozen=True)
class EconomyAnalyticsSnapshotDTO:
    """Aggregated, pure-data snapshot of the entire economy for a specific tick."""
    tick: int
    households: List[HouseholdAnalyticsDTO]
    firms: List[FirmAnalyticsDTO]
    markets: List[MarketAnalyticsDTO]
    money_supply_pennies: int
    m2_leak_pennies: int
    monetary_base_pennies: int

@runtime_checkable
class IAnalyticsTracker(Protocol):
    """Protocol for economic tracking and analytics generation."""

    def track_tick(self, snapshot: EconomyAnalyticsSnapshotDTO) -> None:
        """Processes a tick snapshot and updates internal timeseries metrics."""
        ...

    def get_latest_indicators(self) -> Dict[str, float]:
        """Retrieves the most recently calculated macro indicators."""
        ...

    def get_smoothed_values(self) -> Dict[str, float]:
        """Retrieves Simple Moving Averages for key metrics."""
        ...

@runtime_checkable
class IAnalyticsDAO(Protocol):
    """Protocol for persisting analytics time-series data to storage."""

    def save_tick_metrics(self, tick: int, metrics: Dict[str, float]) -> bool:
        """Persists the computed metrics for a given tick."""
        ...

    def fetch_historical_metrics(self, metric_name: str, since_tick: int) -> List[float]:
        """Retrieves historical values for a specific metric."""
        ...
