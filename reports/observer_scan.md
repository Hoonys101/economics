# 🕵️ Observer Scan Report
**Date:** 2026-01-18 21:23:56
**Total Files:** 624
**Total Lines:** 77106

## 1. 🏗️ Complexity Watchlist (Top 10 Big Files)
| File | Lines | Status |
|---|---|---|
| `design/gemini_output/jules_engine_final.py` | 1337 | 🔴 Critical |
| `design/gemini_output/jules_engine_revised.py` | 1336 | 🔴 Critical |
| `simulation/core_agents.py` | 1040 | 🔴 Critical |
| `simulation/engine.py` | 885 | 🔴 Critical |
| `design/gemini_output/jules_firms_final.py` | 860 | 🔴 Critical |
| `design/gemini_output/jules_firms_revised.py` | 859 | 🔴 Critical |
| `config.py` | 759 | 🟡 Warning |
| `tests/test_engine.py` | 756 | 🟡 Warning |
| `simulation/db/repository.py` | 745 | 🟡 Warning |
| `simulation/firms.py` | 734 | 🟡 Warning |

## 2. 🏷️ Tech Debt Tags
| Tag | Count | Description |
|---|---|---|
| **TODO** | 16 | Review Needed |
| **FIXME** | 1 | Action Required |
| **HACK** | 15 | Review Needed |
| **REVIEW** | 0 | Review Needed |
| **NOTE** | 2 | Review Needed |
| **XXX** | 10 | Action Required |

### Critical Fixes (FIXME/XXX)
- [ ] `design/work_orders/WO-052-Maintenance-Observer-Fixes.md:68` - Exclude the `scripts/observer` directory from the scan loop to prevent the scanner from flagging its
- [ ] `OPERATIONS_MANUAL.md:51` - │   ├── work_orders/           # Jules 업무 지시서 (WO-XXX)
- [ ] `OPERATIONS_MANUAL.md:98` - # WO-XXX: [제목]
- [ ] `OPERATIONS_MANUAL.md:116` - Jules, 'design/work_orders/WO-XXX-Name.md'를 읽고 [작업 요약]을 수행하라.
- [ ] `gemini.md:145` - # Work Order: WO-XXX - [제목]
- [ ] `AGENTS.md:82` - 모든 작업은 `design/work_orders/WO-XXX-*.md` 형식의 지시서를 따릅니다.
- [ ] `design/GEMINI_USAGE_MANUAL.md:103` - 3.  **One Shot, One Kill**: Jules에게 너무 긴 지시사항을 한 번에 주면 헷갈려합니다. Work Order 문서를 먼저 만들고, JSON에는 "WO-XXX
- [ ] `design/TEAM_LEADER_HANDBOOK.md:72` - 원칙: "위험도가 고(High)이거나 리팩토링 선행 권고가 있다면, 즉시 구현 중단 및 선행 과제(TD-XXX) 별도 발주."
- [ ] `design/TEAM_LEADER_HANDBOOK.md:93` - 참조: design/work_orders/WO-XXX.md 먼저 작성
- [ ] `design/gemini_output/audit_hardcoded_debt.md:1` - 🕵️  Generating Report for: 'Task: Identify all hardcoded magic numbers and rule-based heuristics acr
- [ ] `design/drafts/draft_Write_a_Zero_Question_Implemen.md:147` - # [Refactor] Work Order: WO-XXX - 설정 중앙화 및 시나리오 로더 구현