# Task Checklist: Phase 4.5 - The Responsible Government (Fiscal Stability)

> **Goal**: Prevent economic collapse (extinction) by implementing a logic-driven Government that follows fiscal rules and responds to political approval.

## 0. Preparation
- [x] **Spec**: Finalize `phase4_5_responsible_government_spec.md`
- [ ] **Handover**: Create Work Order for Jules

## 1. Survival Parameter Tuning (Priority #1)
- [ ] **Config**: Increase `INITIAL_HOUSEHOLD_ASSETS` (Prevent early death)
- [ ] **Config**: Adjust `SURVIVAL_NEED_DEATH_THRESHOLD` or `HOUSEHOLD_DEATH_TURNS_THRESHOLD`
- [ ] **Config**: Set `WEALTH_THRESHOLD_FOR_LEISURE = 50000.0` (Prevent early retirement)
- [ ] **Firm Init**: Initial inventory = 50 (Prevent supply gap at Tick 1)

---

## ⚠️ Long-Term TODO: AI-Driven Labor Incentive (철학적 과제)
> **Current Approach**: "배고프면 일해라" 로직을 하드코딩으로 강제 (Starvation Fear Logic)
> **Ideal Approach**: AI가 [생존 → 노동 필요성]을 스스로 학습하도록 Reward Shaping 및 Q-Learning 개선
> **Status**: *Deferred until simulation stability is achieved*

- [ ] **Reward Shaping**: 노동 보상 함수에 "식량 재고 기반 긍정적 신호" 반영
- [ ] **Remove Hard-Coded Logic**: `calculate_labor_utility`의 `return 999999.0` 제거 후 AI가 동일 결론 도달하는지 검증

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
