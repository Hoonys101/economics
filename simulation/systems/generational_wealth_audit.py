from __future__ import annotations
from typing import List, Dict, Any
import logging
from simulation.core_agents import Household

logger = logging.getLogger(__name__)

class GenerationalWealthAudit:
    """
    WO-058: Generational Wealth Audit
    Calculates and logs the distribution of wealth across generations.
    """
    def __init__(self, config_module: Any):
        self.config_module = config_module
        self.logger = logging.getLogger("simulation.systems.generational_wealth_audit")

    def run_audit(self, agents: List[Household], current_tick: int) -> None:
        """
        Calculates and logs the wealth distribution across generations.

        Args:
            agents: A list of all household agents in the simulation.
            current_tick: The current simulation tick.
        """
        wealth_by_generation: Dict[int, float] = {}
        count_by_generation: Dict[int, int] = {}

        for agent in agents:
            if not agent.is_active:
                continue

            generation = getattr(agent, 'generation', 1)
            wealth = agent.assets

            wealth_by_generation[generation] = wealth_by_generation.get(generation, 0.0) + wealth
            count_by_generation[generation] = count_by_generation.get(generation, 0) + 1

        if not wealth_by_generation:
            self.logger.info("GENERATIONAL_WEALTH_AUDIT | No active agents to audit.", extra={"tick": current_tick})
            return

        total_wealth = sum(wealth_by_generation.values())
        total_agents = sum(count_by_generation.values())

        log_message = f"GENERATIONAL_WEALTH_AUDIT | Tick: {current_tick} | Total Wealth: {total_wealth:.2f} | Total Agents: {total_agents}\n"
        for gen, wealth in sorted(wealth_by_generation.items()):
            count = count_by_generation[gen]
            avg_wealth = wealth / count if count > 0 else 0
            wealth_share = (wealth / total_wealth) * 100 if total_wealth > 0 else 0
            log_message += f"  - Gen {gen}: {count} agents, Total Wealth: {wealth:.2f} ({wealth_share:.2f}%), Avg Wealth: {avg_wealth:.2f}\n"

        self.logger.info(log_message.strip(), extra={"tick": current_tick, "tags": ["wealth_audit"]})
