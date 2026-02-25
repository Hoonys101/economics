from _typeshed import Incomplete
from simulation.systems.api import ISocialSystem as ISocialSystem, SocialMobilityContext as SocialMobilityContext
from typing import Any

class SocialSystem(ISocialSystem):
    """
    Manages social mobility, rank calculation, and reference standards for the simulation.
    """
    config: Incomplete
    def __init__(self, config: Any) -> None: ...
    def update_social_ranks(self, context: SocialMobilityContext) -> None:
        """
        Calculates and updates the social rank (percentile) for all active households.
        The score is a weighted sum of consumption and housing tier.
        """
    def calculate_reference_standard(self, context: SocialMobilityContext) -> dict[str, float]:
        """
        Calculates the average consumption and housing tier of the top 20% households.
        """
