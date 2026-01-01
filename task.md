# Task Checklist: Phase 4.5 - The Responsible Government (Fiscal Stability)

> **Goal**: Prevent economic collapse (extinction) by implementing a logic-driven Government that follows fiscal rules and responds to political approval.

## 0. Preparation
- [x] **Spec**: Finalize `phase4_5_responsible_government_spec.md`
- [ ] **Handover**: Create Work Order for Jules

## 1. Survival Parameter Tuning (Priority #1)
- [x] **Config**: Increase `INITIAL_HOUSEHOLD_ASSETS` (Prevent early death)
- [x] **Config**: Adjust `SURVIVAL_NEED_DEATH_THRESHOLD` or `HOUSEHOLD_DEATH_TURNS_THRESHOLD`
- [x] **Config**: Set `WEALTH_THRESHOLD_FOR_LEISURE = 50000.0` (Prevent early retirement)
- [x] **Firm Init**: Initial inventory = 50 (Prevent supply gap at Tick 1)

---

## ⚠️ Long-Term TODO: AI-Driven Labor Incentive (철학적 과제)
> **Current Approach**: "배고프면 일해라" 로직을 하드코딩으로 강제 (Starvation Fear Logic)
> **Ideal Approach**: AI가 [생존 → 노동 필요성]을 스스로 학습하도록 Reward Shaping 및 Q-Learning 개선
> **Status**: *Deferred until simulation stability is achieved*

- [ ] **Reward Shaping**: 노동 보상 함수에 "식량 재고 기반 긍정적 신호" 반영
- [ ] **Remove Hard-Coded Logic**: `calculate_labor_utility`의 `return 999999.0` 제거 후 AI가 동일 결론 도달하는지 검증

## 2. Political System (The Approval Function)
- [x] **Model**: Implement `Government.evaluate_approval(household)`
    - [x] Survival Score (Wage/Benefit)
    - [x] Relative Score (Asset comparison)
    - [x] Future Score (GDP Growth)
    - [x] Tax Score (Sensitivity based on Personality)
- [x] **Metric**: Track `average_approval_rating` in `Government` class

## 3. Fiscal Rules (The Loop)
- [x] **Logic**: Implement `Government.adjust_fiscal_policy()`
    - [x] **Surplus Rule**: If Cash > 10% GDP -> Distribute 30% of excess as Dividend
    - [x] **Tax Bounding**: Rate kept between 5% and 50% (Gradual ±1% adjustment)
    - [x] **Inflation Guard**: Halt distribution if Inflation > 5%

## 4. Verification
- [x] **Test**: `verify_fiscal_stability.py` (Run 1000 ticks)
- [x] **Success Criteria**:
    - [x] Active Households > 50% after 1000 ticks
    - [x] Tax Rate fluctuates realistically (not zero)
    - [x] No "Money Black Hole" (Government hoarding)

---

# Task Checklist: Phase 6 - The Brand Economy (Differentiation)
> **Goal**: Transition from "Survival Economy" (Commodity) to "Brand Economy" (Product Differentiation).

## 1. Core Logic (Supply Side)
- [x] **BrandManager**: `BrandManager` class with Adstock, Awareness, Quality logic.
- [x] **Firm Integration**: `Firm` updates `BrandManager` and injects `brand_info` into Orders.
- [x] **Market Logic**: `OrderBookMarket` supports `Targeted Matching` (Buyer -> Specific Seller).

## 2. Household Logic (Demand Side)
- [x] **Spec**: Defined Preference Init & Utility Formula in `phase6_brand_economy_spec.md`.
- [ ] **Handover**: Assign `phase6_demand_instructions.md` to Jules.
- [ ] **Implementation**:
    - [ ] `Household.quality_preference` Init
    - [ ] `Household.choose_best_seller()` (Utility Logic)
    - [ ] `Targeted Buy Order` Creation in `make_decisions()`

## 3. Verification
- [ ] **Script**: `verify_brand_economy.py`
    - [ ] Check if High Brand Value Firms -> Higher Sales/Prices.
    - [ ] Verify `Adstock` decay and `Awareness` growth S-curve.
