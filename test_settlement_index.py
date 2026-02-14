from simulation.systems.settlement_system import SettlementSystem

def test_index():
    ss = SettlementSystem()

    # Test register
    ss.register_account(101, 1)
    ss.register_account(101, 2)
    ss.register_account(102, 3)

    holders_101 = ss.get_account_holders(101)
    holders_102 = ss.get_account_holders(102)
    holders_103 = ss.get_account_holders(103)

    print(f"Holders 101: {sorted(holders_101)}")
    assert sorted(holders_101) == [1, 2]
    print(f"Holders 102: {holders_102}")
    assert holders_102 == [3]
    print(f"Holders 103: {holders_103}")
    assert holders_103 == []

    # Test deregister
    ss.deregister_account(101, 1)
    holders_101 = ss.get_account_holders(101)
    print(f"Holders 101 after deregister 1: {holders_101}")
    assert holders_101 == [2]

    # Test remove agent from all
    ss.register_account(101, 4)
    ss.register_account(102, 4)
    ss.register_account(103, 4)

    print(f"Holders 101 before removal: {sorted(ss.get_account_holders(101))}")

    ss.remove_agent_from_all_accounts(4)

    print(f"Holders 101 after removal: {ss.get_account_holders(101)}")
    assert 4 not in ss.get_account_holders(101)
    assert 4 not in ss.get_account_holders(102)
    assert 4 not in ss.get_account_holders(103)

    print("Verification Passed!")

if __name__ == "__main__":
    test_index()
