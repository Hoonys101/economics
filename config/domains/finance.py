from modules.common.config.api import FinanceConfigDTO

finance_config = FinanceConfigDTO(
    initial_base_annual_rate=0.05,
    bank_margin=0.02,
    credit_spread_base=0.02,
    loan_default_term=50,
    ticks_per_year=100.0,
    default_mortgage_rate=0.05,
    bank_deposit_margin=0.02,
    bank_credit_spread_base=0.02,
    default_loan_term_ticks=50,
    bank_solvency_buffer=1000.0,
    default_mortgage_interest_rate=0.05,
    reserve_req_ratio=0.1,
    initial_money_supply=100000.0,
    gold_standard_mode=False,
    neutral_real_rate=0.02,
    dsr_critical_threshold=0.4,
    cb_update_interval=10,
    cb_inflation_target=0.02,
    cb_taylor_alpha=1.5,
    cb_taylor_beta=0.5
)
