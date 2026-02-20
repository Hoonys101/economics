# Audit Spec: Phase 4.1 AI & Logic Refinement (Planning)

## 1. Objective
Analyze the current implementation of AI decision-making, agent lifecycle, and fiscal policy to create a consolidated proposal for "Mission 4.1". This report will be used for a design review with the Senior Architect.

## 2. Scope of Analysis

### 2.1. AI Constraint Awareness (TD-AI-DEBT-AWARE)
- **Current State**: AI agents (Firm/Household) may submit intents that violate debt ceilings, leading to rejections and log pollution.
- **Audit Task**: 
    - Identify how the `AgentSensorySnapshotDTO` provides wealth/debt data to engines.
    - Propose how to inject `current_debt_ratio` or `credit_availability` into the sensory input.
    - Recommend reward penalty mechanics for intent rejection.

### 2.2. Lifecycle Queue Scrubbing (TD-LIFECYCLE-STALE)
- **Current State**: Dead agent IDs may linger in `inter_tick_queue` or `market_queues`, causing ghost transaction attempts.
- **Audit Task**:
    - Analyze the `AgentLifecycleManager.execute` flow and the `DeathSystem`.
    - Design a `ScrubbingPhase` that identifies and removes all references to liquidated agent IDs from global queues.

### 2.3. Fiscal Stimulus & Wage Policy (TD-ECON-WAR-STIMULUS)
- **Current State**: Stimulus triggers might be masking deep-seated wage imbalances.
- **Audit Task**:
    - Review `FiscalEngine` logic for stimulus triggering.
    - Analyze the relationship between `WelfareService` spending and `Firm` productivity-wage models.
    - Propose tuning parameters to distinguish between temporary liquidity crises and permanent structural failure.

## 3. Required Output
A consolidated markdown report titled `REPORT_phase4-ai-logic-audit.md` containing:
1. **Structural Diagnosis**: Current flow of data and lifecycle events.
2. **Technical Proposal**: Detailed changes needed in DTOs, Engines, and Orchestrators.
3. **Architectural Impact**: How these changes align with the SEO Pattern and Penny Standard.
4. **Discussion Points**: Key questions for the Senior Architect.

## 4. Analysis Files
- `simulation/decisions/ai_driven_household_engine.py`
- `simulation/decisions/ai_driven_firm_engine.py`
- `simulation/systems/lifecycle_manager.py`
- `simulation/agents/government.py`
- `modules/government/engines/fiscal_engine.py`
- `simulation/dtos/api.py`
