# Blueprint: Labor Market Architecture (Wave 3 Detailed Spec)

## 🏛️ Core Philosophy (Developer Context)

Implementation must strictly adhere to these three pillars to preserve economic emergence:
1.  **The Veil of Ignorance:** Agents choose majors based on **Envy (질투)**—looking at past salaries—not their own hidden talent.
2.  **The Halo Effect:** Education level is a **Signal (간판)**. Firms with low `market_insight` will overvalue degrees, while high-insight firms ignore them.
3.  **The Sunk Cost Trap:** University graduation creates an irrational **Reservation Wage** due to 매몰 비용 (Sunk Costs) and "Pride," leading to an education bubble.

---

## 1. Data Contracts

### 1.1 Agent State (Internal - Hidden)
*   `hidden_talent: Dict[IndustryDomain, float]`: 0.0-1.0. **Immutable & Hidden** from the agent itself.
*   `experience: Dict[IndustryDomain, float]`: Cumulative field years per domain.
*   `education_level`: `HIGH_SCHOOL` or `COLLEGE`.
*   `major: Optional[IndustryDomain]`: Only for `COLLEGE`.
*   `sunk_cost_pennies`: Cumulative wealth spent on education.

### 1.2 JobSeekerDTO (Public - Observable)
*   **DO NOT** expose `hidden_talent` or `actual_skill` in DTOs.
*   Include: `education_level`, `major`, `experience`, and `reservation_wage`.

---

## 2. Decision Logic (Pseudo-code)

### 2.1 Major Selection (Envy-Driven)
```python
def select_major(self, market_history):
    # Envy: Use 100-Tick Lagged SMA wages to trigger "Hog Cycles"
    historical_wages = market_history.get_100_tick_sma_wages_by_domain()
    
    # Selection: Maximize perceived income, ignore talent
    return max(historical_wages, key=historical_wages.get)
```

### 2.2 Reservation Wage (The Sunk Cost Trap)
```python
def calculate_reservation_wage(self):
    base = system_constants.BASE_WAGE
    if self.education_level == COLLEGE:
        # Pride & Sunk Costs: Demand premium + amortized tuition recovery
        return base * 1.5 + (self.sunk_cost_pennies * 0.1)
    return base * (1.0 + (self.experience[current_domain] * 0.1))
```

---

## 3. Matching & Bargaining

### 3.1 Willingness To Pay (The Halo Effect)
```python
def calculate_wtp(self, resume: JobSeekerDTO):
    expected_prod = base_productivity_calc(resume.major, resume.experience)
    
    if self.market_insight < 0.3: # Threshold for "Low Insight"
        if resume.education_level == COLLEGE:
            # Halo Effect: Blindly double expected productivity
            perceived_prod = expected_prod * 2.0
        else:
            perceived_prod = expected_prod
    else:
        # Realist: Ignore the degree, look at alignment and years
        perceived_prod = expected_prod
        
    return perceived_prod * PROFIT_MARGIN_GOAL
```

### 3.2 Nash Bargaining
```python
def resolve_match(wtp, res_wage, worker_power=0.5):
    if res_wage > wtp: return MATCH_FAILED
    
    # Wage = Reservation + Share of Surplus
    surplus = wtp - res_wage
    return res_wage + (surplus * worker_power)
```

---

## 4. Emergence & Learning

### 4.1 Actual Productivity (The Truth)
**Crucial:** University is **0.5x** more efficient per year than field work.
```python
def get_productivity(agent, domain):
    talent = agent.hidden_talent[domain]
    
    field_exp = agent.experience[domain] # 1.0 per yr
    univ_skill = 2.0 if agent.major == domain else 0.0 # 4 yrs @ 0.5 = 2.0
    
    return talent * (field_exp + univ_skill)
```

### 4.2 Firm Learning (TD-Error)
Firms must "feel" the pain of overpaying for signals.
```python
# Error = What I thought I'd get vs What the machine actually produced
td_error = expected_prod_at_hire - realized_prod_at_tick
if td_error > 0:
    # Firm learns it was tricked by the "Halo"
    self.market_insight += td_error * LEARNING_RATE
```
