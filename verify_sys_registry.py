
import sys
import os
import logging
from typing import Dict, Any
from pathlib import Path

# Ensure we can import modules
sys.path.append(os.getcwd())

from modules.system.constants import ID_CENTRAL_BANK, ID_GOVERNMENT, ID_BANK, ID_ESCROW, ID_PUBLIC_MANAGER
from simulation.initialization.initializer import SimulationInitializer
from modules.common.config_manager.api import ConfigManager
from simulation.db.repository import SimulationRepository
from modules.system.registry import AgentRegistry
from simulation.agents.government import Government
from simulation.agents.central_bank import CentralBank
from simulation.bank import Bank
from modules.system.execution.public_manager import PublicManager
from modules.system.escrow_agent import EscrowAgent

import config

class MockConfigManager(ConfigManager):
    def __init__(self):
        pass

    def get(self, key: str, default: Any = None) -> Any:
        return default

def verify():
    print("Verifying System Agent Registration...")

    # Setup dependencies
    config_manager = MockConfigManager()
    repo = SimulationRepository()

    logger = logging.getLogger("Verify")

    # Create Initializer
    initializer = SimulationInitializer(
        config_manager=config_manager,
        config_module=config,
        goods_data=[],
        repository=repo,
        logger=logger,
        households=[],
        firms=[],
        ai_trainer=None,
        initial_balances={}
    )

    # Build Simulation
    try:
        sim = initializer.build_simulation()
    except Exception as e:
        print(f"FAILED to build simulation: {e}")
        import traceback
        traceback.print_exc()
        return

    # Verify Agents in sim.agents
    print(f"sim.agents keys: {list(sim.agents.keys())}")

    assert ID_CENTRAL_BANK in sim.agents, "CentralBank not in sim.agents"
    assert ID_GOVERNMENT in sim.agents, "Government not in sim.agents"
    assert ID_BANK in sim.agents, "Bank not in sim.agents"
    assert ID_ESCROW in sim.agents, "EscrowAgent not in sim.agents"
    assert ID_PUBLIC_MANAGER in sim.agents, "PublicManager not in sim.agents"

    print("All System Agents present in sim.agents.")

    # Verify Types
    assert isinstance(sim.agents[ID_CENTRAL_BANK], CentralBank)
    assert isinstance(sim.agents[ID_GOVERNMENT], Government)
    assert isinstance(sim.agents[ID_BANK], Bank)
    assert isinstance(sim.agents[ID_ESCROW], EscrowAgent)
    assert isinstance(sim.agents[ID_PUBLIC_MANAGER], PublicManager)

    print("All System Agents have correct types.")

    # Verify AgentRegistry
    registry = sim.agent_registry

    gov = registry.get_agent(ID_GOVERNMENT)
    assert gov is not None, "Registry failed to retrieve Government by ID"
    assert gov.id == ID_GOVERNMENT, f"Government ID mismatch: {gov.id} != {ID_GOVERNMENT}"

    financial_agents = registry.get_all_financial_agents()
    ids = [a.id for a in financial_agents]
    print(f"Financial Agent IDs: {ids}")

    assert ID_CENTRAL_BANK in ids
    assert ID_GOVERNMENT in ids
    assert ID_BANK in ids
    assert ID_PUBLIC_MANAGER in ids

    print("AgentRegistry verification passed.")

    # Check PublicManager ID
    pm = sim.public_manager
    assert pm.id == ID_PUBLIC_MANAGER, f"PublicManager ID mismatch: {pm.id}"

    print("SUCCESS: System Agent Registration Verified.")

if __name__ == "__main__":
    verify()
