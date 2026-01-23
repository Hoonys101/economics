import joblib  # type: ignore
import os
import logging
import numpy as np
from sklearn.linear_model import SGDRegressor
from sklearn.feature_extraction import DictVectorizer
from sklearn.preprocessing import StandardScaler


logger = logging.getLogger(__name__)


class ModelWrapper:
    def __init__(self, value_orientation):
        self.value_orientation = value_orientation
        self.model = SGDRegressor(alpha=1.0)
        self.vectorizer = DictVectorizer(sparse=False)
        self.scaler = StandardScaler()
        self.is_trained = False
        self.scaler_fitted = False
        self.model_filepath = f"ai_model_{self.value_orientation}.pkl"

        # Fit vectorizer with all possible features to ensure consistent feature space
        dummy_state = self._get_all_possible_features_dummy_state()
        self.vectorizer.fit([dummy_state])

    def _get_all_possible_features_dummy_state(self):
        # Define all possible item_ids and goods based on goods.json
        all_item_ids = ["food", "luxury_food", "education_service"]  # From goods.json
        all_goods = [
            "food",
            "luxury_food",
            "education_service",
        ]  # From goods.json, assuming all items can be inventoried

        dummy_state = {
            "assets": 0.0,
            "survival_need": 0.0,
            "social_need": 0.0,
            "growth_need": 0.0,
            "is_employed": 0.0,
            "labor_skill": 0.0,
            "social_status": 0.0,
            "num_employees": 0.0,
        }

        for item_id in all_item_ids:
            dummy_state[f"perceived_price_{item_id}"] = 0.0
            dummy_state[f"production_target_{item_id}"] = 0.0

        for good in all_goods:
            dummy_state[f"inventory_{good}"] = 0.0

        return dummy_state

    def predict(self, state_dict):
        state_vectorized = self.vectorizer.transform([state_dict])
        if state_vectorized.shape[1] == 0:
            return -np.inf

        scaled_state_vectorized = self.scaler.transform(state_vectorized)
        predicted_reward = self.model.predict(scaled_state_vectorized)[0]

        # Add logging for debugging
        logger.debug(
            f"Predicting reward for state: {state_dict}",
            extra={"tags": ["ai_predict_debug", "state"]},
        )
        logger.debug(
            f"Scaled state vector: {scaled_state_vectorized}",
            extra={"tags": ["ai_predict_debug", "scaled_state"]},
        )
        if self.is_trained:
            logger.debug(
                f"Model coefficients: {self.model.coef_}",
                extra={"tags": ["ai_predict_debug", "model_coef"]},
            )
            logger.debug(
                f"Model intercept: {self.model.intercept_}",
                extra={"tags": ["ai_predict_debug", "model_intercept"]},
            )
        logger.debug(
            f"Predicted reward: {predicted_reward}",
            extra={"tags": ["ai_predict_debug", "predicted_reward"]},
        )

        return predicted_reward

    def train(self, states, rewards):
        state_vectors = self.vectorizer.transform(states)

        if not self.scaler_fitted:
            self.scaler.fit(state_vectors)
            self.scaler_fitted = True
        scaled_state_vectors = self.scaler.transform(state_vectors)

        self.model.partial_fit(scaled_state_vectors, rewards)
        self.is_trained = True

    def save(self):
        try:
            data_to_save = {
                "model": self.model,
                "vectorizer": self.vectorizer,
                "scaler": self.scaler,
                "is_trained": self.is_trained,
                "scaler_fitted": self.scaler_fitted,
            }
            with open(self.model_filepath, "wb") as f:
                joblib.dump(data_to_save, f)
            logger.info(
                f"Model for {self.value_orientation} saved.",
                extra={"tick": 0, "agent_id": "N/A", "tags": ["ai_model", "save"]},
            )
        except Exception as e:
            logger.error(
                f"Error saving model for {self.value_orientation}: {e}",
                extra={
                    "tick": 0,
                    "agent_id": "N/A",
                    "tags": ["ai_model", "save", "error"],
                },
            )

    def load(self):
        if os.path.exists(self.model_filepath):
            try:
                with open(self.model_filepath, "rb") as f:
                    data = joblib.load(f)
                    self.model = data["model"]
                    self.vectorizer = data["vectorizer"]
                    self.scaler = data["scaler"]
                    self.is_trained = data["is_trained"]
                    self.scaler_fitted = data["scaler_fitted"]
                logger.info(
                    f"Model for {self.value_orientation} loaded.",
                    extra={"tick": 0, "agent_id": "N/A", "tags": ["ai_model", "load"]},
                )
            except Exception as e:
                logger.error(
                    f"Error loading model for {self.value_orientation}: {e}",
                    extra={
                        "tick": 0,
                        "agent_id": "N/A",
                        "tags": ["ai_model", "load", "error"],
                    },
                )
        else:
            logger.info(
                f"No existing model found for {self.value_orientation}.",
                extra={"tick": 0, "agent_id": "N/A", "tags": ["ai_model", "load"]},
            )
