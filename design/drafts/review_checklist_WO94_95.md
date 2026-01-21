# Review Checklist: WO-094 & WO-095

**Status**: Waiting for Jules (In Progress)

## 📋 WO-094: Phase 23 Simulation Verify
**Expected Artifacts**:
- `scripts/verify_phase23_harvest.py`
- `design/gemini_output/report_phase23_great_harvest.md`

**Audit Points**:
1. [ ] **Isolation**: 검증 스크립트가 `simulation/` 핵심 코드를 수정하지 않았는가?
2. [ ] **Logic**: `food_tfp_multiplier = 3.0`이 정상 적용되었는가?
3. [ ] **Result**:
   - Food Price Drop > 50%
   - Population Growth > 2x
   - Engel Coefficient < 50%

## 📋 WO-095: Tech Debt Cleanup
**Expected Artifacts**:
- PR Branch (Config & Refactor)

**Audit Points**:
1. [ ] **Config**: `config.py`에 `PRICE_MEMORY_LENGTH`, `WAGE_MEMORY_LENGTH` 추가 확인.
2. [ ] **EconComponent**: `deque(maxlen=...)`에 하드코딩 대신 Config 변수 사용 확인.
3. [ ] **Production**: `produce()` 메서드에서 `tech_multiplier` 중복 정의 제거 확인.
4. [ ] **Safety**: 로직 변경이 없는지(Pure Refactor) 확인. 기존 테스트 통과 여부.

---
**Action Plan on Return:**
1. `git fetch` & `git branch -r` to find PRs.
2. Update `command_registry.json` -> `git review`.
3. Run `git-go.bat`.
