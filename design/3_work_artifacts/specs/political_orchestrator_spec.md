# Specification: Wave 5 Political Orchestrator

## 1. Overview
The **Political Orchestrator** is a specialized subsystem responsible for aggregating the "Will of the People" (Households) and the "Influence of Capital" (Firms). It serves as the bridge between the economic simulation and the Government's decision-making logic (RL Agent).

## 2. Core Mandates
1.  **Zero-Sum Lobbying**: Political influence is a purchasable asset. Firms must pay real money (transfer to Treasury) to exert pressure. No magic counters.
2.  **Weighted Democracy**: The simulation models a "Realpolitik" environment where social status and wealth amplify a vote's impact on the Government's approval rating.
3.  **Stateless Aggregation**: The Orchestrator collects signals per tick/cycle, produces a `PoliticalClimateDTO`, and then resets. It does not maintain long-term history (that is the role of the `GovernmentState`).

## 3. Detailed Logic

### 3.1. Voting Mechanism (Households)
The `IVoter.cast_vote` logic follows this pseudo-code:

```python
def cast_vote(self, tick, gov_state):
    # 1. Calculate Utility Gap
    # "Are my needs met?" (0.0 to 1.0)
    current_utility = self.calculate_current_utility()
    # "What did I expect?" (Based on history/class)
    expected_utility = self.social_state.expectation_threshold

    gap = current_utility - expected_utility

    # 2. Determine Approval (Sigmoid-like response)
    # If gap > 0, Approval > 0.5 (Happy)
    # If gap < 0, Approval < 0.5 (Angry)
    approval_value = clamp(0.5 + (gap * sensitivity), 0.0, 1.0)

    # 3. Identify Grievance
    primary_grievance = "NONE"
    if approval_value < 0.4:
        if self.financial_stress > 0.8:
            primary_grievance = "INFLATION" if market.inflation > 0.05 else "POVERTY"
        elif gov_state.income_tax_rate > 0.2:
            primary_grievance = "HIGH_TAX"

    # 4. Calculate Weight (Plutocracy Factor)
    # Base weight 1.0. Multiplied by Social Status (1-10) and Wealth Tier.
    weight = 1.0 * self.social_state.status_level * log(self.net_worth + 1)

    return VoteRecordDTO(
        agent_id=self.id,
        tick=tick,
        approval_value=approval_value,
        primary_grievance=primary_grievance,
        political_weight=weight
    )
```

### 3.2. Lobbying Mechanism (Firms)
The `ILobbyist.formulate_lobbying_effort` logic:

```python
def formulate_lobbying_effort(self, tick, gov_state):
    # 1. Check Pain Points
    tax_burden = self.last_tax_paid / self.revenue

    target = None
    shift = 0.0

    if tax_burden > 0.3: # Too high!
        target = "CORPORATE_TAX"
        shift = -0.05 # Lobby for 5% cut

    # 2. Check Budget
    # Willing to spend 10% of retained earnings on lobbying
    budget = self.wallet.balance * 0.10
    cost_per_point = 10000 # 100 credits per influence point

    if target and budget > cost_per_point:
        investment = min(budget, cost_per_point * 10) # Cap investment

        # 3. Create Payloads
        effort = LobbyingEffortDTO(
            firm_id=self.id,
            tick=tick,
            target_policy=target,
            desired_shift=shift,
            investment_pennies=investment
        )

        payment = PaymentRequestDTO(
            payer=self.id,
            payee="GOVERNMENT_TREASURY",
            amount=int(investment),
            currency="CREDIT",
            memo=f"LOBBYING_{target}"
        )

        return effort, payment

    return None
```

### 3.3. Aggregation Logic (The Orchestrator)
The `calculate_political_climate` method:

```python
def calculate_political_climate(self, tick):
    total_weight = 0.0
    weighted_approval_sum = 0.0
    grievance_counts = Counter()
    pressure_map = defaultdict(float)

    # 1. Process Votes
    for vote in self._vote_buffer:
        total_weight += vote.political_weight
        weighted_approval_sum += (vote.approval_value * vote.political_weight)
        if vote.primary_grievance != "NONE":
            # Grievances are also weighted!
            grievance_counts[vote.primary_grievance] += vote.political_weight

    overall_approval = weighted_approval_sum / total_weight if total_weight > 0 else 0.5

    # 2. Process Lobbying
    for lobby in self._lobbying_buffer:
        # Pressure = Money * Direction
        # e.g. 5000 pennies * -0.05 shift = -250 "Pressure Units"
        pressure = lobby.investment_pennies * lobby.desired_shift
        pressure_map[lobby.target_policy] += pressure

    return PoliticalClimateDTO(
        tick=tick,
        overall_approval_rating=overall_approval,
        party_support_breakdown={}, # TODO: Implement Party logic
        top_grievances=grievance_counts.most_common(5),
        lobbying_pressure=dict(pressure_map)
    )
```

## 4. Interfaces & Protocols
See `modules/government/political/api.py` for strict Protocol definitions.
