# 🕵️ Observer Scan Report
**Date:** 2026-01-11 13:48:13
**Total Files:** 369
**Total Lines:** 48873

## 1. 🏗️ Complexity Watchlist (Top 10 Big Files)
| File | Lines | Status |
|---|---|---|
| `simulation\engine.py` | 1859 | 🔴 Critical |
| `simulation\core_agents.py` | 1114 | 🔴 Critical |
| `simulation\firms.py` | 919 | 🔴 Critical |
| `simulation\db\repository.py` | 745 | 🟡 Warning |
| `tests\test_engine.py` | 702 | 🟡 Warning |
| `config.py` | 698 | 🟡 Warning |
| `simulation\decisions\ai_driven_household_engine.py` | 657 | 🟡 Warning |
| `app.py` | 617 | 🟡 Warning |
| `tests\test_firm_decision_engine_new.py` | 602 | 🟡 Warning |
| `utils\logger.py` | 520 | 🟡 Warning |

## 2. 🏷️ Tech Debt Tags
| Tag | Count | Description |
|---|---|---|
| **TODO** | 18 | Review Needed |
| **FIXME** | 7 | Action Required |
| **HACK** | 16 | Review Needed |
| **REVIEW** | 1 | Review Needed |
| **NOTE** | 2 | Review Needed |
| **XXX** | 11 | Action Required |

### Critical Fixes (FIXME/XXX)
- [ ] `design\roles\OBSERVER_MANUAL.md:32` - 2.  **Forgotten TODOs**: 1주일 이상 방치된 `FIXME`나 Critical `TODO`가 있는가?
- [ ] `design\roles\OBSERVER_MANUAL.md:52` - - (즉시 해결해야 할 FIXME나 버그 리포트)
- [ ] `design\roles\OBSERVER_MANUAL.md:54` - - 예: `FIXME` in `corporate_manager.py`: "Insolvent crash bug" 방치됨.
- [ ] `scripts\observer\scan_codebase.py:11` - TAGS_TO_SCAN = ['TODO', 'FIXME', 'HACK', 'REVIEW', 'NOTE', 'XXX']
- [ ] `scripts\observer\scan_codebase.py:99` - desc = "Action Required" if tag in ['FIXME', 'XXX'] else "Review Needed"
- [ ] `scripts\observer\scan_codebase.py:103` - report.append("### Critical Fixes (FIXME/XXX)")
- [ ] `scripts\observer\scan_codebase.py:104` - critical_tags = tag_locations.get('FIXME', []) + tag_locations.get('XXX', [])
- [ ] `gemini.md:105` - # Work Order: WO-XXX - [제목]
- [ ] `OPERATIONS_MANUAL.md:51` - │   ├── work_orders/           # Jules 업무 지시서 (WO-XXX)
- [ ] `OPERATIONS_MANUAL.md:98` - # WO-XXX: [제목]
- [ ] `OPERATIONS_MANUAL.md:116` - Jules, 'design/work_orders/WO-XXX-Name.md'를 읽고 [작업 요약]을 수행하라.
- [ ] `.agent\rules\economics.md:35` - │   ├── work_orders/           # Jules 업무 지시서 (WO-XXX)
- [ ] `.agent\rules\economics.md:72` - # WO-XXX: [제목]
- [ ] `.agent\rules\economics.md:84` - Jules, 'design/work_orders/WO-XXX-Name.md'를 읽고 [작업 요약]을 수행하라.
- [ ] `scripts\observer\scan_codebase.py:11` - TAGS_TO_SCAN = ['TODO', 'FIXME', 'HACK', 'REVIEW', 'NOTE', 'XXX']
- [ ] `scripts\observer\scan_codebase.py:99` - desc = "Action Required" if tag in ['FIXME', 'XXX'] else "Review Needed"
- [ ] `scripts\observer\scan_codebase.py:103` - report.append("### Critical Fixes (FIXME/XXX)")
- [ ] `scripts\observer\scan_codebase.py:104` - critical_tags = tag_locations.get('FIXME', []) + tag_locations.get('XXX', [])