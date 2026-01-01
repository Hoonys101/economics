# Task Checklist: Phase 4.5 - The Responsible Government (Fiscal Stability)

> **Goal**: Prevent economic collapse (extinction) by implementing a logic-driven Government that follows fiscal rules and responds to political approval.

## 0. Preparation
- [x] **Spec**: Finalize `phase4_5_responsible_government_spec.md`
- [ ] **Handover**: Create Work Order for Jules

## 1. Survival Parameter Tuning (Priority #1)
- [ ] **Config**: Increase `INITIAL_HOUSEHOLD_ASSETS` (Prevent early death)
- [ ] **Config**: Adjust `SURVIVAL_NEED_DEATH_THRESHOLD` or `HOUSEHOLD_DEATH_TURNS_THRESHOLD`

## 2. Political System (The Approval Function)
- [ ] **Model**: Implement `Government.evaluate_approval(household)`
    - [ ] Survival Score (Wage/Benefit)
    - [ ] Relative Score (Asset comparison)
    - [ ] Future Score (GDP Growth)
    - [ ] Tax Score (Sensitivity based on Personality)
- [ ] **Metric**: Track `average_approval_rating` in `Government` class

## 3. Fiscal Rules (The Loop)
- [ ] **Logic**: Implement `Government.adjust_fiscal_policy()`
    - [ ] **Surplus Rule**: If Cash > 10% GDP -> Distribute 30% of excess as Dividend
    - [ ] **Tax Bounding**: Rate kept between 5% and 50% (Gradual ±1% adjustment)
    - [ ] **Inflation Guard**: Halt distribution if Inflation > 5%

## 4. Verification
- [ ] **Test**: `verify_fiscal_stability.py` (Run 1000 ticks)
- [ ] **Success Criteria**:
    - [ ] Active Households > 50% after 1000 ticks
    - [ ] Tax Rate fluctuates realistically (not zero)
    - [ ] No "Money Black Hole" (Government hoarding)

---

# (Deferred) Task Checklist: Phase 6 - The Brand Economy
*Blocked until economic stability is secured.*

## 1. Core Logic
- [ ] BrandManager Module
- [ ] Config Updates

## 2. Market Overhaul
- [ ] Targeted Orders
- [ ] Household Utility Function
