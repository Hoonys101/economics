from __future__ import annotations
from typing import Protocol, Any, Dict, runtime_checkable
from simulation.dtos.api import MockFactoryDTO

@runtime_checkable
class IMockFactory(Protocol):
    """Module D: Protocol for decoupled mock generation."""
    def create_mock(self, dto: MockFactoryDTO) -> Any:
        """Generates a mock object based on the factory DTO."""
        ...

    def verify_expectations(self) -> bool:
        """Verifies that all expectations set on the factory's mocks were met."""
        ...

@runtime_checkable
class ITestAssertion(Protocol):
    """Module D: Protocol for standardized economic assertions."""
    def assert_integer_precision(self, value: Any) -> None:
        """Enforces that a value adheres to the Penny Standard (integer)."""
        ...
