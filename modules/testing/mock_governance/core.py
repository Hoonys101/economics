"""
Core implementation of Mock Drift Automation & Protocol Governance.
"""
import inspect
from typing import Type, Any, List, Optional, Set, Protocol
from unittest.mock import MagicMock, create_autospec
from .api import IProtocolInspector, IMockFactory, IMockRegistry, MockViolationDTO, T

class ProtocolInspector(IProtocolInspector):
    """
    Analyzes Protocol classes to extract their full contract.
    """
    def get_protocol_members(self, protocol_cls: Type[Any]) -> List[str]:
        members: Set[str] = set()

        # Traverse MRO to handle inheritance
        for cls in inspect.getmro(protocol_cls):
            # Skip non-Protocol base classes like 'object', 'Generic', or implementation details
            # Standard typing.Protocol classes have _is_protocol=True
            # Note: getattr(cls, '_is_protocol', False) works for standard Protocols.
            if not getattr(cls, '_is_protocol', False):
                continue

            # Skip the 'Protocol' class itself if it appears in MRO (it has _is_protocol=True)
            if cls is Protocol:
                continue

            # Add typed attributes from __annotations__
            if hasattr(cls, "__annotations__"):
                for name in cls.__annotations__.keys():
                    if not name.startswith("_"):
                        members.add(name)

            # Add methods and properties from __dict__
            for name, val in cls.__dict__.items():
                if name.startswith("_"):
                    continue

                # Check if it's a method, property, or callable
                # We include anything that is public and defined on the protocol
                members.add(name)

        return list(members)

    def validate_signature(self, protocol_cls: Type[Any], method_name: str, mock_method: Any) -> bool:
        # Placeholder for signature validation
        # In a real implementation, we would use inspect.signature to compare
        return True

class MockRegistry(IMockRegistry):
    """
    Registry to track mock usage and enforce policies.
    """
    def __init__(self):
        self._violations: List[MockViolationDTO] = []

    def register_violation(self, violation: MockViolationDTO) -> None:
        self._violations.append(violation)

    def get_violations(self) -> List[MockViolationDTO]:
        return list(self._violations)

class StrictMockFactory(IMockFactory):
    """
    Factory for creating strict mocks.
    """
    def __init__(self, registry: Optional[IMockRegistry] = None, inspector: Optional[IProtocolInspector] = None):
        self.registry = registry or MockRegistry()
        self.inspector = inspector or ProtocolInspector()

    def create_mock(self, protocol: Type[T], strict: bool = True, name: Optional[str] = None) -> T:
        if strict:
            # Gather all members that should be allowed on the mock
            members = self.inspector.get_protocol_members(protocol)
            # Create a MagicMock with spec_set restriction
            mock = MagicMock(spec_set=members, name=name)
            return mock  # type: ignore
        else:
            # Standard MagicMock with spec (allows adding attributes, but spec provides validation for existing ones)
            members = self.inspector.get_protocol_members(protocol)
            mock = MagicMock(spec=members, name=name)
            return mock # type: ignore

    def create_autospec(self, target: Any, **kwargs) -> Any:
        return create_autospec(target, **kwargs)

# Singleton instances for easy access
registry = MockRegistry()
inspector = ProtocolInspector()
factory = StrictMockFactory(registry, inspector)
