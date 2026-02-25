from _typeshed import Incomplete

logger: Incomplete

class ModelWrapper:
    value_orientation: Incomplete
    model: Incomplete
    vectorizer: Incomplete
    scaler: Incomplete
    is_trained: bool
    scaler_fitted: bool
    model_filepath: Incomplete
    def __init__(self, value_orientation) -> None: ...
    def predict(self, state_dict): ...
    def train(self, states, rewards) -> None: ...
    def save(self) -> None: ...
    def load(self) -> None: ...
