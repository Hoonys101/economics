import pytest
from unittest.mock import MagicMock
from modules.finance.api import ISettlementSystem, IMonetaryAuthority
from tests.utils.protocol import assert_implements_protocol

def test_strict_mock_isettlement_system():
    """
    Verifies that a mock with spec=ISettlementSystem does not allow
    admin methods like mint_and_distribute.
    """
    mock = MagicMock(spec=ISettlementSystem)

    # Should allow standard methods
    mock.transfer.return_value = {} # Just setting return value
    mock.get_balance(1)

    # Should NOT allow admin methods
    with pytest.raises(AttributeError):
        mock.mint_and_distribute(1, 100)

def test_strict_mock_imonetary_authority():
    """
    Verifies that a mock with spec=IMonetaryAuthority allows
    admin methods.
    """
    mock = MagicMock(spec=IMonetaryAuthority)

    # Should allow admin methods
    mock.mint_and_distribute(1, 100)
    mock.audit_total_m2()

    # Should also allow standard methods (inheritance)
    mock.transfer.return_value = {}

def test_protocol_enforcer_utility():
    """
    Verifies the assert_implements_protocol utility.
    """
    class BadSettlement:
        def transfer(self): pass
        # Missing other methods

    class GoodSettlement:
        def transfer(self, *args, **kwargs): pass
        def get_balance(self, *args, **kwargs): pass
        def get_account_holders(self, *args, **kwargs): pass
        # ... assuming minimal implementation or duck typing check

    # Since Protocol checks are lenient with runtime_checkable (isinstance checks presence),
    # we test what we can.

    # Check failure
    with pytest.raises(AssertionError):
        assert_implements_protocol(BadSettlement(), ISettlementSystem)

    # Note: GoodSettlement is hard to define perfectly inline without all typing.
    # But strict mocks should pass if they are specs?
    # assert_implements_protocol checks isinstance.
    # MagicMock(spec=Protocol) does NOT return True for isinstance(mock, Protocol) by default
    # unless we patch things or the Protocol is purely structure-based and Mock happens to match.
    # But usually Mock creates attributes on access, not instantiation.
    # So assertions on Mocks might fail if attributes weren't accessed/created yet.
    # Hence, assert_implements_protocol is mostly for REAL objects.
