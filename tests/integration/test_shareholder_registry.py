from modules.finance.shareholder_registry import ShareholderRegistry
from simulation.markets.stock_market import StockMarket
from modules.market.api import StockMarketConfigDTO

def test_registry_basic_operations():
    registry = ShareholderRegistry()

    # Register shares
    registry.register_shares(firm_id=1, agent_id=101, quantity=100.0)
    registry.register_shares(firm_id=1, agent_id=102, quantity=50.0)

    # Verify shareholders
    shareholders = registry.get_shareholders_of_firm(1)
    # Sort by agent_id for consistent assertion
    shareholders.sort(key=lambda x: x['agent_id'])

    assert len(shareholders) == 2
    assert shareholders[0]['agent_id'] == 101
    assert shareholders[0]['quantity'] == 100.0

    # Check total shares
    total = registry.get_total_shares(1)
    assert total == 150.0

    # Update shares
    registry.register_shares(firm_id=1, agent_id=101, quantity=80.0)
    assert registry.get_total_shares(1) == 130.0

    # Remove shares
    registry.register_shares(firm_id=1, agent_id=102, quantity=0.0)
    shareholders = registry.get_shareholders_of_firm(1)
    assert len(shareholders) == 1
    assert shareholders[0]['agent_id'] == 101

def test_stock_market_integration():
    registry = ShareholderRegistry()
    market = StockMarket(config_dto=StockMarketConfigDTO(book_value_multiplier=1.0), shareholder_registry=registry)

    # Initial state
    market.update_shareholder(agent_id=201, firm_id=2, quantity=500.0)

    # Verify registry is updated
    assert registry.get_total_shares(2) == 500.0
    shareholders = registry.get_shareholders_of_firm(2)
    assert len(shareholders) == 1
    assert shareholders[0]['agent_id'] == 201

if __name__ == "__main__":
    # Manual run helper
    try:
        test_registry_basic_operations()
        test_stock_market_integration()
        print("All tests passed!")
    except Exception as e:
        print(f"Test failed: {e}")
        raise
