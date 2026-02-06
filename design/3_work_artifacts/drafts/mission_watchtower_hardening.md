# Mission Guide: Watchtower Hardening (Track A)

## 1. Objective
Finalize the real-time observability layer by implementing moving averages in the Tracker and missing demographic metrics in the Repository.

## 2. Reference Context
- [PH6_WATCHTOWER_REFINED.md](file:///c:/coding/economics/design/3_work_artifacts/specs/PH6_WATCHTOWER_REFINED.md)
- [Watchtower Architecture Plan](file:///c:/coding/economics/design/3_work_artifacts/specs/PH6_THE_WATCHTOWER_PLAN.md)

## 3. Scope of Work (Focused)
- **Tracker Update**: Implement 50-tick SMA for GDP, CPI, and M2-Leak.
- **Repository Update**: Implement `get_birth_counts` to mirror death count tracking.
- **Service Integration**: Bridge updated Tracker/Repo values into `DashboardService`.

## 4. Constraint (Purity)
- Do NOT modify `TechnologyManager` or `OrderBookMarket` logic in this mission.
- Strictly adhere to the refined spec's SMA placement (Tracker-side).
