from enum import Enum, auto


# Intention Enum 정의 (확장)
class Intention(Enum):
    """
    AI 에이전트의 최상위 목표를 나타내는 Enum.
    가계와 기업 모두에게 적용될 수 있는 공용 목표와 각자에게 특화된 목표를 포함한다.
    """

    # 공용
    DO_NOTHING = auto()
    INCREASE_ASSETS = auto()

    # 가계용
    SATISFY_SURVIVAL_NEED = auto()
    SATISFY_SOCIAL_NEED = auto()
    IMPROVE_SKILLS = auto()

    # 기업용
    MAXIMIZE_PROFIT = auto()
    INCREASE_MARKET_SHARE = auto()
    IMPROVE_PRODUCTIVITY = auto()


# Tactic Enum 정의 (확장)
class Tactic(Enum):
    """
    Intention을 달성하기 위한 구체적인 행동 방침을 나타내는 Enum.
    """

    DO_NOTHING = auto()
    NO_ACTION = auto()
    WAIT = auto()

    # --- 가계용 Tactics ---
    # 소비 결정
    EVALUATE_CONSUMPTION_OPTIONS = auto()  # 모든 소비재 구매를 이 하나의 전술로 통합
    BUY_FOR_BUFFER = auto() # 가격이 유리할 때 필수품(예: food)의 인벤토리 완충재를 채우기 위한 구매 행동.
    BUY_BASIC_FOOD = auto()
    BUY_LUXURY_FOOD = auto()
    DO_NOTHING_CONSUMPTION = auto()

    # 자산 증식
    PARTICIPATE_LABOR_MARKET = auto()
    INVEST_IN_STOCKS = auto()
    START_BUSINESS = auto()

    # 능력 향상
    TAKE_EDUCATION = (
        auto()
    )  # 교육 서비스 구매는 소비의 일종으로 통합될 수 있으나, 일단 별도 유지

    # --- 기업용 Tactics ---
    # MAXIMIZE_PROFIT
    ADJUST_PRICE = auto()
    ADJUST_PRODUCTION = auto()
    ADJUST_WAGES = auto()
    # 새로운 가격 조정 전술
    PRICE_INCREASE_SMALL = auto()
    PRICE_INCREASE_MEDIUM = auto()
    PRICE_DECREASE_SMALL = auto()
    PRICE_DECREASE_MEDIUM = auto()
    PRICE_HOLD = auto()

    # INCREASE_MARKET_SHARE
    LOWER_PRICE = auto()
    INCREASE_MARKETING = auto()

    # IMPROVE_PRODUCTIVITY
    INVEST_IN_CAPITAL = auto()
    TRAIN_EMPLOYEES = auto()


# Personality Enum 정의 (새로 추가)
class Personality(Enum):
    """
    AI 에이전트의 고유한 특질(성격)을 나타내는 Enum.
    각 특질은 특정 Intention에 대한 욕구 성장 가중치에 영향을 미친다.
    """

    # --- Household Personalities ---
    MISER = auto()  # 수전노형 (Asset-Focused)
    STATUS_SEEKER = auto()  # 지위추구형 (Status-Seeking)
    GROWTH_ORIENTED = auto()  # 학습형 (Growth-Oriented)
    IMPULSIVE = auto()     # 충동구매형 (High Adaptation, High Hoarding)
    CONSERVATIVE = auto()  # 보수적형 (Low Adaptation)
    SURVIVAL_MODE = auto() # 생존모드 (Low Wealth)

    # --- Firm Personalities (Phase 16-B) ---
    BALANCED = auto()        # 균형형 (Profit + Brand)
    GROWTH_HACKER = auto()   # 성장형 (Market Share + Quality)
    CASH_COW = auto()        # 수익형 (Dividends + Cash Flow)


class Aggressiveness(Enum):
    """
    AI 에이전트 행동의 적극성을 나타내는 Enum.
    """

    PASSIVE = auto()
    NORMAL = auto()
    NEUTRAL = auto()
    AGGRESSIVE = auto()

class PoliticalParty(Enum):
    """
    Phase 17-5: Leviathan
    Political Parties with distinct policy biases.
    """
    BLUE = auto() # Pro-Corporate (Low Corp Tax, Subsidies)
    RED = auto()  # Pro-Household (Low Income Tax, Welfare)
