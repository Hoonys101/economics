from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Protocol, Optional, Dict, Any
from simulation.models import Order
from simulation.dtos import DecisionContext

@dataclass
class FinancialPlanDTO:
    orders: List[Order] = field(default_factory=list)

@dataclass
class HRPlanDTO:
    orders: List[Order] = field(default_factory=list)

@dataclass
class OperationsPlanDTO:
    orders: List[Order] = field(default_factory=list)

@dataclass
class SalesPlanDTO:
    orders: List[Order] = field(default_factory=list)

class FinanceManagerProtocol(Protocol):
    def formulate_plan(self, context: DecisionContext, dividend_aggressiveness: float, debt_aggressiveness: float) -> FinancialPlanDTO:
        ...

class HRManagerProtocol(Protocol):
    def formulate_plan(self, context: DecisionContext, hiring_aggressiveness: float) -> HRPlanDTO:
        ...

class OperationsManagerProtocol(Protocol):
    def formulate_plan(self, context: DecisionContext, capital_aggressiveness: float, rd_aggressiveness: float, guidance: Dict[str, Any]) -> OperationsPlanDTO:
        ...

class SalesManagerProtocol(Protocol):
    def formulate_plan(self, context: DecisionContext, sales_aggressiveness: float) -> SalesPlanDTO:
        ...
