"""
API Definition for Mock Drift Automation & Protocol Governance.
This module defines the interfaces for creating strictly compliant mocks
and tracking violations where mocks diverge from their defined Protocols.
"""
from __future__ import annotations
from typing import Protocol, Type, Any, TypeVar, List, Optional, runtime_checkable, Dict
from dataclasses import dataclass
from unittest.mock import MagicMock

# Generic Type for Protocols
T = TypeVar("T")

@dataclass
class MockViolationDTO:
    """
    Data Transfer Object representing a detected deviation between a Mock and its Protocol.
    Used for generating the 'Mock Drift' report.
    """
    protocol_name: str
    attribute_name: str
    violation_type: str  # e.g., "UNDEFINED_ATTRIBUTE", "SIGNATURE_MISMATCH"
    location: str        # Test file or function name
    severity: str        # "ERROR" (Fail test) or "WARNING" (Log only)

@runtime_checkable
class IProtocolInspector(Protocol):
    """
    Service interface for analyzing Protocol classes to extract their full contract,
    handling inheritance and MRO (Method Resolution Order) correctly.
    """
    def get_protocol_members(self, protocol_cls: Type[Any]) -> List[str]:
        """
        Returns a list of all public attributes and methods defined in the Protocol,
        including those inherited from parent Protocols.
        """
        ...

    def validate_signature(self, protocol_cls: Type[Any], method_name: str, mock_method: Any) -> bool:
        """
        Checks if the mock's method signature is compatible with the Protocol's definition.
        """
        ...

@runtime_checkable
class IMockFactory(Protocol):
    """
    Centralized factory interface for creating strict mocks.
    Replaces direct `MagicMock()` instantiation in tests.
    """
    def create_mock(self, protocol: Type[T], strict: bool = True, name: Optional[str] = None) -> T:
        """
        Creates a mock object typed as T.

        Args:
            protocol: The Protocol class to mock.
            strict: If True, uses `spec_set` to forbid creating unknown attributes.
            name: Optional name for debugging.

        Returns:
            A MagicMock instance that strictly adheres to T.
        """
        ...

    def create_autospec(self, target: Any, **kwargs) -> Any:
        """
        Wrapper around unittest.mock.create_autospec with additional Protocol awareness.
        """
        ...

@runtime_checkable
class IMockRegistry(Protocol):
    """
    Registry to track mock usage and enforce policies across the test suite.
    """
    def register_violation(self, violation: MockViolationDTO) -> None:
        """Records a violation."""
        ...

    def get_violations(self) -> List[MockViolationDTO]:
        """Retrieves all recorded violations for reporting."""
        ...
