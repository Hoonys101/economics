from decimal import Decimal

def round_to_pennies(value: Decimal | float | int) -> int:
    """
    Applies Banker's Rounding (Round Half to Even) to a value to get an integer number of pennies.
    This is the standard for all monetary calculations in the simulation.

    Args:
        value: The value to round. Can be Decimal, float, or int.

    Returns:
        The rounded value as an integer number of pennies.

    Raises:
        ValueError: If the input cannot be converted to a valid Decimal.
    """
