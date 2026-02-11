from decimal import Decimal, ROUND_HALF_EVEN, InvalidOperation
from typing import Union, Optional

def round_to_pennies(value: Union[Decimal, float, int]) -> int:
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
    if isinstance(value, int):
        return value

    try:
        # Convert to Decimal for precise rounding
        if not isinstance(value, Decimal):
            d_value = Decimal(str(value))
        else:
            d_value = value

        # Quantize to integer (0 precision) using ROUND_HALF_EVEN
        # Since we represent pennies as integers, 1.5 pennies (float) -> 2 pennies (int)
        # Wait, the input is usually 'dollars' in float format in legacy code,
        # but the new standard says input is ALREADY scaled if it's an intermediate calc?
        # No, the spec says:
        # "interest_amount_decimal = principal_decimal * interest_rate # Decimal('3.5175')"
        # "interest_pennies = round_to_pennies(interest_amount_decimal) # 352 pennies ($3.52)"
        # So the input to this function is ALREADY in pennies units (just fractional).

        # Example:
        # Principal = 10050 pennies ($100.50)
        # Rate = 0.035 (3.5%)
        # Interest = 10050 * 0.035 = 351.75 pennies.
        # round_to_pennies(351.75) -> 352.

        rounded = d_value.quantize(Decimal('1'), rounding=ROUND_HALF_EVEN)
        return int(rounded)

    except (InvalidOperation, ValueError, TypeError) as e:
        raise ValueError(f"Cannot round invalid monetary value: {value}") from e
