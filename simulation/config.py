from __future__ import annotations
from typing import Any, List, Dict, Tuple, Optional
import os
from enum import Enum

class SimulationConfig:
    """
    Simulation Configuration Class wrapping config.py values.
    This provides a type-safe and testable interface for configuration.
    """

    # Defaults from config.py are hardcoded here for fallback or tests
    # But ideally it should load from config.py or be injected.
    # For now, we mirror key values used in systems.

    FOOD_CONSUMPTION_QUANTITY = 1.0
    PERCEIVED_PRICE_UPDATE_FACTOR = 0.1
    INFLATION_MEMORY_WINDOW = 10
    ADAPTATION_RATE_IMPULSIVE = 0.8
    ADAPTATION_RATE_NORMAL = 0.3
    ADAPTATION_RATE_CONSERVATIVE = 0.1
    BRAND_SENSITIVITY_BETA = 0.5
    HOUSEHOLD_LOW_ASSET_THRESHOLD = 100.0
    HOUSEHOLD_LOW_ASSET_WAGE = 8.0
    HOUSEHOLD_DEFAULT_WAGE = 10.0
    HOUSEHOLD_MIN_WAGE_DEMAND = 10.0

    # Added for compatibility with other components
    MAX_WORK_HOURS = 14.0
    SHOPPING_HOURS = 2.0
    HOURS_PER_TICK = 24.0
    INITIAL_RENT_PRICE = 100.0
    INITIAL_FIRM_LIQUIDITY_NEED = 200.0
    INVENTORY_HOLDING_COST_RATE = 0.005
    LIQUIDITY_NEED_INCREASE_RATE = 0.2
    ASSETS_CLOSURE_THRESHOLD = 0.0
    FIRM_CLOSURE_TURNS_THRESHOLD = 20
    FIRM_MIN_PRODUCTION_TARGET = 10.0
    INFRASTRUCTURE_TFP_BOOST = 0.05
    IMITATION_LEARNING_INTERVAL = 100
    LABOR_MARKET_MIN_WAGE = 8.0
    ENABLE_VANITY_SYSTEM = True
    GOODS = {
        "basic_food": {"initial_price": 5.0},
        "clothing": {"initial_price": 15.0},
        "luxury_food": {"initial_price": 30.0},
        "education_service": {"initial_price": 50.0},
        "iron": {"initial_price": 8.0},
        "consumer_goods": {"initial_price": 15.0},
        "luxury_bag": {"initial_price": 2000.0}
    }
    TICKS_PER_YEAR = 100.0
    INITIAL_HOUSEHOLD_ASSETS_MEAN = 5000.0
    QUALITY_PREF_SNOB_MIN = 0.7
    QUALITY_PREF_MISER_MAX = 0.3
    VALUATION_PER_MULTIPLIER = 10.0
    INVISIBLE_HAND_SENSITIVITY = 0.1
    MACRO_PORTFOLIO_ADJUSTMENT_ENABLED = True
    IPO_INITIAL_SHARES = 1000.0
    BANKRUPTCY_CONSECUTIVE_LOSS_THRESHOLD = 5
    DIVIDEND_RATE = 0.1

    def __init__(self, config_module: Any = None):
        if config_module:
            # Copy attributes from config_module if present
            for key in dir(config_module):
                if not key.startswith("__"):
                    setattr(self, key, getattr(config_module, key))
