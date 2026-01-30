# 🛠️ Technical Debt Register (High-Level Summary)

> **목적**: 시뮬레이션의 신뢰성을 저해하거나 유지보수를 어렵게 하는 기술적 부채를 추적 관리합니다.
> **최고 권위 원부**: [TECH_DEBT_LEDGER.md](./TECH_DEBT_LEDGER.md)

---

## 🚨 Active & Critical

### [TD-132] Hardcoded Government ID
- **발견일**: 2026-01-28
- **증상**: `GOVERNMENT_ID`가 전역 상수로 하드코딩되어 멀티 인스턴스 시뮬레이션 시 위험.
- **해결 방안**: `WorldState` 또는 `Registry`를 통해 동적 확인.

### [TD-156] Systemic Monetary Leak (M2 Drift)
- **발견일**: 2026-01-30
- **증상**: "The Great Reset" 검증 중 +/- 900k 이상의 막대한 통화량 오차 발견.
- **영향**: 시뮬레이션의 물리적 법칙(질량 보존) 위배.

### [TD-157] Price-Consumption Deadlock
- **발견일**: 2026-01-30
- **증상**: WO-097 재검증 중 식료품 가격이 $5.00$에서 고정되어 변하지 않는 현상.
- **영향**: 시장 메커니즘 마비 및 인구 붕괴 유발.

### [TD-140~142] God File Infestation (LOC > 600)
- **대상**: `db/repository.py`, `ai_driven_household_engine.py`, `corporate_manager.py`
- **조치**: 클래스 쪼개기(Decomposition) 및 관심사 분리(SoC) 수행.

### [TD-143] Hardcoded Placeholders (WO-XXX)
- **내능**: 문서 내에 `WO-XXX` 형태의 자리 표시자 잔존.

---

## ✅ Resolved (Recent)

| ID | Title | Solution |
|---|---|---|
| **TD-123** | God Class: `Household` | Decomposed into Stateless Components (WO-123) |
| **TD-124** | God Class: `TransactionProcessor` | Split into 6-Layer Architecture (WO-124) |
| **TD-105** | Positive Drift Mystery | Fixed via Reflux atomic transfer & closure check |
| **TD-106** | Bankruptcy Money Leak | Linked Bankruptcy to Settlement System |
| **TD-130** | Reflux System (Dark Pools) | Operation Sacred Refactoring (Purge Reflux) |
| **TD-131** | Monolithic TickScheduler | Decomposition into IPhaseStrategy steps |

---

## ℹ️ Minor (Monitor)

### [TD-107] CentralBank Asset Structure
- **내용**: `CentralBank`의 `assets`가 `float`가 아닌 `dict` 형태일 수 있다는 코드 흔적 발견.

---
*For full details, see the [Technical Debt Ledger](./TECH_DEBT_LEDGER.md).*
