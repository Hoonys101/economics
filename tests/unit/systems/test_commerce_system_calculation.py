import pytest
from unittest.mock import MagicMock
from simulation.systems.commerce_system import CommerceSystem

def test_calculate_total_cost():
    config = MagicMock()
    system = CommerceSystem(config)

    # Test cases from audit
    # 1. Simple: 10.0 * 1.0 * 1.05 = 10.5
    assert system.calculate_total_cost(10.0, 1.0, 0.05) == 10.50

    # 2. Rounding: 10.123 * 1.0 * 1.05
    # Trade: 10.12
    # Tax: 0.51
    # Total: 10.63
    assert system.calculate_total_cost(10.123, 1.0, 0.05) == 10.63

    # 3. High Qty: 0.01 * 100 * 1.05
    # Trade: 1.00
    # Tax: 0.05
    # Total: 1.05
    assert system.calculate_total_cost(0.01, 100.0, 0.05) == 1.05

    # 4. Zero tax
    assert system.calculate_total_cost(10.0, 1.0, 0.0) == 10.0
