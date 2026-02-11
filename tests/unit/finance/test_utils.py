import pytest
from decimal import Decimal
from modules.finance.utils.currency_math import round_to_pennies

def test_round_to_pennies_basic():
    # 1.5 pennies -> 2 pennies (Round half to even)
    assert round_to_pennies(1.5) == 2
    assert round_to_pennies(2.5) == 2
    assert round_to_pennies(3.5) == 4

    # 10.0 -> 10
    assert round_to_pennies(10.0) == 10

    # 0.1 -> 0
    assert round_to_pennies(0.1) == 0

    # 0.6 -> 1
    assert round_to_pennies(0.6) == 1

def test_round_to_pennies_decimal():
    assert round_to_pennies(Decimal("1.5")) == 2
    assert round_to_pennies(Decimal("2.5")) == 2
    assert round_to_pennies(Decimal("3.5")) == 4
    assert round_to_pennies(Decimal("1.49999")) == 1
    assert round_to_pennies(Decimal("1.50001")) == 2

def test_round_to_pennies_int():
    assert round_to_pennies(100) == 100
    assert round_to_pennies(0) == 0
    assert round_to_pennies(-50) == -50

def test_round_to_pennies_large():
    # 1234.56789 -> 1235 (Nearest integer)
    # round_to_pennies assumes input is ALREADY scaled to pennies unit.
    # So 1234.5 pennies -> 1234 (Even)
    assert round_to_pennies(1234.5) == 1234

    # 1235.5 pennies -> 1236 (Even)
    assert round_to_pennies(1235.5) == 1236

def test_round_to_pennies_negative():
    # -1.5 -> -2
    assert round_to_pennies(-1.5) == -2
    # -2.5 -> -2
    assert round_to_pennies(-2.5) == -2
    # -3.5 -> -4
    assert round_to_pennies(-3.5) == -4
