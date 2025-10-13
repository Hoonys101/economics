import numpy as np
from typing import Any

class RewardCalculator:
    def __init__(self, config_module: Any):
        self.config_module = config_module

    def calculate_short_term_reward(self, pre_state, post_state_assets):
        pre_state_assets = pre_state.get('assets', 0)
        return post_state_assets - pre_state_assets

    def calculate_long_term_reward(self, final_states):
        rewards = []
        for final_state in final_states:
            reward = final_state['assets'] * self.config_module.AI_ASSET_REWARD_WEIGHT
            reward += final_state['labor_skill'] * self.config_module.AI_SKILL_REWARD_WEIGHT
            reward += final_state.get('social_status', 0) * self.config_module.AI_SOCIAL_STATUS_REWARD_WEIGHT
            # Add other long-term goals here, e.g., growth_need, wealth_need, etc.
            # reward += final_state.get('growth_need', 0) * self.config_module.AI_GROWTH_REWARD_WEIGHT
            # reward += final_state.get('wealth_need', 0) * self.config_module.AI_WEALTH_REWARD_WEIGHT
            rewards.append(reward)
        return np.array(rewards)
