
import logging
from typing import Any, Dict, List
from simulation.dtos.api import SimulationState
from simulation.systems.lifecycle.adapters import BirthContextAdapter
from modules.simulation.api import IBirthContext

def debug_protocol():
    # Mock SimulationState
    state = SimulationState(
        time=0,
        households=[],
        firms=[],
        agents={},
        markets={},
        primary_government=None,
        bank=None,
        central_bank=None,
        escrow_agent=None,
        stock_market=None,
        stock_tracker=None,
        goods_data={},
        market_data={},
        config_module=None,
        tracker=None,
        logger=logging.getLogger("test"),
        ai_training_manager=None,
        ai_trainer=None,
        next_agent_id=0,
        currency_registry_handler=None,
        currency_holders=[]
    )
    

    from simulation.systems.lifecycle.adapters import DeathContextAdapter
    from modules.simulation.api import IDeathContext

    death_adapter = DeathContextAdapter(state)
    print(f"\nTesting death adapter: {type(death_adapter)}")
    print(f"Is IDeathContext: {isinstance(death_adapter, IDeathContext)}")

    death_fields = [
        "time", "agents", "markets", "households", "firms", "inactive_agents",
        "currency_registry_handler", "currency_holders", "settlement_system",
        "primary_government", "real_estate_units", "bank", "transaction_processor",
        "transactions"
    ]

    for f in death_fields:
        has_attr = hasattr(death_adapter, f)
        print(f"Field {f:25}: {has_attr}")

if __name__ == "__main__":
    debug_protocol()
