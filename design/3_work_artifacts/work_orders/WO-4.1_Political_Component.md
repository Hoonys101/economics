# Work Order: WO-4.1 - The Political Self (Voter Identity)

**Module**: Phase 4 - Political Economy  
**Target**: `Household` (Container), `PoliticalComponent` (New Component)  
**Status**: 🔵 Drafted  
**Goal**: Implement political identity, vision, and approval logic for individual households.

---

## 🏗️ Technical Specification

### 1. `PoliticalComponent` (New Class)
*   **Path**: `modules/household/political_component.py`
*   **Purpose**: Encapsulates ideological vision, trust in government, and approval calculations.
*   **State Variables**:
    *   `_economic_vision (float)`: $0.0$ (Safety/Red) to $1.0$ (Growth/Blue). Derived from `Personality`.
    *   `_trust_score (float)`: Initialized at $0.5$.
    *   `_current_approval (float)`: Updated every tick.

### 2. Logic: The Paradox Mechanic (지지의 역석)
*   **Formula**: $Approval = (0.4 \cdot Econ\_Satisfaction) + (0.6 \cdot (1.0 - |Vision - Gov\_Stance|))$
*   **Constituency Constraint**:
    *   `SafetyVision` households favor RED.
    *   `GrowthVision` households favor BLUE, even if their `Econ_Satisfaction` is low (The Paradox).
*   **Trust Damper**: If `trust_score < 0.2`, approval is weighted down to $0.0$.

### 3. Integration Hook (Container Injection)
*   **File**: `simulation/core_agents.py`
*   **Action**: 
    1. Import `PoliticalComponent`.
    2. Inject into `Household.__init__`: `self.political_component = PoliticalComponent(personality)`.
    3. Delegate approval calculation in `SocialComponent.update_psychology()` to `political_component.calculate_approval()`.

---

## 🧪 Verification Plan
*   **Unit Test**: `test_political_vision_assignment` - Verify vision is correctly derived from personality (Growth-Oriented -> high Vision).
*   **Unit Test**: `test_paradox_voting` - Verify a poor household (low satisfaction) with high `GrowthVision` still provides higher approval to BLUE than RED.
*   **Unit Test**: `test_trust_collapse` - Verify approval drops to $0.0$ when trust is $0.1$.

---

## 🚦 Instructions for Implementer
1.  Define `PoliticalVision` enum in `simulation/ai/enums.py`.
2.  Implement `PoliticalComponent` logic as per the formula above.
3.  Inject into `Household` and ensure the macro-data (Gov Party/Stance) is passed to the component during the simulation update loop.
