from modules.finance.monetary.api import IMonetaryStrategy as IMonetaryStrategy, MacroEconomicSnapshotDTO as MacroEconomicSnapshotDTO, MonetaryDecisionDTO as MonetaryDecisionDTO, MonetaryPolicyConfigDTO as MonetaryPolicyConfigDTO, MonetaryRuleType as MonetaryRuleType, OMOActionType as OMOActionType

class TaylorRuleStrategy:
    """
    Implements the Taylor Rule for interest rate targeting.
    i = r* + pi + alpha(pi - pi*) + beta(y)
    """
    @property
    def rule_type(self) -> MonetaryRuleType: ...
    def calculate_decision(self, snapshot: MacroEconomicSnapshotDTO, current_rate: float, config: MonetaryPolicyConfigDTO) -> MonetaryDecisionDTO: ...

class FriedmanKPercentStrategy:
    """
    Implements Friedman's k-percent rule.
    Targets a fixed growth rate of Money Supply (M2).
    """
    @property
    def rule_type(self) -> MonetaryRuleType: ...
    def calculate_decision(self, snapshot: MacroEconomicSnapshotDTO, current_rate: float, config: MonetaryPolicyConfigDTO) -> MonetaryDecisionDTO: ...

class McCallumRuleStrategy:
    """
    Implements McCallum Rule.
    Targets Monetary Base (M0) to stabilize Nominal GDP.
    """
    @property
    def rule_type(self) -> MonetaryRuleType: ...
    def calculate_decision(self, snapshot: MacroEconomicSnapshotDTO, current_rate: float, config: MonetaryPolicyConfigDTO) -> MonetaryDecisionDTO: ...
