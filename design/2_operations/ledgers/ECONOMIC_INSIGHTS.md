# Economic Insights Ledger

This ledger records key economic insights and architectural decisions derived from the simulation development.

## [INSIGHT] R&D Investment and Endogenous Innovation Models

- **Phenomenon (Phenomenon):**
  The previous technology advancement model relied on `unlock_tick`, a fixed time-based mechanism where technologies were unlocked deterministically regardless of firm efforts. This failed to reflect the uncertainty and dynamic nature of innovation in real-world economies.

- **Cause (Cause):**
  Time-based models decouple the core activity of firms (R&D investment) from technological progress, limiting the depth of the simulation and diminishing the strategic importance of player/agent choices (investment).

- **Solution (Solution):**
  Refactored `TechnologyManager` to introduce a **Probabilistic Unlock Model** based on `cost_threshold` (development cost) and cumulative R&D investment by firms (`P = min(CAP, (Sector_R&D / Cost)^2)`). (Reference: `_check_probabilistic_unlocks`)

- **Lesson Learned (Lesson Learned):**
  Key simulation events (like technological innovation) should be driven by **Endogenous Variables**—that is, the activities of agents (e.g., R&D investment). This enhances the realism of the system, gives meaning to agents' strategic behaviors, and serves as a foundation for generating unpredictable and dynamic outcomes.
