# 📋 [2026-01-14] Daily Action Plan

**1. 🚦 System Health**
- **Architecture**: **Degrading**
  - 핵심 모듈(`engine.py`, `core_agents.py`, `firms.py`)의 복잡도가 Critical 수준(1,000라인 근접/초과)에 도달했습니다.
- **Top Risks**:
  1. **Money Leak (WO-056)**: 자산 총합과 통화량 간의 불일치(-999.8)가 해결되지 않아 경제 시뮬레이션의 정합성을 위협 중입니다.
  2. **High Coupling**: God Class 문제로 인해 새로운 AI 정책 엔진(WO-057) 통합 시 사이드 이펙트 발생 위험이 높습니다.

**2. 🚨 Critical Alerts (Must Fix)**
- **Active Bug**: `PROJECT_STATUS.md`에 명시된 **Money Leak (-999.8)**. 즉각적인 디버깅이 필요합니다.
- **Documentation Hygiene**: `reports/observer_scan.md` 결과, `OPERATIONS_MANUAL.md` 및 `gemini.md` 등에서 `XXX`, `FIXME`와 같은 임시 플레이스홀더가 다수 발견되었습니다.

**3. 🚀 Proposed Action Plan (Jules' Proposal)**

#### **Proposal 1: Investigate and Fix Money Leak (WO-056)**
- **Why**: 화폐 보존 법칙(Conservation of Money) 위배는 경제 모델의 신뢰도를 0으로 만듭니다.
- **Target**: `simulation/engine.py` (Transaction Logic) 및 `simulation/bank.py`
- **Plan**:
  - `scan_codebase.py`로는 잡을 수 없는 런타임 누수입니다.
  - 거래 로그에 'Double-Entry Check'를 강화하여, 자산 이동 시점마다 `delta_sum == 0`을 검증하는 핫픽스를 주입합니다.

#### **Proposal 2: Documentation Cleanup**
- **Why**: 매뉴얼 내의 방치된 플레이스홀더(`WO-XXX` 등)는 스캐너의 노이즈를 증가시키고, 작업 지침의 명확성을 떨어뜨립니다.
- **Target**: `OPERATIONS_MANUAL.md`, `gemini.md`, `design/work_orders/`
- **Plan**: `observer_scan.md`에서 지적된 4개의 Critical Fixes 항목(Line 51, 98, 116 등)을 정리합니다.

#### **Proposal 3: Engine Decomposition Strategy (RFC)**
- **Why**: `engine.py` (1309 Lines)는 유지보수 한계에 도달했습니다.
- **Target**: `simulation/engine.py`
- **Plan**:
  - `Market` 관련 로직(Goods, Labor, Financial)을 별도 시스템 모듈로 분리하는 리팩토링 계획을 수립합니다.
  - 당장은 코드 수정보다는 상세 설계(Design Doc) 작성을 우선 제안합니다.
