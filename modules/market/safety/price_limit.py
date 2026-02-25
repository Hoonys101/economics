from typing import Optional
from modules.market.api import IPriceLimitEnforcer, CanonicalOrderDTO
from modules.market.safety_dtos import PriceLimitConfigDTO, ValidationResultDTO

class PriceLimitEnforcer(IPriceLimitEnforcer):
    """
    Stateless enforcer for price limits, strictly adhering to the Penny Standard (int).
    Validates orders against reference prices and configured limits.
    """
    def __init__(self, config: PriceLimitConfigDTO):
        self.config = config
        self.reference_price: int = 0

    def validate_order(self, order: CanonicalOrderDTO) -> ValidationResultDTO:
        """
        Validates an order's price against active boundaries.
        MUST remain strictly idempotent and side-effect free (SRP).
        """
        if not self.config.is_enabled:
            return ValidationResultDTO(is_valid=True)

        price = order.price_pennies

        # STATIC Check
        if self.config.mode == 'STATIC':
            if self.config.static_ceiling is not None and price > self.config.static_ceiling:
                return ValidationResultDTO(
                    is_valid=False,
                    reason=f"Price {price} exceeds static ceiling {self.config.static_ceiling}"
                )
            if self.config.static_floor is not None and price < self.config.static_floor:
                return ValidationResultDTO(
                    is_valid=False,
                    reason=f"Price {price} below static floor {self.config.static_floor}"
                )
            return ValidationResultDTO(is_valid=True)

        # DYNAMIC Check
        if self.config.mode == 'DYNAMIC':
            # Handle Discovery Phase (No Reference Price)
            if self.reference_price <= 0:
                # If we have static backstops, we can check them even in dynamic mode
                # But spec implies mode switch. Let's stick to simple logic:
                # If ref price is 0, we can't calculate dynamic bounds. Allow discovery.
                return ValidationResultDTO(is_valid=True, reason="Discovery Phase")

            # Calculate bounds in pennies using integer math
            # base_limit is float (e.g. 0.30).
            # We use int() truncation for safety.
            delta = int(self.reference_price * self.config.base_limit)
            upper = self.reference_price + delta
            lower = max(0, self.reference_price - delta)

            if price > upper:
                return ValidationResultDTO(
                    is_valid=False,
                    reason=f"Price {price} exceeds dynamic ceiling {upper} (Ref: {self.reference_price})"
                )
            if price < lower:
                 return ValidationResultDTO(
                     is_valid=False,
                     reason=f"Price {price} below dynamic floor {lower} (Ref: {self.reference_price})"
                 )

            return ValidationResultDTO(is_valid=True)

        # Default Safe
        return ValidationResultDTO(is_valid=True)

    def set_reference_price(self, price: int) -> None:
        """
        Sets the reference anchor price used for dynamic boundary calculations.
        """
        self.reference_price = price

    def update_config(self, config: PriceLimitConfigDTO) -> None:
        """
        Updates the enforcer's active configuration limits.
        """
        self.config = config
