import pytest
from simulation.orchestration.command_service import CommandService
from modules.governance.cockpit.api import CockpitCommand

def test_command_service_initialization():
    service = CommandService()
    assert service._command_queue == pytest.approx([])

def test_validate_set_base_rate_valid():
    service = CommandService()
    cmd = CockpitCommand(type="SET_BASE_RATE", payload={"rate": 0.05})
    assert service.validate_command(cmd) is True

def test_validate_set_base_rate_invalid_type():
    service = CommandService()
    cmd = CockpitCommand(type="SET_BASE_RATE", payload={"rate": "0.05"}) # string instead of float
    assert service.validate_command(cmd) is False

def test_validate_set_base_rate_out_of_bounds():
    service = CommandService()
    cmd = CockpitCommand(type="SET_BASE_RATE", payload={"rate": 0.25}) # > 0.2
    assert service.validate_command(cmd) is False

def test_validate_set_tax_rate_valid():
    service = CommandService()
    cmd = CockpitCommand(type="SET_TAX_RATE", payload={"tax_type": "corporate", "rate": 0.25})
    assert service.validate_command(cmd) is True

def test_validate_set_tax_rate_invalid_type():
    service = CommandService()
    cmd = CockpitCommand(type="SET_TAX_RATE", payload={"tax_type": "luxury", "rate": 0.25})
    assert service.validate_command(cmd) is False

def test_validate_pause_resume_step():
    service = CommandService()
    assert service.validate_command(CockpitCommand(type="PAUSE", payload={})) is True
    assert service.validate_command(CockpitCommand(type="RESUME", payload={})) is True
    assert service.validate_command(CockpitCommand(type="STEP", payload={})) is True

def test_enqueue_valid_command():
    service = CommandService()
    cmd = CockpitCommand(type="PAUSE", payload={})
    service.enqueue_command(cmd)
    assert len(service._command_queue) == 1

def test_enqueue_invalid_command():
    service = CommandService()
    cmd = CockpitCommand(type="SET_BASE_RATE", payload={"rate": 1.5})
    service.enqueue_command(cmd)
    assert len(service._command_queue) == 0

def test_pop_commands():
    service = CommandService()
    service.enqueue_command(CockpitCommand(type="PAUSE", payload={}))
    service.enqueue_command(CockpitCommand(type="RESUME", payload={}))

    commands = service.pop_commands()
    assert len(commands) == 2
    assert commands[0].type == "PAUSE"
    assert commands[1].type == "RESUME"
    assert len(service._command_queue) == 0
