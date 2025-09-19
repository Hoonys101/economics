class StateBuilder:
    def build_state(self, agent):
        """에이전트의 현재 상태를 dict 형태로 반환합니다."""
        state = {'assets': agent.assets, **agent.needs}
        agent_type = agent.__class__.__name__.lower()
        if agent_type == 'household':
            state['is_employed'] = float(agent.is_employed)
            state['labor_skill'] = agent.labor_skill
            state['social_status'] = agent.social_status
            for item_id, price in agent.perceived_avg_prices.items():
                state[f'perceived_price_{item_id}'] = price
        elif agent_type == 'firm':
            if hasattr(agent, 'production_targets'):
                for item_id, target_quantity in agent.production_targets.items():
                    state[f'production_target_{item_id}'] = target_quantity
            if hasattr(agent, 'employees'):
                state['num_employees'] = len(agent.employees)
        if hasattr(agent, 'inventory'):
            for good, quantity in agent.inventory.items():
                state[f'inventory_{good}'] = quantity
        return state
