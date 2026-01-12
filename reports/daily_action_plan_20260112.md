### 📋 2026-01-12 Daily Action Plan

**1. 🚦 System Health**
- **Architecture**: Stable
- **Top Risks**: Observer Tool Reliability (False positives in static analysis are masking potential real issues).

**2. 🚨 Critical Alerts (Must Fix)**
- No *actual* critical code defects found.
- *Note*: The scanner reported `FIXME` and `XXX` tags, but manual verification confirmed these are false positives (e.g., `GROWTH_HACKER` enum matching `HACK` tag, `WO-XXX` in documentation).

**3. 🚀 Proposed Action Plan (Jules' Proposal)**
*Jules가 제안하는 금일 작업 목록입니다.*

#### **Proposal 1: Refine Observer Scanner Logic**
- **Why**: 현재 스캐너(`scan_codebase.py`)는 `GROWTH_HACKER`와 같은 코드 용어를 `HACK` 태그로 오진하고, 문서 파일(`OPERATIONS_MANUAL.md`)의 템플릿 텍스트(`WO-XXX`)를 치명적 결함으로 보고하여 분석의 정확도를 떨어뜨립니다.
- **Target**: `scripts/observer/scan_codebase.py`
- **Plan**:
  1. **Self-Exclusion**: `scripts/observer/` 디렉토리를 스캔 대상에서 확실하게 제외하도록 경로 필터링 로직 수정.
  2. **Regex Enforcement**: 태그 매칭 시 단어 경계(`\bTAG\b`)를 적용하거나, `HACK` 태그는 주석(`# HACK`) 형태만 감지하도록 정규식 개선.
  3. **Scope Reduction**: `OPERATIONS_MANUAL.md` 및 `design/` 폴더를 스캔 대상에서 제외하거나, `.md` 파일에 대해서는 `XXX` 등 특정 태그 검사를 완화.

#### **Proposal 2: Standardize Action Proposal Configuration**
- **Why**: `simulation/decisions/action_proposal.py` 내부에 구매 가능한 물품 리스트(`["food", "luxury_food"]`)와 구매 확률 등이 하드코딩되어 있으며, 이를 설정 파일로 옮기라는 `TODO`가 방치되어 있습니다. 이는 유지보수성을 저하시킵니다.
- **Target**: `simulation/decisions/action_proposal.py`, `config.py`
- **Plan**:
  1. **Config Update**: `config.py`에 `AVAILABLE_GOODS_FOR_PURCHASE` 및 `HOUSEHOLD_PURCHASE_CHANCE` 상수 정의.
  2. **Refactoring**: `ActionProposalEngine`이 하드코딩된 값 대신 `config_module`의 상수를 참조하도록 수정.
  3. **Cleanup**: 관련 `TODO` 주석 제거.
