from typing import Protocol, runtime_checkable

@runtime_checkable
class IFinancialEntity(Protocol):
    id: int

@runtime_checkable
class IEmployeeDataProvider(IFinancialEntity, Protocol):
    labor_skill: float

class BaseAgent(IFinancialEntity):
    def __init__(self, id: int):
        self.id = id

class Household(BaseAgent, IEmployeeDataProvider):
    def __init__(self, id: int):
        super().__init__(id)
        self.labor_skill = 1.0

h = Household(1)
print(f"Household {h.id} created with skill {h.labor_skill}")
print(f"Is instance of IFinancialEntity: {isinstance(h, IFinancialEntity)}")
print(f"Is instance of IEmployeeDataProvider: {isinstance(h, IEmployeeDataProvider)}")
