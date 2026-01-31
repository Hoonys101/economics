# Work Order: - Genesis Fix (Zombie Economy)

**Phase:** 21.5 (Critical Hotfix)
**Priority:** BLOCKER
**Date:** 2026-01-10

---

## 1. Problem Statement

`scripts/iron_test.py`가 독립적으로 에이전트를 생성하면서 `main.create_simulation()`의 Genesis 로직을 우회함.

**Missing Initialization:**
| Element | main.py | iron_test.py |
|---|---|---|
| Household Initial Food | Line 189-191 ✅ | ❌ Missing |
| Firm Inventory | Lines 248-256 ✅ | ❌ Missing |
| Initial Employment | Lines 279-296 ✅ | ❌ Missing |
| Firm Founder/Owner | Lines 259-278 ✅ | ❌ Missing |
| Share Distribution | Lines 275-277 ✅ | ❌ Missing |

---

## 2. Solution Options

### Option A: Refactor iron_test.py to use `main.create_simulation()`
**Pros:** Single source of truth, no duplication.
**Cons:** Less control over test parameters.

### Option B: Copy Genesis logic into iron_test.py
**Pros:** Full control over test setup.
**Cons:** Duplication, maintenance burden.

**Recommendation: Option A** - Use `main.create_simulation()` and pass overrides.

---

## 3. Implementation Plan

### Track A: Fix iron_test.py (Jules-A)
- Replace manual agent creation with `main.create_simulation()`.
- Pass config overrides for test parameters.
- Verify Iron Test passes with proper Genesis.

### Track B: Add "Kickstart" Safety Net (Jules-B) [Optional - Phase 2]
- If even with proper Genesis economy collapses:
- Add government "Startup Stimulus" (first 10 ticks).
- Inject money into economy if GDP falls below threshold.

---

## 4. Verification

```bash
python scripts/iron_test.py --ticks 100
```

**Success Criteria:**
- Final Population > 0
- Final GDP > 0
- Labor Share > 0%

---

## 5. Jules Assignment

| Track | Assignee | Task |
|---|---|---|
| **Track A (Primary)** | Jules-A | Refactor `iron_test.py` to use `main.create_simulation()` |
| **Track B (Contingency)** | - | Only if Track A fails after fix |

**Parallelization: Single Jules only.** This is a serial fix task.
