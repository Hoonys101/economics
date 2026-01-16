# 🕵️ Observer Scan Report
**Date:** 2026-01-15 21:07:51
**Total Files:** 534
**Total Lines:** 69564

## 1. 🏗️ Complexity Watchlist (Top 10 Big Files)
| File | Lines | Status |
|---|---|---|
| `design/gemini_output/jules_engine_final.py` | 1337 | 🔴 Critical |
| `simulation/engine.py` | 1337 | 🔴 Critical |
| `design/gemini_output/jules_engine_revised.py` | 1336 | 🔴 Critical |
| `simulation/core_agents.py` | 1106 | 🔴 Critical |
| `design/gemini_output/jules_firms_final.py` | 860 | 🔴 Critical |
| `simulation/firms.py` | 860 | 🔴 Critical |
| `design/gemini_output/jules_firms_revised.py` | 859 | 🔴 Critical |
| `config.py` | 759 | 🟡 Warning |
| `simulation/db/repository.py` | 745 | 🟡 Warning |
| `simulation/decisions/ai_driven_household_engine.py` | 708 | 🟡 Warning |

## 2. 🏷️ Tech Debt Tags
| Tag | Count | Description |
|---|---|---|
| **TODO** | 17 | Review Needed |
| **FIXME** | 1 | Action Required |
| **HACK** | 15 | Review Needed |
| **REVIEW** | 1 | Review Needed |
| **NOTE** | 2 | Review Needed |
| **XXX** | 7 | Action Required |

### Critical Fixes (FIXME/XXX)
- [ ] `design/work_orders/WO-052-Maintenance-Observer-Fixes.md:68` - Exclude the `scripts/observer` directory from the scan loop to prevent the scanner from flagging its
- [ ] `OPERATIONS_MANUAL.md:51` - │   ├── work_orders/           # Jules 업무 지시서 (WO-XXX)
- [ ] `OPERATIONS_MANUAL.md:98` - # WO-XXX: [제목]
- [ ] `OPERATIONS_MANUAL.md:116` - Jules, 'design/work_orders/WO-XXX-Name.md'를 읽고 [작업 요약]을 수행하라.
- [ ] `gemini.md:144` - # Work Order: WO-XXX - [제목]
- [ ] `AGENTS.md:82` - 모든 작업은 `design/work_orders/WO-XXX-*.md` 형식의 지시서를 따릅니다.
- [ ] `design/TEAM_LEADER_HANDBOOK.md:63` - 참조: design/work_orders/WO-XXX.md 먼저 작성
- [ ] `design/gemini_output/audit_hardcoded_debt.md:1` - 🕵️  Generating Report for: 'Task: Identify all hardcoded magic numbers and rule-based heuristics acr