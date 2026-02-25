from _typeshed import Incomplete
from modules.market.api import CanonicalOrderDTO as CanonicalOrderDTO, IPriceLimitEnforcer as IPriceLimitEnforcer
from modules.market.safety_dtos import PriceLimitConfigDTO as PriceLimitConfigDTO, ValidationResultDTO as ValidationResultDTO

class PriceLimitEnforcer(IPriceLimitEnforcer):
    """
    Stateless enforcer for price limits, strictly adhering to the Penny Standard (int).
    Validates orders against reference prices and configured limits.
    """
    config: Incomplete
    reference_price: int
    def __init__(self, config: PriceLimitConfigDTO) -> None: ...
    def validate_order(self, order: CanonicalOrderDTO) -> ValidationResultDTO:
        """
        Validates an order's price against active boundaries.
        MUST remain strictly idempotent and side-effect free (SRP).
        """
    def set_reference_price(self, price: int) -> None:
        """
        Sets the reference anchor price used for dynamic boundary calculations.
        """
    def update_config(self, config: PriceLimitConfigDTO) -> None:
        """
        Updates the enforcer's active configuration limits.
        """
