# WO-108: Operation Parity (DTO & Spec Alignment)

**Date**: 2026-01-22
**Priority**: LOW
**Status**: PENDING

---

## 🎯 Mission Objective
`AUDIT_SPEC_PARITY.md`에서 지적된 DTO 필드 누락 및 명세서와의 불일치를 해결하여 데이터 정합성을 확보한다.

---

## 📋 작업 세부 지침

### 1. [TD-084] DTO Schema Extension
**파일:** `modules/household/dtos.py`, `simulation/dtos/firm_state_dto.py`
- 명세서(`design/specs/`)에 정의된 거시/미시 경제 지표 필드 중 DTO에 누락된 항목을 추가한다. (예: `perceived_fair_price`, `automation_level`, `sentiment_index` 등)
- 각 에이전트의 `get_state_dto()` 메서드가 새로운 필드들을 정확히 채워주도록 수정한다.

### 2. Parity Score Recovery
- 감사 보고서(`audit_parity_v2.md`)에서 지적한 모든 'Ghost Implementation' 항목을 실제 코드로 구현하거나, 구현 불가능할 경우 문서를 수정하여 정합성을 일치시킨다.

---

## ✅ 완료 조건
1. [ ] DTO 구조가 명세서의 데이터 요구사항을 100% 충족함.
2. [ ] `audit_parity_v2`를 재실행했을 때 점수가 95% 이상으로 상승함.

---
**Antigravity (Team Leader)**
