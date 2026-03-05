import threading
import pytest
from typing import List

from modules.finance.registry.account_registry import AccountRegistry
from modules.simulation.api import AgentID


def test_account_registry_thread_safety():
    """
    Test thread safety of AccountRegistry under heavy concurrent load.
    10 threads, each performing 1000 register/deregister operations.
    """
    registry = AccountRegistry()
    num_threads = 10
    num_ops = 1000

    # We'll have threads create accounts across 5 distinct banks
    bank_ids = [AgentID(100 + i) for i in range(5)]

    def worker(thread_id: int):
        # Each thread uses a distinct set of agent IDs to avoid logical interference,
        # but they all hit the same banks to trigger concurrent dict/set access
        for op in range(num_ops):
            agent_id = AgentID(thread_id * 10000 + op)
            bank_id = bank_ids[op % len(bank_ids)]

            # Register
            registry.register_account(bank_id, agent_id)

            # Some operations get deregistered, others don't
            if op % 2 == 0:
                registry.deregister_account(bank_id, agent_id)

            # Randomly fetch holders
            if op % 10 == 0:
                registry.get_account_holders(bank_id)
                registry.get_agent_banks(agent_id)

    threads: List[threading.Thread] = []
    for i in range(num_threads):
        t = threading.Thread(target=worker, args=(i,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    # Verification (Zero-Sum Integrity Check)
    # Total accounts registered: num_threads * num_ops
    # Total accounts deregistered: num_threads * (num_ops // 2)
    # Expected remaining: num_threads * (num_ops - num_ops // 2)

    expected_remaining_per_thread = num_ops - (num_ops // 2 + num_ops % 2) if num_ops % 2 != 0 else num_ops // 2
    total_expected_remaining = num_threads * expected_remaining_per_thread

    actual_remaining = 0
    for bank_id in bank_ids:
        actual_remaining += len(registry.get_account_holders(bank_id))

    assert actual_remaining == total_expected_remaining, f"Expected {total_expected_remaining} remaining accounts, got {actual_remaining}"

    # Verify reverse mapping is also consistent
    for i in range(num_threads):
        for op in range(num_ops):
            agent_id = AgentID(i * 10000 + op)
            banks = registry.get_agent_banks(agent_id)
            if op % 2 == 0:
                # Deregistered
                assert len(banks) == 0
            else:
                # Registered
                assert len(banks) == 1
