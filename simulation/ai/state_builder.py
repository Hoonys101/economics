from typing import Dict, Any

class StateBuilder:
    def build_state(self, agent_data: Dict[str, Any], market_data: Dict[str, Any], value_orientation: str) -> Dict[str, Any]:
        """
        에이전트의 현재 상태와 시장 데이터를 기반으로 AI 모델이 사용할 상태를 dict 형태로 반환합니다.
        """
        state = {}

        # 1. Agent Data 통합
        state['assets'] = agent_data.get('assets', 0.0)
        for need_type, need_value in agent_data.get('needs', {}).items():
            state[f'need_{need_type}'] = need_value
        state['is_employed'] = float(agent_data.get('is_employed', False))
        state['labor_skill'] = agent_data.get('labor_skill', 1.0)
        state['social_status'] = agent_data.get('social_status', 0.0)

        # 2. Market Data 통합
        # goods_market prices
        if 'goods_market' in market_data and isinstance(market_data['goods_market'], dict):
            for key, value in market_data['goods_market'].items():
                if key.endswith('_current_sell_price'):
                    state[key] = value
        
        # specific goods prices
        for item_id in ['food', 'luxury_good', 'education_service']:
            if item_id in market_data and 'price' in market_data[item_id]:
                state[f'{item_id}_price'] = market_data[item_id]['price']

        # labor market data
        if 'labor' in market_data:
            state['labor_avg_wage'] = market_data['labor'].get('avg_wage', 0.0)
            state['labor_unemployment_rate'] = market_data['labor'].get('unemployment_rate', 0.0)

        # loan market data
        if 'loan_market' in market_data:
            state['loan_interest_rate'] = market_data['loan_market'].get('interest_rate', 0.0)

        # 3. Value Orientation 통합 (필요시)
        state['value_orientation'] = value_orientation # 모델이 직접 처리할 수 있도록 문자열로 포함

        # 4. Inventory 통합
        for good, quantity in agent_data.get('inventory', {}).items():
            state[f'inventory_{good}'] = quantity

        return state
