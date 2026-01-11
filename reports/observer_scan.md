# 🕵️ Observer Scan Report
**Date:** 2026-01-11 21:00:36
**Total Files:** 383
**Total Lines:** 50170

## 1. 🏗️ Complexity Watchlist (Top 10 Big Files)
| File | Lines | Status |
|---|---|---|
| `simulation/engine.py` | 1305 | 🔴 Critical |
| `simulation/core_agents.py` | 1017 | 🔴 Critical |
| `simulation/firms.py` | 919 | 🔴 Critical |
| `simulation/db/repository.py` | 745 | 🟡 Warning |
| `config.py` | 712 | 🟡 Warning |
| `tests/test_engine.py` | 702 | 🟡 Warning |
| `simulation/decisions/ai_driven_household_engine.py` | 657 | 🟡 Warning |
| `app.py` | 617 | 🟡 Warning |
| `tests/test_firm_decision_engine_new.py` | 602 | 🟡 Warning |
| `simulation/decisions/corporate_manager.py` | 540 | 🟡 Warning |

## 2. 🏷️ Tech Debt Tags
| Tag | Count | Description |
|---|---|---|
| **TODO** | 18 | Review Needed |
| **FIXME** | 4 | Action Required |
| **HACK** | 16 | Review Needed |
| **REVIEW** | 1 | Review Needed |
| **NOTE** | 2 | Review Needed |
| **XXX** | 8 | Action Required |

### Critical Fixes (FIXME/XXX)
- [ ] `scripts/observer/scan_codebase.py:11` - TAGS_TO_SCAN = ['TODO', 'FIXME', 'HACK', 'REVIEW', 'NOTE', 'XXX']
- [ ] `scripts/observer/scan_codebase.py:99` - desc = "Action Required" if tag in ['FIXME', 'XXX'] else "Review Needed"
- [ ] `scripts/observer/scan_codebase.py:103` - report.append("### Critical Fixes (FIXME/XXX)")
- [ ] `scripts/observer/scan_codebase.py:104` - critical_tags = tag_locations.get('FIXME', []) + tag_locations.get('XXX', [])
- [ ] `OPERATIONS_MANUAL.md:51` - │   ├── work_orders/           # Jules 업무 지시서 (WO-XXX)
- [ ] `OPERATIONS_MANUAL.md:98` - # WO-XXX: [제목]
- [ ] `OPERATIONS_MANUAL.md:116` - Jules, 'design/work_orders/WO-XXX-Name.md'를 읽고 [작업 요약]을 수행하라.
- [ ] `gemini.md:146` - # Work Order: WO-XXX - [제목]
- [ ] `scripts/observer/scan_codebase.py:11` - TAGS_TO_SCAN = ['TODO', 'FIXME', 'HACK', 'REVIEW', 'NOTE', 'XXX']
- [ ] `scripts/observer/scan_codebase.py:99` - desc = "Action Required" if tag in ['FIXME', 'XXX'] else "Review Needed"
- [ ] `scripts/observer/scan_codebase.py:103` - report.append("### Critical Fixes (FIXME/XXX)")
- [ ] `scripts/observer/scan_codebase.py:104` - critical_tags = tag_locations.get('FIXME', []) + tag_locations.get('XXX', [])