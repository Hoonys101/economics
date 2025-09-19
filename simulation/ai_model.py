import random
from typing import Dict, Any, List
import numpy as np
import logging

from simulation.base_agent import BaseAgent
from simulation.models import Order, Transaction
from simulation.decisions.base_decision_engine import BaseDecisionEngine
from simulation.decisions.action_proposal import ActionProposalEngine
from simulation.ai.state_builder import StateBuilder
from simulation.ai.model_wrapper import ModelWrapper
from simulation.ai.reward_calculator import RewardCalculator
from simulation.ai.engine_registry import AIEngineRegistry

np.set_printoptions(threshold=np.inf)

logger = logging.getLogger(__name__)

class AIDecisionEngine(BaseDecisionEngine):
    """
    AI 기반 의사결정 엔진.
    '어떤 행동이 최선인가?'에 대한 책임을 진다.
    """
    def __init__(self, value_orientation: str, action_proposal_engine: ActionProposalEngine, state_builder: StateBuilder, epsilon=0.1):
        super().__init__()
        self.value_orientation = value_orientation
        self.action_proposal_engine = action_proposal_engine
        self.state_builder = state_builder
        self.model_wrapper = ModelWrapper(value_orientation)
        self.epsilon = epsilon
        self.model_wrapper.load()

        logger.info(f"AIDecisionEngine initialized for {value_orientation}", extra={'tick': 0, 'agent_id': 'N/A', 'tags': ['init', 'ai']})

    def make_decisions(self, agent: BaseAgent, market_data: Dict[str, Any], current_time: int) -> List[Order]:
        log_extra = {'tick': current_time, 'agent_id': agent.id, 'tags': ['ai_decision']}
        logger.debug(f"Making decision for {agent.id}. Is trained: {self.model_wrapper.is_trained}", extra=log_extra)

        candidate_action_sets = self.action_proposal_engine.propose_actions(agent, current_time)
        if not candidate_action_sets:
            return []

        # 탐색(Exploration) 또는 훈련되지 않은 모델
        if not self.model_wrapper.is_trained or random.random() < self.epsilon:
            logger.debug("Entering exploration branch.", extra=log_extra)
            return random.choice(candidate_action_sets)

        best_orders = []
        best_predicted_reward = -np.inf
        
        current_state_dict = self.state_builder.build_state(agent)

        for candidate_orders in candidate_action_sets:
            if not candidate_orders:
                continue

            hypothetical_state = current_state_dict.copy()
            
            trade_value_change = 0
            for order in candidate_orders:
                if order.order_type == 'BUY':
                    trade_value_change -= order.quantity * order.price
                else: # SELL
                    trade_value_change += order.quantity * order.price
            
            hypothetical_state['assets'] += trade_value_change

            try:
                predicted_reward = self.model_wrapper.predict(hypothetical_state)

                if predicted_reward > best_predicted_reward:
                    best_predicted_reward = predicted_reward
                    best_orders = candidate_orders
            except Exception as e:
                
                if 'NotFittedError' in str(e):
                    logger.warning(f"Predicting reward failed due to NotFittedError. Falling back to random choice. Error: {e}", extra=log_extra)
                    return random.choice(candidate_action_sets)
                logger.error(f"Error predicting reward: {e}", extra=log_extra)
        
        logger.debug(f"Best orders found with predicted reward: {best_predicted_reward:.2f}", extra=log_extra)
        return best_orders


class AITrainingManager:
    def __init__(self):
        self.experience_buffer: Dict[str, List[Dict[str, Any]]] = {}
        self.episode_experience_buffer: Dict[str, List[Dict[str, Any]]] = {}
        self.state_builder = StateBuilder()
        self.reward_calculator = RewardCalculator()
        self.proposal_engine = ActionProposalEngine(n_action_samples=10)
        self.engine_registry = AIEngineRegistry(self.proposal_engine, self.state_builder)
        logger.info("AITrainingManager initialized.", extra={'tick': 0, 'agent_id': 'N/A', 'tags': ['init', 'ai']})

    def get_engine(self, value_orientation: str) -> AIDecisionEngine:
        return self.engine_registry.get_engine(value_orientation)

    def collect_experience(self, agent: BaseAgent, pre_state: Dict[str, Any], all_transactions: List[Transaction], current_tick: int):
        post_state_assets = agent.assets
        short_term_reward = self.reward_calculator.calculate_short_term_reward(pre_state, post_state_assets)
        
        log_extra = {'tick': current_tick, 'agent_id': agent.id, 'tags': ['ai_experience']}
        logger.debug(f"Collecting experience. Short-term reward: {short_term_reward:.2f}", extra=log_extra)

        value_orientation = agent.value_orientation
        if value_orientation not in self.experience_buffer:
            self.experience_buffer[value_orientation] = []
        if value_orientation not in self.episode_experience_buffer:
            self.episode_experience_buffer[value_orientation] = []
        
        self.experience_buffer[value_orientation].append({'state': pre_state, 'reward': short_term_reward})
        self.episode_experience_buffer[value_orientation].append({
            'tick': current_tick,
            'state': pre_state,
            'agent_snapshot': {
                'assets': agent.assets,
                'labor_skill': getattr(agent, 'labor_skill', 0),
                'social_status': getattr(agent, 'social_status', 0)
            }
        })

    def end_episode(self, all_agents: List[BaseAgent]):
        # --- 단기 훈련 ---
        # (기존 단기 훈련 로직 - 현재는 비활성화)

        # --- 장기 훈련 ---
        for vo, experiences in self.episode_experience_buffer.items():
            if not experiences:
                continue

            log_extra = {'tick': 0, 'agent_id': 'N/A', 'tags': ['ai_train_long_term'], 'value_orientation': vo}
            logger.info(f"Starting long-term training for {vo}. Experiences: {len(experiences)}", extra=log_extra)

            final_states = [exp['agent_snapshot'] for exp in experiences]
            
            long_term_rewards = self.reward_calculator.calculate_long_term_reward(final_states)
            logger.debug(f"Long-term rewards for {vo}: {long_term_rewards}", extra=log_extra)

            initial_states = [exp['state'] for exp in experiences]

            try:
                engine = self.get_engine(vo)
                engine.model_wrapper.train(initial_states, long_term_rewards)
                logger.info(f"Long-term model for {vo} trained successfully.", extra=log_extra)

            except Exception as e:
                logger.error(f"Error during long-term training for {vo}: {e}", extra=log_extra)

        # 에피소드 종료 후 모든 버퍼 비우기
        self.experience_buffer = {}
        self.episode_experience_buffer = {}