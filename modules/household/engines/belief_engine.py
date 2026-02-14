from typing import Dict, Any, Optional
from collections import deque

from modules.household.api import IBeliefEngine, BeliefInputDTO, BeliefResultDTO

class BeliefEngine(IBeliefEngine):
    """
    Stateless engine for updating household beliefs about prices and inflation.
    """

    def update_beliefs(self, input_dto: BeliefInputDTO) -> BeliefResultDTO:
        market_data = input_dto.market_data
        goods_market = market_data.get("goods_market")

        # We start with copies to ensure we return new state, preserving purity if caller replaces
        # However, for performance we might just copy the dicts.
        new_perceived_prices = input_dto.perceived_prices.copy()
        new_expected_inflation = input_dto.expected_inflation.copy()

        # If no goods market data, return current state
        if not goods_market:
            return BeliefResultDTO(
                new_perceived_prices=new_perceived_prices,
                new_expected_inflation=new_expected_inflation
            )

        adaptive_rate = input_dto.adaptation_rate
        stress_config = input_dto.stress_scenario_config

        if stress_config and stress_config.is_active:
            if stress_config.scenario_name == 'hyperinflation':
                # Check for attribute existence safely or if typed DTO has it
                if hasattr(stress_config, "inflation_expectation_multiplier"):
                     adaptive_rate *= stress_config.inflation_expectation_multiplier

        config = input_dto.config
        # We access price_history directly. Since it's a DefaultDict[str, Deque],
        # modifying the deque inside is an in-place operation on the structure passed.
        # This is a side-effect on the Input DTO's referenced object, which is common for large history buffers.
        price_history = input_dto.price_history

        for item_id in input_dto.goods_info_map.keys():
            # Retrieve actual price from market data
            # Key format assumed from legacy code: "{item_id}_avg_traded_price"
            actual_price = goods_market.get(f"{item_id}_avg_traded_price")

            if actual_price is not None and actual_price > 0:
                history = price_history[item_id]

                # Update Inflation Expectation
                if history:
                    last_price = history[-1]
                    if last_price > 0:
                        inflation_t = (actual_price - last_price) / last_price
                        old_expect = new_expected_inflation.get(item_id, 0.0)
                        new_expect = old_expect + adaptive_rate * (inflation_t - old_expect)
                        new_expected_inflation[item_id] = new_expect

                # Update Price History
                history.append(actual_price)

                # Update Perceived Price
                old_perceived_price = new_perceived_prices.get(item_id, actual_price)

                # Check config for update factor, fallback to default if not present (though it should be in DTO)
                update_factor = getattr(config, 'perceived_price_update_factor', 0.2)

                new_perceived_price = (update_factor * actual_price) + ((1 - update_factor) * old_perceived_price)
                new_perceived_prices[item_id] = new_perceived_price

        return BeliefResultDTO(
            new_perceived_prices=new_perceived_prices,
            new_expected_inflation=new_expected_inflation
        )
