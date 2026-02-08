from typing import TypedDict, Optional

class AgentTickAnalyticsDTO(TypedDict):
    """
    Transient data container for tick-level agent analytics.
    Avoids 'getattr' probing on agent instances.
    """
    run_id: int
    time: int
    agent_id: int
    labor_income_this_tick: Optional[float]
    capital_income_this_tick: Optional[float]
    consumption_this_tick: Optional[float]
    utility_this_tick: Optional[float]
    savings_rate_this_tick: Optional[float]
