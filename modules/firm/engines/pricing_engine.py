from modules.firm.api import IPricingEngine, PricingInputDTO, PricingResultDTO

class PricingEngine(IPricingEngine):
    """
    Stateless engine for calculating product prices based on market signals (Invisible Hand).
    """

    def calculate_price(self, input_dto: PricingInputDTO) -> PricingResultDTO:
        """
        Calculates the new price based on excess demand/supply ratio.
        Logic adapted from Firm._calculate_invisible_hand_price.
        """
        market_snapshot = input_dto.market_snapshot
        item_id = input_dto.item_id

        demand = 0.0
        supply = 0.0
        excess_demand_ratio = 0.0

        if market_snapshot and market_snapshot.market_signals:
            signal = market_snapshot.market_signals.get(item_id)
            if signal:
                demand = signal.total_bid_quantity
                supply = signal.total_ask_quantity
                if supply > 0:
                    excess_demand_ratio = (demand - supply) / supply
                else:
                    excess_demand_ratio = 1.0 if demand > 0 else 0.0

        sensitivity = input_dto.config.invisible_hand_sensitivity
        current_price = input_dto.current_price

        # Guard against zero or negative price
        if current_price <= 0:
            current_price = 10.0

        candidate_price = current_price * (1.0 + (sensitivity * excess_demand_ratio))

        # Ensure price doesn't drop too low or become negative
        if candidate_price < 0.01:
            candidate_price = 0.01

        shadow_price = (candidate_price * 0.2) + (current_price * 0.8)

        return PricingResultDTO(
            new_price=candidate_price,
            shadow_price=shadow_price,
            demand=demand,
            supply=supply,
            excess_demand_ratio=excess_demand_ratio
        )
