from __future__ import annotations
from typing import TypeVar, Generic, Protocol, runtime_checkable, List, Dict, Optional
from dataclasses import dataclass

T_External = TypeVar('T_External')
T_Kernel = TypeVar('T_Kernel')

# ==========================================
# 1. External DTOs (Pure Data, No Core Imports)
# ==========================================

@dataclass(frozen=True)
class PublicFirmDTO:
    """External representation of a Firm. No core dependencies."""
    firm_id: str
    capital: float
    inventory_count: int

@dataclass(frozen=True)
class PublicHouseholdDTO:
    """External representation of a Household. No core dependencies."""
    household_id: str
    wealth: float

@dataclass(frozen=True)
class PublicEconomicIndicatorsDTO:
    """External representation of economic health."""
    gdp: float
    cpi: float
    unemployment_rate: float

# ==========================================
# 2. Public API Protocols
# ==========================================

@runtime_checkable
class FirmServiceProtocol(Protocol):
    """Public interface for firm operations. Uses ONLY External DTOs."""
    
    def get_firm_status(self, firm_id: str) -> PublicFirmDTO:
        ...
        
    def process_transaction(self, firm_id: str, amount: float) -> bool:
        ...

@runtime_checkable
class HouseholdServiceProtocol(Protocol):
    """Public interface for household operations."""
    
    def get_household_status(self, household_id: str) -> PublicHouseholdDTO:
        ...

# ==========================================
# 3. Mapper / Adapter Interfaces
# ==========================================

@runtime_checkable
class DTOMapperProtocol(Protocol, Generic[T_External, T_Kernel]):
    """Strict bidirectional mapping protocol to isolate External and Kernel layers."""
    
    def to_external(self, kernel_obj: T_Kernel) -> T_External:
        """Converts internal Kernel object to safe External DTO."""
        ...
        
    def to_kernel(self, external_dto: T_External) -> T_Kernel:
        """Converts External DTO to internal Kernel object (if applicable)."""
        ...
