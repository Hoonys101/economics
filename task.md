# Task Checklist: Phase 6 - The Brand Economy

## 0. Preparation
- [x] **Spec**: Finalize `phase6_brand_economy_spec.md` (Concrete Design)
- [ ] **Handover**: Create Work Order for Jules

## 1. Core Logic (Brand Engine)
- [ ] **Config**: Add `MARKETING_DECAY_RATE`, `LOYALTY_DECAY`, constants in `config.py`
- [ ] **Module**: Implement `simulation/brands/brand_manager.py` (Adstock, S-Curve, EMA)
- [ ] **Test**: Unit test for `BrandManager` math

## 2. Agent Updates
- [ ] **Firm**: Integrate `brand_manager` into `Firm` agent
- [ ] **Firm**: Add `marketing_budget` to action space and state
- [ ] **Household**: Add `quality_preference` and `brand_loyalty` to state

## 3. Market Overhaul (Targeted Orders)
- [ ] **DTO**: Update `Order` class with `target_agent_id`
- [ ] **Market**: Refactor `OrderBookMarket.match_orders` to handle Targeted Buy Orders (Priority Matching)
- [ ] **Household Logic**: Implement `choose_best_seller` (Utility Function)

## 4. AI & Integration
- [ ] **Reward**: Update `FirmAI` to reward Brand Awareness growth (Intangible Asset Valuation)
- [ ] **Verification**: Run `verify_brand_economy.py` (To be created)
