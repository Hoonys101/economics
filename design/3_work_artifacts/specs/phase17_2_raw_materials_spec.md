# Phase 17-2: Raw Materials Market (Supply Chain) Technical Spec

## 1. Overview
This phase introduces the **B2B Supply Chain**, where firms buy goods from other firms to produce their own goods. This adds the **Cost of Goods Sold (COGS)** dynamic and **Supply Chain Constraints** (bottlenecks).

**Core Concept**: `Input Constraint`. Production is no longer just about Labor/Capital; it now requires Physical Inputs (Raw Materials).

## 2. New Firm Types

### 2.1. CollectorFirm (Extractive Industry)
- **Role**: Primary industry (Mining, Forestry, Farming).
- **Inheritance**: `Firm`.
- **Production**: Standard Cobb-Douglas (Labor + Capital). **No Material Input Required.**
- **Output**: Raw Materials (`iron`, `wood`, `grain`).
- **Economics**: High Fixed Cost (Heavy Capital), Low Variable Cost.

### 2.2. ManufacturingFirm (Secondary Industry)
- **Role**: Secondary industry (Factory, Processing).
- **Inheritance**: `Firm` (Modified logic) (or new class).
- **Production**: Constrained Cobb-Douglas.
  - `Potential_Output = Cobb_Douglas(Labor, Capital)`
  - `Material_Constraint = Input_Inventory / Input_Requirement_Per_Unit`
  - `Actual_Output = min(Potential_Output, Material_Constraint)`
- **Input Management**:
  - Requires `buy_inputs()` tactic to procure raw materials from the market *before* production.
  - Maintains `input_inventory` (distinct from `inventory` which is output).

## 3. Data Model Updates

### 3.1. Firm Class
- Add `input_inventory: Dict[str, float]` (Stores raw materials).
- Add `input_requirements: Dict[str, float]` (Config: What inputs are needed per unit of output).

### 3.2. Config (`config.py`)
- Define `RAW_MATERIALS`: `['iron', 'wood']`.
- Update `GOODS` to specify input requirements.
  ```python
  "consumer_goods": {
      "inputs": {"iron": 1.0}, # Requires 1 unit of iron per unit of consumer_goods
      ...
  }
  ```

## 4. AI & Decision Engine Updates (Complex)

### 4.1. CorporateManager (`_manage_procurement`)
- **Objective**: Ensure enough inputs for production targets.
- **Timing**: Called before production in the same tick (JIT).
- **Pricing Strategy (Architect Directive)**: **Market Taker**.
  - `Bid_Price = Market.last_price * 1.05` (5% Premium).
  - Priority is securing materials to prevent stalling.
- **Logic**:
  - `Target_Production` determines `Required_Inputs`.
  - `Deficit = Required - Current_Input_Inventory`.
  - If Deficit > 0, place `BUY` order for raw material at `Premium Price`.

### 4.2. FirmAI & Spawning Updates
- **Spawn Logic (Architect Directive)**:
  - `ManufacturingFirm` requires higher working capital to fund input purchases (B2B lag).
  - Set `initial_capital` to **1.5x ~ 2.0x** of standard firms.
- **FirmAI**:
  - State: Needs to see `Input Constraint`.
  - "Do I have enough inputs?"
- **Action**: Procurement is currently deterministic (Auto-buy needed amount).
  - *Phase 17-2 MVP*: `CorporateManager` automatically calculates and orders needed inputs based on Production Target. No separate AI channel yet.

## 5. Implementation Steps

### Step 1: Configuration
- Add `iron` to `GOODS` (Sector: `MATERIAL`).
- Add `inputs` requirements to `consumer_goods`.

### Step 2: Firm Class Update
- Initialize `input_inventory`.
- Update `produce()`:
  - Check `config_module.GOODS[self.specialization].get("inputs")`.
  - Calculate `max_possible_by_inputs`.
  - `actual_produced = min(produced_by_factors, max_possible_by_inputs)`.
  - **Deduct Used Inputs**: `self.input_inventory[mat] -= actual_produced * req`.

### Step 3: Procurement Logic (CorporateManager)
- Add `_manage_procurement(firm)` method.
- Called in `decide_ceo_actions`.
- Calculate `production_target`.
- Check needed inputs.
- Place `BUY` orders for inputs.

### Step 4: Engine Integration
- Ensure `spawn_firm` can create `iron` mines (CollectorFirm implicitly, just standard Firm with no input req).

## 6. Verification Plan
- **Script**: `tests/verify_supply_chain.py`.
- **Scenario**:
  - 1 Iron Mine (`Firm A`).
  - 1 Factory (`Firm B`) producing `consumer_goods` (needs Iron).
  - Household buys `consumer_goods`.
- **Check**:
  - Firm B buys Iron from Firm A.
  - Firm B's production is limited if Firm A produces 0.
  - Firm B's `input_inventory` drains as it produces.
