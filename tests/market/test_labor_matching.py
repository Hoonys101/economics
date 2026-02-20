
import pytest
from simulation.markets.matching_engine import OrderBookMatchingEngine, MatchingResultDTO, OrderBookStateDTO, CanonicalOrderDTO
from simulation.models import Transaction

class TestLaborMatching:

    def setup_method(self):
        self.engine = OrderBookMatchingEngine()

    def create_order(self, agent_id, side, price_pennies, quantity=1.0, brand_info=None, target_agent_id=None):
        return CanonicalOrderDTO(
            agent_id=agent_id,
            side=side,
            item_id='labor',
            quantity=quantity,
            price_pennies=price_pennies,
            price_limit=price_pennies / 100.0,
            market_id='labor',
            brand_info=brand_info,
            target_agent_id=target_agent_id
        )

    def test_utility_priority_matching(self):
        """
        Scenario:
        - Firm A offers 20.00 (2000 pennies).
        - Worker 1: Skill 1.0, Educ 0. Wage 10.00 (1000 pennies). Utility = 1.0 / 1000 = 0.001
        - Worker 2: Skill 2.0, Educ 0. Wage 10.00 (1000 pennies). Utility = 2.0 / 1000 = 0.002 (Higher)

        Expect: Firm A matches with Worker 2 first.
        """
        firm_order = self.create_order(agent_id='FirmA', side='BUY', price_pennies=2000, quantity=1.0)

        worker1 = self.create_order(agent_id='Worker1', side='SELL', price_pennies=1000, quantity=1.0,
                                    brand_info={'labor_skill': 1.0, 'education_level': 0})
        worker2 = self.create_order(agent_id='Worker2', side='SELL', price_pennies=1000, quantity=1.0,
                                    brand_info={'labor_skill': 2.0, 'education_level': 0})

        state = OrderBookStateDTO(
            buy_orders={'labor': [firm_order]},
            sell_orders={'labor': [worker1, worker2]},
            market_id='labor'
        )

        result = self.engine.match(state, current_tick=1)

        assert len(result.transactions) == 1
        tx = result.transactions[0]
        assert tx.buyer_id == 'FirmA'
        assert tx.seller_id == 'Worker2' # Expected matching with higher utility worker
        assert tx.quality == 2.0 # Skill should be reflected in quality

    def test_affordability_constraint(self):
        """
        Scenario:
        - Firm A offers 15.00 (1500 pennies).
        - Worker 1: Skill 2.0 (High Util), Wage 20.00 (2000 pennies). Too expensive.
        - Worker 2: Skill 1.0 (Low Util), Wage 10.00 (1000 pennies). Affordable.

        Expect: Firm A matches with Worker 2, skipping Worker 1 despite higher utility?
        Wait, Utility = Perception / Price.
        Worker 1: 2.0 / 2000 = 0.001
        Worker 2: 1.0 / 1000 = 0.001
        Equal Utility?
        Let's make Worker 1 even better: Skill 5.0.
        Worker 1: 5.0 / 2000 = 0.0025.
        Worker 2: 1.0 / 1000 = 0.001.
        Worker 1 has higher utility but is unaffordable.
        Expect match with Worker 2.
        """
        firm_order = self.create_order(agent_id='FirmA', side='BUY', price_pennies=1500, quantity=1.0)

        worker1 = self.create_order(agent_id='Worker1', side='SELL', price_pennies=2000, quantity=1.0,
                                    brand_info={'labor_skill': 5.0, 'education_level': 0})
        worker2 = self.create_order(agent_id='Worker2', side='SELL', price_pennies=1000, quantity=1.0,
                                    brand_info={'labor_skill': 1.0, 'education_level': 0})

        state = OrderBookStateDTO(
            buy_orders={'labor': [firm_order]},
            sell_orders={'labor': [worker1, worker2]},
            market_id='labor'
        )

        result = self.engine.match(state, current_tick=1)

        assert len(result.transactions) == 1
        tx = result.transactions[0]
        assert tx.buyer_id == 'FirmA'
        assert tx.seller_id == 'Worker2'

    def test_highest_bidder_priority(self):
        """
        Scenario:
        - Firm A offers 20.00.
        - Firm B offers 30.00.
        - Worker 1: Wage 10.00.

        Expect: Firm B matches with Worker 1.
        """
        firmA = self.create_order(agent_id='FirmA', side='BUY', price_pennies=2000, quantity=1.0)
        firmB = self.create_order(agent_id='FirmB', side='BUY', price_pennies=3000, quantity=1.0)

        worker1 = self.create_order(agent_id='Worker1', side='SELL', price_pennies=1000, quantity=1.0)

        state = OrderBookStateDTO(
            buy_orders={'labor': [firmA, firmB]},
            sell_orders={'labor': [worker1]},
            market_id='labor'
        )

        result = self.engine.match(state, current_tick=1)

        assert len(result.transactions) == 1
        tx = result.transactions[0]
        assert tx.buyer_id == 'FirmB'
        assert tx.seller_id == 'Worker1'

    def test_education_impact_on_utility(self):
        """
        Scenario:
        - Firm A offers 20.00.
        - Worker 1: Skill 1.0, Educ 0. Wage 10.00. Perception = 1.0. Util = 1/1000.
        - Worker 2: Skill 1.0, Educ 10. Wage 10.00. Perception = 1.0 * (1 + 0.1*10) = 2.0. Util = 2/1000.

        Expect: Firm A matches with Worker 2.
        """
        firm_order = self.create_order(agent_id='FirmA', side='BUY', price_pennies=2000, quantity=1.0)

        worker1 = self.create_order(agent_id='Worker1', side='SELL', price_pennies=1000, quantity=1.0,
                                    brand_info={'labor_skill': 1.0, 'education_level': 0})
        worker2 = self.create_order(agent_id='Worker2', side='SELL', price_pennies=1000, quantity=1.0,
                                    brand_info={'labor_skill': 1.0, 'education_level': 10})

        state = OrderBookStateDTO(
            buy_orders={'labor': [firm_order]},
            sell_orders={'labor': [worker1, worker2]},
            market_id='labor'
        )

        result = self.engine.match(state, current_tick=1)

        assert len(result.transactions) == 1
        tx = result.transactions[0]
        assert tx.buyer_id == 'FirmA'
        assert tx.seller_id == 'Worker2'

    def test_targeted_match_priority(self):
        """
        Scenario:
        - Firm A targets Worker 1. Offer 20.00.
        - Worker 1: Wage 20.00.
        - Worker 2: Better Utility, Wage 10.00.

        Expect: Firm A matches with Worker 1 (Targeted).
        """
        firm_order = self.create_order(agent_id='FirmA', side='BUY', price_pennies=2000, quantity=1.0, target_agent_id='Worker1')

        worker1 = self.create_order(agent_id='Worker1', side='SELL', price_pennies=2000, quantity=1.0,
                                    brand_info={'labor_skill': 1.0})
        worker2 = self.create_order(agent_id='Worker2', side='SELL', price_pennies=1000, quantity=1.0,
                                    brand_info={'labor_skill': 5.0}) # Better util

        state = OrderBookStateDTO(
            buy_orders={'labor': [firm_order]},
            sell_orders={'labor': [worker1, worker2]},
            market_id='labor'
        )

        result = self.engine.match(state, current_tick=1)

        assert len(result.transactions) == 1
        tx = result.transactions[0]
        assert tx.buyer_id == 'FirmA'
        assert tx.seller_id == 'Worker1'

    def test_non_labor_market_uses_standard_logic(self):
        """
        Scenario:
        - Goods market.
        - Buyer A offers 20.00.
        - Seller 1: Price 10.00 (Cheapest).
        - Seller 2: Price 15.00 (But hypothetically higher utility if it were labor).

        Expect: Buyer A matches with Seller 1 (Cheapest).
        Standard logic sorts sells by price ascending.
        """
        buyer = self.create_order(agent_id='BuyerA', side='BUY', price_pennies=2000, quantity=1.0)

        # Give Seller 2 stats that would give high utility if it were labor
        seller1 = self.create_order(agent_id='Seller1', side='SELL', price_pennies=1000, quantity=1.0)
        seller2 = self.create_order(agent_id='Seller2', side='SELL', price_pennies=1500, quantity=1.0,
                                    brand_info={'labor_skill': 100.0, 'education_level': 100})

        # Change item_id to 'apple' and market_id to 'goods'
        state = OrderBookStateDTO(
            buy_orders={'apple': [buyer]},
            sell_orders={'apple': [seller1, seller2]},
            market_id='goods'
        )

        result = self.engine.match(state, current_tick=1)

        assert len(result.transactions) == 1
        tx = result.transactions[0]
        assert tx.buyer_id == 'BuyerA'
        assert tx.seller_id == 'Seller1' # Cheapest matched first in standard market
