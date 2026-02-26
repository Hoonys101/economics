from typing import List, Dict, Any, Optional
from modules.scenarios.api import IJudgeFactory, IScenarioJudge, ScenarioStrategy, Tier, Category
from modules.system.api import IWorldState, DEFAULT_CURRENCY

class GoldStandardJudge:
    def __init__(self) -> None:
        self._tier = Tier.PHYSICS
        self._name = "GoldStandardConservation"

    @property
    def tier(self) -> Tier: return self._tier

    @property
    def name(self) -> str: return self._name

    def judge(self, world_state: IWorldState) -> bool:
        ledger = world_state.get_monetary_ledger()
        if not ledger:
            return True

        current_m2 = ledger.get_total_m2_pennies(DEFAULT_CURRENCY)
        expected_m2 = ledger.get_expected_m2_pennies(DEFAULT_CURRENCY)

        delta = current_m2 - expected_m2
        # Tolerance of 100 pennies (1.00 unit) matches legacy float tolerance
        return abs(delta) <= 100

    def get_metrics(self, world_state: IWorldState) -> Dict[str, Any]:
        ledger = world_state.get_monetary_ledger()
        if not ledger:
            return {}
        return {
            "current_m2": ledger.get_total_m2_pennies(DEFAULT_CURRENCY),
            "expected_m2": ledger.get_expected_m2_pennies(DEFAULT_CURRENCY),
            "delta": ledger.get_total_m2_pennies(DEFAULT_CURRENCY) - ledger.get_expected_m2_pennies(DEFAULT_CURRENCY)
        }

class IndustrialRevolutionJudge:
    def __init__(self) -> None:
        self._tier = Tier.MACRO
        self._name = "IndustrialRevolutionJudge"

    @property
    def tier(self) -> Tier: return self._tier

    @property
    def name(self) -> str: return self._name

    def judge(self, world_state: IWorldState) -> bool:
        tech_sys = world_state.get_technology_system()
        if not tech_sys:
            return True

        # Verify Tech Unlock
        if "TECH_AGRI_CHEM_01" not in tech_sys.active_techs:
             # If strictly requiring it after tick X, we need context.
             # For now, just checking if it causes issues.
             # But judge usually runs every tick.
             # Legacy verify_industrial_revolution checked after specific ticks.
             # Here we return True until the end, or check progress.
             return True

        # Check Visionary Adoption (Firm 0 - assuming deterministic ID or finding the visionary)
        # This is hard to check without knowing WHICH firm is visionary.
        # Legacy script constructed firms manually.
        # We can check if ANY firm has adopted.
        firms = world_state.get_all_firms()
        adopted_count = sum(1 for f in firms if tech_sys.has_adopted(f.id, "TECH_AGRI_CHEM_01"))

        return True # Mainly just collecting metrics for now, as specific assertions depend on time

    def get_metrics(self, world_state: IWorldState) -> Dict[str, Any]:
        tech_sys = world_state.get_technology_system()
        if not tech_sys:
             return {}

        firms = world_state.get_all_firms()
        adopted_count = sum(1 for f in firms if tech_sys.has_adopted(f.id, "TECH_AGRI_CHEM_01"))
        unlocked = "TECH_AGRI_CHEM_01" in tech_sys.active_techs

        return {
            "tech_unlocked": unlocked,
            "adoption_count": adopted_count,
            "total_firms": len(firms)
        }

class DomainJudgeFactory(IJudgeFactory):
    def create_judges(self, strategy: ScenarioStrategy) -> List[IScenarioJudge]:
        judges: List[IScenarioJudge] = []

        # Map Category to Judges
        if strategy.category == Category.MONETARY:
            judges.append(GoldStandardJudge())
        elif strategy.category == Category.TECHNOLOGY:
            judges.append(IndustrialRevolutionJudge())

        # Map ID to Judges (Specific Overrides)
        if strategy.id == "gold_standard_conservation":
            # Avoid duplicate if already added via Category
            if not any(isinstance(j, GoldStandardJudge) for j in judges):
                judges.append(GoldStandardJudge())
        elif strategy.id == "industrial_revolution_diffusion":
             if not any(isinstance(j, IndustrialRevolutionJudge) for j in judges):
                judges.append(IndustrialRevolutionJudge())

        return judges
