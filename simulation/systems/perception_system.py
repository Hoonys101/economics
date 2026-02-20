from collections import deque
from typing import Dict, Any, List, Optional
from dataclasses import replace
import random
import logging

from modules.system.api import MarketSnapshotDTO, MarketSignalDTO, HousingMarketSnapshotDTO
from simulation.dtos.api import GovernmentPolicyDTO

logger = logging.getLogger(__name__)

class PerceptionSystem:
    def __init__(self):
        self.snapshot_history: deque[MarketSnapshotDTO] = deque(maxlen=10)
        self.current_snapshot: Optional[MarketSnapshotDTO] = None

    def update(self, current_snapshot: MarketSnapshotDTO):
        self.current_snapshot = current_snapshot
        self.snapshot_history.append(current_snapshot)

    def apply_filter(self, agent_insight: float, current_snapshot: MarketSnapshotDTO) -> MarketSnapshotDTO:
        """
        Applies perceptual distortion based on agent insight.
        > 0.8: Smart Money (Real Time)
        > 0.3: Laggards (3-Tick MA)
        <= 0.3: Lemons (5-Tick Lag + Noise)
        """
        if agent_insight > 0.8:
            return current_snapshot

        if agent_insight > 0.3:
            # 3-Tick Moving Average
            return self._calculate_moving_average(3)

        # 5-Tick Lag + Noise
        return self._get_lagged_snapshot_with_noise(5, 0.05)

    def apply_policy_filter(self, agent_insight: float, policy: Optional[GovernmentPolicyDTO]) -> Optional[GovernmentPolicyDTO]:
        """
        Distorts Government Policy perception (Panic Index).
        Low insight -> Amplify panic.
        """
        if not policy:
            return None

        if agent_insight > 0.8:
            return policy

        # Amplify panic for low insight
        # Insight 0.0 -> Multiplier 1.8
        # Insight 0.8 -> Multiplier 1.0

        amplification = 1.0
        if agent_insight < 0.8:
            amplification = 1.0 + (0.8 - agent_insight) # Max 1.8x panic

        new_panic = min(1.0, policy.market_panic_index * amplification)

        return replace(policy, market_panic_index=new_panic)

    def _calculate_moving_average(self, window_size: int) -> MarketSnapshotDTO:
        if not self.snapshot_history:
            return self.current_snapshot # Fallback

        history = list(self.snapshot_history)[-window_size:]
        if not history:
             return self.current_snapshot

        # Use latest as template for non-numeric fields
        base = history[-1]

        # Creating a averaged signal dict
        avg_signals = {}
        for signal_key in base.market_signals:
            # Average specific fields
            total_price = 0.0
            count = 0
            for snap in history:
                sig = snap.market_signals.get(signal_key)
                if sig and sig.last_traded_price is not None:
                    total_price += sig.last_traded_price
                    count += 1

            avg_price = int(total_price / count) if count > 0 else base.market_signals[signal_key].last_traded_price

            # Replace in signal DTO
            original_sig = base.market_signals[signal_key]
            # MarketSignalDTO is frozen
            avg_signals[signal_key] = replace(original_sig, last_traded_price=avg_price)

        # Average Market Data (prices)
        avg_data = base.market_data.copy()
        # Identify price keys (heuristic: ends with _price, _cost)
        for key, val in avg_data.items():
            if isinstance(val, (int, float)) and ("price" in key or "cost" in key):
                total = 0.0
                count = 0
                for snap in history:
                    v = snap.market_data.get(key)
                    if v is not None:
                        total += v
                        count += 1
                avg_data[key] = total / count if count > 0 else val

        return replace(base, market_signals=avg_signals, market_data=avg_data)

    def _get_lagged_snapshot_with_noise(self, lag: int, noise_level: float) -> MarketSnapshotDTO:
        if len(self.snapshot_history) <= lag:
            target_snap = self.snapshot_history[0] # Oldest available
        else:
            target_snap = self.snapshot_history[-(lag + 1)]

        # Apply Gaussian Noise to prices
        noisy_signals = {}
        for k, sig in target_snap.market_signals.items():
            if sig.last_traded_price is not None:
                noise = random.gauss(0, noise_level)
                new_price = int(sig.last_traded_price * (1 + noise))
                # MarketSignalDTO is frozen
                noisy_signals[k] = replace(sig, last_traded_price=new_price)
            else:
                noisy_signals[k] = sig

        noisy_data = target_snap.market_data.copy()
        for key, val in noisy_data.items():
            if isinstance(val, (int, float)) and ("price" in key or "cost" in key):
                noise = random.gauss(0, noise_level)
                noisy_data[key] = val * (1 + noise)

        return replace(target_snap, market_signals=noisy_signals, market_data=noisy_data)
