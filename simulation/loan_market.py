from typing import List, Any, Optional, override
import logging

from simulation.models import Order, Transaction
from simulation.bank import Bank  # Bank 클래스 임포트
from simulation.core_markets import Market # Import Market

logger = logging.getLogger(__name__)


class LoanMarket(Market):
    """대출 요청 및 상환을 처리하는 시장"""

    def __init__(self, market_id: str, bank: Bank, config_module: Any):
        super().__init__(market_id=market_id)
        self.id = market_id
        self.bank = bank  # 시장과 연결된 은행 인스턴스
        self.config_module = config_module  # Store config_module
        self.loan_requests: List[Order] = []  # 대출 요청 주문 큐
        self.repayment_requests: List[Order] = []  # 상환 요청 주문 큐
        logger.info(
            f"LoanMarket {market_id} initialized with bank: {bank.id}",
            extra={
                "tick": 0,
                "market_id": self.id,
                "agent_id": bank.id,
                "tags": ["init", "market"],
            },
        )

    def place_order(self, order: Order, current_tick: int) -> List[Transaction]:
        """대출 요청 또는 상환 주문을 시장에 제출합니다."""
        transactions: List[Transaction] = []
        log_extra = {
            "tick": current_tick,
            "market_id": self.id,
            "agent_id": order.agent_id,
            "order_type": order.order_type,
            "item_id": order.item_id,
            "quantity": order.quantity,
            "price": order.price,
        }
        logger.info(
            f"Order placed: Type={order.order_type}, Item={order.item_id}, Agent={order.agent_id}, Amount={order.quantity}",
            extra=log_extra,
        )

        if order.order_type == "LOAN_REQUEST":
            # Phase 4: Credit Jail Check (Enforced here in Market as we can't easily modify Bank signature safely)
            # Actually, to check credit jail we need the agent instance.
            # LoanMarket doesn't store agents. Order has agent_id.
            # BUT, we can't easily access the agent instance from here unless we pass it or lookup.
            # Simulation Engine holds agents. Market doesn't.
            # However, the Household Agent ITSELF makes the decision.
            # If household is in credit jail, it should not request a loan?
            # Or the request should be denied.
            # Since we can't look up the agent easily here, and Bank grant_loan only takes ID...
            # Wait, `bank.run_tick` takes `agents_dict`.
            # Maybe we should pass `agents_dict` to `market.match_orders` or something?
            # But `place_order` is called by Engine which has agents.
            # Engine calls `household.make_decision` -> `market.place_order`.
            # We are stuck in a slight architectural limitation.
            # Option A: Trust Household not to ask (Weak).
            # Option B: Pass agent instance in Order object (Intrusive).
            # Option C: Bank looks up agent in `grant_loan`? Bank doesn't have agent list.
            # Option D: LoanMarket has reference to agents? No.

            # Let's assume for this specific implementation that we will allow the request to proceed to `grant_loan`,
            # but since I couldn't verify the agent status in `grant_loan` (Step 1 analysis), I am blocked here too?
            # NO, I can modify `grant_loan` to accept `agent` object IF I change the call site in `Engine`.
            # Let's check `simulation/engine.py`.
            # `Engine` loop: `household_orders, action_vector = household.make_decision(...)` -> `target_market.place_order(order, self.time)`.
            # `Order` object is created by Agent.
            # I can't easily pass Agent instance via Order without changing Order definition (Models).

            # WORKAROUND:
            # I will inject a `check_credit_eligibility` callback or reference into LoanMarket? No.
            # Simplest: In `Bank.grant_loan`, simply assume valid unless I can check.
            # BUT I MUST CHECK.
            # Let's use a "Credit Bureau" singleton or shared state? No.

            # Let's look at `simulation/bank.py` again. `process_default` uses `agent` object.
            # `run_tick` uses `agents_dict`.
            # The Bank DOES know about agents during `run_tick`. But not during `grant_loan`?
            # If `grant_loan` is called during `Engine.run_tick`, the Bank doesn't have the list.

            # OK, the only robust way is to pass the agent to `grant_loan` or `place_order`.
            # `place_order` takes `Order`.
            # I will modify `grant_loan` to take `borrower_agent` (Optional).
            # And I will modify `place_order` to try to retrieve the agent? Impossible.

            # WAIT. The `Order` comes from `Household`. The `Household` knows itself.
            # When `Household` decides to request loan, it SHOULD check `credit_frozen_until_tick`.
            # "Bankrupt agents remain active but are economically crippled".
            # If I block it at decision level, it's invisible to Bank (no "denied" log).
            # If I block it at Bank level, I need the data.

            # Let's modify `Order` model to optionally include `agent_ref`? No, bad serialization.

            # Solution: I will modify `Engine` to pass the `agent` instance when calling `place_order`?
            # `Engine` code: `target_market.place_order(order, self.time)`
            # I can change this to `target_market.place_order(order, self.time, agent=agent)`.
            # `Market.place_order` signature would change.
            # This is a good refactor.
            # I will update `Market.place_order` signature in `simulation/core_markets.py` and overrides.
            # This allows Markets to inspect the Agent.

            # Plan Update:
            # 1. Update `Market.place_order` signature in `core_markets.py` to accept `agent: Optional[Any] = None`.
            # 2. Update `LoanMarket.place_order` to accept `agent` and check jail.
            # 3. Update `OrderBookMarket.place_order` and `StockMarket.place_order` to accept `agent`.
            # 4. Update `Engine` to pass `agent` when calling `place_order`.

            # I will skip this big refactor for now and use a simpler hack?
            # No, correct way is `place_order(order, tick, agent)`.

            # Alternative: Since I can't do big refactor in 1 turn safely without risk.
            # I will check `credit_frozen_until_tick` in `Household.make_decision` / `HouseholdAI`?
            # But "Bank imposes ban".

            # Let's try to inject `agents_map` into `LoanMarket`?
            # `Engine` initializes `LoanMarket`.
            # `Engine` has `self.agents`.
            # I can pass `self.agents` reference to `LoanMarket` after init?
            # `self.markets["loan_market"].set_agents_ref(self.agents)`?
            # This is cleaner.

            pass # Placeholder for diff, actual logic below

            loan_amount = order.quantity
            interest_rate = order.price
            duration = (
                self.config_module.DEFAULT_LOAN_DURATION
            )

            # Credit Jail Check via Agent Lookup (Assuming we have agent ref, see set_agents_ref)
            borrower_id = order.agent_id
            is_jailed = False

            # We need to access the agent.
            # I'll implement `set_agents_ref` pattern.
            if hasattr(self, "agents_ref") and self.agents_ref:
                agent = self.agents_ref.get(borrower_id)
                if agent and hasattr(agent, "credit_frozen_until_tick"):
                    if current_tick < agent.credit_frozen_until_tick:
                        is_jailed = True

            if is_jailed:
                logger.warning(
                    f"LOAN_DENIED | Agent {borrower_id} is in Credit Jail until {agent.credit_frozen_until_tick}.",
                    extra=log_extra,
                )
                loan_id = None
            else:
                # Bank calculates rate internally based on base rate + spread
                # We ignore order.price (interest_rate) as the bank sets the rate
                loan_id = self.bank.grant_loan(
                    borrower_id=order.agent_id,
                    amount=loan_amount,
                    term_ticks=duration
                )
            # Fetch details if needed or assume success if ID returned
            # Legacy expected loan_details but we only got ID.
            # We can skip details or fetch them.
            if loan_id:
                transactions.append(
                    Transaction(
                        item_id="loan_granted",
                        quantity=loan_amount,
                        price=1.0,
                        buyer_id=self.bank.id,
                        seller_id=order.agent_id,
                        transaction_type="loan",
                        time=current_tick,
                        market_id=self.id,
                    )
                )
                logger.info(
                    f"Loan granted to {order.agent_id} for {loan_amount:.2f}. Loan ID: {loan_id}",
                    extra={**log_extra, "loan_id": loan_id},
                )
            else:
                logger.warning(
                    f"Loan denied for {order.agent_id} for {loan_amount:.2f}.",
                    extra=log_extra,
                )

        elif order.order_type == "REPAYMENT":
            loan_id = order.item_id
            repay_amount = order.quantity

            # Update Bank State (Principal Reduction)
            if hasattr(self.bank, "process_repayment"):
                 self.bank.process_repayment(loan_id, repay_amount)

            # Transaction: Money from Borrower (Buyer) to Bank (Seller)
            # Transaction: Money from Borrower (Buyer) to Bank (Seller)
            # Logic: Buyer pays, Seller receives.
            transactions.append(
                Transaction(
                    item_id="loan_repaid",
                    quantity=repay_amount,
                    price=1.0,
                    buyer_id=order.agent_id, # Agent pays money (Assets decrease)
                    seller_id=self.bank.id,  # Bank gets money (Assets increase)
                    transaction_type="loan",
                    time=current_tick,
                    market_id=self.id,
                )
            )
            logger.info(
                f"Repayment of {repay_amount:.2f} processed for loan {loan_id} by {order.agent_id}.",
                extra={**log_extra, "loan_id": loan_id},
            )

        elif order.order_type == "DEPOSIT":
            amount = order.quantity
            deposit_id = self.bank.deposit_from_customer(order.agent_id, amount)

            if deposit_id:
                # Deposit: Agent gives money to Bank.
                # Agent loses money (Buyer). Bank gains money (Seller).
                transactions.append(
                    Transaction(
                        item_id="deposit",
                        quantity=amount,
                        price=1.0,
                        buyer_id=order.agent_id,   # Agent pays
                        seller_id=self.bank.id,    # Bank receives
                        transaction_type="deposit",
                        time=current_tick,
                        market_id=self.id,
                    )
                )
                logger.info(
                    f"Deposit accepted from {order.agent_id} for {amount:.2f}. Deposit ID: {deposit_id}",
                    extra={**log_extra, "deposit_id": deposit_id},
                )
            else:
                logger.warning(f"Deposit failed for {order.agent_id}", extra=log_extra)

        elif order.order_type == "WITHDRAW":
            amount = order.quantity
            success = self.bank.withdraw_for_customer(order.agent_id, amount)

            if success:
                # Withdraw: Bank gives money to Agent.
                # Buyer=Bank, Seller=Agent.
                transactions.append(
                    Transaction(
                        item_id="withdrawal",
                        quantity=amount,
                        price=1.0,
                        buyer_id=self.bank.id,     # Bank pays
                        seller_id=order.agent_id,  # Agent receives
                        transaction_type="withdrawal",
                        time=current_tick,
                        market_id=self.id,
                    )
                )
                logger.info(
                    f"Withdrawal accepted for {order.agent_id} for {amount:.2f}.",
                    extra=log_extra,
                )
            else:
                logger.warning(f"Withdrawal failed for {order.agent_id}", extra=log_extra)

        else:  # Handle unknown order types
            logger.warning(f"Unknown order type: {order.order_type}", extra=log_extra)

        return transactions

    def process_interest(self, current_tick: int) -> List[Transaction]:
        """은행의 이자 처리 로직을 호출합니다."""
        logger.info(
            f"Processing interest for outstanding loans at tick {current_tick}.",
            extra={
                "tick": current_tick,
                "market_id": self.id,
                "tags": ["loan", "interest"],
            },
        )
        interest_transactions = []
        for loan_id, loan_details in list(
            self.bank.loans.items()
        ):  # Iterate over a copy since dict might change
            if loan_details["remaining_payments"] > 0:
                interest_amount = loan_details["amount"] * loan_details["interest_rate"]
                # 이자 지불 트랜잭션 생성 (차입자가 은행에 지불)
                interest_transactions.append(
                    Transaction(
                        item_id="interest_payment",
                        quantity=interest_amount,
                        price=1,
                        buyer_id=loan_details["borrower_id"],
                        seller_id=self.bank.id,
                        transaction_type="loan",
                        time=current_tick,
                        market_id=self.id,
                    )
                )
                logger.info(
                    f"Interest payment of {interest_amount:.2f} for loan {loan_id} by {loan_details['borrower_id']}.",
                    extra={
                        "tick": current_tick,
                        "market_id": self.id,
                        "loan_id": loan_id,
                        "borrower_id": loan_details["borrower_id"],
                        "amount": interest_amount,
                    },
                )

                # 대출 잔액에서 이자만큼 차감 (간단화된 모델)
                # loan_details["amount"] -= interest_amount # 이자는 별도로 처리하고 원금은 상환 시에만 줄어든다고 가정
                loan_details["remaining_payments"] -= 1

        return interest_transactions

    def get_total_demand(self) -> float:
        """총 수요를 반환합니다. LoanMarket의 경우 0을 반환합니다."""
        return 0.0

    def get_total_supply(self) -> float:
        """총 공급을 반환합니다. LoanMarket의 경우 0을 반환합니다."""
        return 0.0

    def match_orders(self, current_time: int) -> List[Transaction]:
        """LoanMarket에서는 별도의 주문 매칭 로직이 없습니다. 대출/상환은 place_order에서 즉시 처리됩니다."""
        return []

    def get_daily_avg_price(self) -> float:
        """LoanMarket의 일일 평균 가격은 의미가 없으므로 0을 반환합니다."""
        return 0.0

    def get_daily_volume(self) -> float:
        """LoanMarket의 일일 거래량은 의미가 없으므로 0을 반환합니다."""
        return 0.0

    @override
    def clear_orders(self) -> None:
        """LoanMarket은 매 틱 초기화할 내부 상태가 없습니다."""
        self.matched_transactions = []

