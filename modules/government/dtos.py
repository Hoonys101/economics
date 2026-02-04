from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from simulation.ai.enums import PolicyActionTag

@dataclass
class TaxHistoryItemDTO:
    tick: int
    total: float
    tax_revenue: Dict[str, float]

@dataclass
class TaxBracketDTO:
    """Defines a single progressive tax bracket."""
    floor: float
    rate: float
    ceiling: Optional[float] # None for the highest bracket

@dataclass
class FiscalPolicyDTO:
    """State of the current fiscal policy."""
    progressive_tax_brackets: List[TaxBracketDTO]
    # TBD: Other fiscal tools like subsidies, welfare

@dataclass
class MonetaryPolicyDTO:
    """State of the current monetary policy."""
    target_interest_rate: float
    inflation_target: float
    unemployment_target: float
    # TBD: QE/QT parameters

@dataclass
class GovernmentStateDTO:
    """The complete state of the Government agent."""
    id: int
    assets: float
    fiscal_policy: FiscalPolicyDTO
    monetary_policy: MonetaryPolicyDTO

@dataclass
class MacroEconomicSnapshotDTO:
    """Snapshot of macro-economic indicators for Monetary Policy."""
    inflation_rate: float
    nominal_gdp: float
    potential_gdp: float
    unemployment_rate: float

@dataclass
class PolicyActionDTO:
    """Represents a proposed government policy action."""
    name: str
    utility: float
    tag: PolicyActionTag
    action_type: str
    params: Dict[str, Any] = field(default_factory=dict)
