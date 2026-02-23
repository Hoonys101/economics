from typing import TypedDict

class AgentTickAnalyticsDTO(TypedDict):
    """
    Transient data container for tick-level agent analytics.
    Avoids 'getattr' probing on agent instances.
    """
    run_id: int
    time: int
    agent_id: int
    labor_income_this_tick: int | None
    capital_income_this_tick: int | None
    consumption_this_tick: int | None
    utility_this_tick: float | None
    savings_rate_this_tick: float | None
