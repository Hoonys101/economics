# 📋 2026-01-11 Daily Action Plan

**1. 🚦 System Health**
- **Architecture**: Stable
- **Top Risks**:
  1. **Economic Integrity Risk**: Potential asset leak when agents die without heirs (InheritanceManager).
  2. **Maintenance Risk**: High cyclomatic complexity in `simulation/engine.py` (1305 lines).

**2. 🚨 Critical Alerts (Must Fix)**
- **Asset Leak (Inheritance)**: `simulation/systems/inheritance_manager.py` contains a TODO (`# TODO: Handle remaining assets for No Heir case.`) indicating that while cash is confiscated, Stocks and Real Estate may remain owned by deceased agents ("Zombie Assets"), violating the Conservation of Mass.
- **Tooling False Positives**: The observer scanner (`scan_codebase.py`) incorrectly flags its own definition of tags (FIXME, XXX) as critical issues.

**3. 🚀 Proposed Action Plan (Jules' Proposal)**
*Jules가 제안하는 금일 작업 목록입니다.*

#### **Proposal 1: Fix Asset Leak in Inheritance (No Heir Case)**
- **Why**: "Zero Leak" 원칙과 "Conservation of Mass" 보존을 위해 필수적입니다. 상속인이 없는 경우(No Heir), 사망자의 잔여 주식과 부동산이 시스템에서 증발하거나 소유자 불명(Dead Agent) 상태로 남는 것을 방지해야 합니다.
- **Target**: `simulation/systems/inheritance_manager.py` (Method: `process_death`)
- **Plan**:
  1. `process_death` 메서드의 `if not heirs:` 블록 내 로직을 확장합니다.
  2. 잔여 주식(Stocks): `stock_market.update_shareholder`를 호출하여 소유권을 정부(Government)로 이전하거나 시장에 즉시 매각(Liquidation) 처리합니다.
  3. 잔여 부동산(Real Estate): `owned_properties`를 순회하며 소유권을 정부로 이전(`owner_id = None` or `government.id`)하거나 경매 처리합니다.
  4. 모든 자산 처리가 완료되면 사망자의 포트폴리오와 부동산 목록을 `clear()` 합니다.

#### **Proposal 2: Fix Observer Scanner False Positives**
- **Why**: 진단 도구의 신뢰성을 높이고, 실제 코드의 문제점(Tech Debt)에 집중하기 위함입니다. 도구 자체의 코드가 "Critical Fix"로 오진되는 노이즈를 제거해야 합니다.
- **Target**: `scripts/observer/scan_codebase.py`
- **Plan**:
  1. 스캔 대상 파일 수집 로직(`os.walk` loop)에 예외 처리를 추가합니다.
  2. `scripts/observer/` 디렉토리 또는 자기 자신(`scan_codebase.py`)을 스캔 대상에서 제외(exclude)하도록 수정합니다.
