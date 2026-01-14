# 🕵️ Observer Scan Report
**Date:** 2026-01-14 21:04:42
**Total Files:** 467
**Total Lines:** 58690

## 1. 🏗️ Complexity Watchlist (Top 10 Big Files)
| File | Lines | Status |
|---|---|---|
| `simulation/engine.py` | 1269 | 🔴 Critical |
| `simulation/core_agents.py` | 1105 | 🔴 Critical |
| `simulation/firms.py` | 847 | 🔴 Critical |
| `config.py` | 745 | 🟡 Warning |
| `simulation/db/repository.py` | 745 | 🟡 Warning |
| `tests/test_engine.py` | 702 | 🟡 Warning |
| `simulation/decisions/ai_driven_household_engine.py` | 662 | 🟡 Warning |
| `app.py` | 617 | 🟡 Warning |
| `tests/test_firm_decision_engine_new.py` | 602 | 🟡 Warning |
| `simulation/agents/government.py` | 540 | 🟡 Warning |

## 2. 🏷️ Tech Debt Tags
| Tag | Count | Description |
|---|---|---|
| **TODO** | 17 | Review Needed |
| **FIXME** | 1 | Action Required |
| **HACK** | 15 | Review Needed |
| **REVIEW** | 0 | Review Needed |
| **NOTE** | 2 | Review Needed |
| **XXX** | 8 | Action Required |

### Critical Fixes (FIXME/XXX)
- [ ] `design/work_orders/WO-052-Maintenance-Observer-Fixes.md:68` - Exclude the `scripts/observer` directory from the scan loop to prevent the scanner from flagging its
- [ ] `OPERATIONS_MANUAL.md:51` - │   ├── work_orders/           # Jules 업무 지시서 (WO-XXX)
- [ ] `OPERATIONS_MANUAL.md:98` - # WO-XXX: [제목]
- [ ] `OPERATIONS_MANUAL.md:116` - Jules, 'design/work_orders/WO-XXX-Name.md'를 읽고 [작업 요약]을 수행하라.
- [ ] `gemini.md:144` - # Work Order: WO-XXX - [제목]
- [ ] `AGENTS.md:82` - 모든 작업은 `design/work_orders/WO-XXX-*.md` 형식의 지시서를 따릅니다.
- [ ] `design/TEAM_LEADER_HANDBOOK.md:252` - "work_order": "<WO-XXX.md>",
- [ ] `design/TEAM_LEADER_HANDBOOK.md:316` - *   **Output**: `design/specs/WO-XXX_Schema.md` (DTO, 함수 시그니처 정의)
- [ ] `design/TEAM_LEADER_HANDBOOK.md:324` - *   **Output**: `design/specs/WO-XXX_Plan.md` (구체적 로직 포함)