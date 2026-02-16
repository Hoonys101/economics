import pytest
from typing import Protocol, runtime_checkable
from unittest.mock import MagicMock
from modules.testing.mock_governance.core import factory, ProtocolInspector
from modules.finance.api import IBank, IFinancialAgent

@runtime_checkable
class SimpleProtocol(Protocol):
    def method_one(self) -> int: ...
    @property
    def prop_one(self) -> str: ...

@runtime_checkable
class InheritedProtocol(SimpleProtocol, Protocol):
    def method_two(self) -> None: ...
    attr_one: int

class TestMockGovernance:
    def test_protocol_inspector_members(self):
        inspector = ProtocolInspector()
        members = inspector.get_protocol_members(InheritedProtocol)

        assert "method_one" in members
        assert "prop_one" in members
        assert "method_two" in members
        assert "attr_one" in members

        # Ensure private members and dunders are excluded
        assert "__init__" not in members
        assert "__module__" not in members
        assert "_is_protocol" not in members

    def test_strict_mock_creation(self):
        mock = factory.create_mock(SimpleProtocol, strict=True)

        # Valid usage
        mock.method_one.return_value = 1
        assert mock.method_one() == 1

        # Invalid usage (Drift)
        with pytest.raises(AttributeError):
            mock.non_existent_method()

        with pytest.raises(AttributeError):
            mock.new_attr = "value"

    def test_inherited_protocol_mock(self):
        mock = factory.create_mock(InheritedProtocol, strict=True)

        # From base
        mock.method_one.return_value = 1
        assert mock.method_one() == 1

        # From child
        mock.method_two()
        mock.attr_one = 10

        # Drift
        with pytest.raises(AttributeError):
            mock.drift_method()

    def test_ibank_mock_real_world(self):
        # Testing with the real IBank protocol from the codebase
        mock_bank = factory.create_mock(IBank, strict=True)

        # Check inherited from IFinancialAgent
        mock_bank.get_balance.return_value = 1000
        assert mock_bank.get_balance() == 1000

        # Check IBank specific
        mock_bank.base_rate = 0.05
        assert mock_bank.base_rate == 0.05

        # Check drift
        with pytest.raises(AttributeError):
            mock_bank.fake_method()

    def test_non_strict_mock(self):
        mock = factory.create_mock(SimpleProtocol, strict=False)

        # Valid usage
        mock.method_one.return_value = 1

        # Drift allowed in non-strict mode (setting new attributes)
        mock.new_attr = "value"
        assert mock.new_attr == "value"
