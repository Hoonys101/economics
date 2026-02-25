import pytest
from modules.system.command_pipeline.service import CommandIngressService
from modules.governance.cockpit.api import CockpitCommand

def test_enqueue_and_drain():
    ingress = CommandIngressService()

    # Test Pause (Control)
    ingress.enqueue_command(CockpitCommand(type="PAUSE", payload={}))
    control_cmds = ingress.drain_control_commands()
    assert len(control_cmds) == 1
    assert control_cmds[0].command_type == "PAUSE_STATE"
    assert control_cmds[0].new_value is True

    # Test Tick Command (Set Tax)
    ingress.enqueue_command(CockpitCommand(type="SET_TAX_RATE", payload={"tax_type": "income", "rate": 0.2}))

    batch = ingress.drain_for_tick(10)
    assert batch.tick == 10
    assert len(batch.system_commands) == 1
    cmd = batch.system_commands[0]
    assert cmd.command_type == "SET_TAX_RATE"
    assert cmd.new_rate == 0.2

    # Ensure control command didn't leak
    assert len(batch.god_commands) == 0
