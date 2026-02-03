# WO-4.3: PoliticalComponent Implementation

**Status**: 🟢 Ready for Implementation (PR-Chunk #4)
**Target**: `modules/household/political_component.py`, `simulation/core_agents.py`
**Goal**: Implement the "Political Self" for households as a decoupled component.

## 1. Scope of Work
- Create `PoliticalComponent` and `SocialStateDTO` extensions.
- Inject component into `Household` container.
- Implement Paradox Mechanic and Trust Damper.

## 2. Implementation Details

### 2.1. State Modeling
- Extend `SocialStateDTO` in `modules/household/dtos.py`:
  - `economic_vision: float`
  - `trust_score: float`

### 2.2. PoliticalComponent Logic
- `initialize_state(personality)`: Derive vision (Growth/Safety) with noise.
- `update_opinion(context)`: 
  - `Approval = 0.4*Satisfaction + 0.6*IdeologicalMatch`
  - If `trust < 0.2`, `Approval = 0`.
  - Update `approval_rating` (binary) and `discontent`.

### 2.3. Household Integration
- Instantiate `PoliticalComponent` in `Household.__init__`.
- Replace `self.social_component.update_political_opinion` with `self.political_component.update_opinion`.
- **Delete** deprecated `update_political_opinion` from `SocialComponent`.

## 3. Verification
- **Unit Test**: Growth-oriented personality produces vision > 0.7.
- **Integration Test**: Low asset household with growth vision supports BLUE party.
