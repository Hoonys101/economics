# 🔍 PR Review: PH9.2 Firm & Core Protocol Enforcement

## 🔍 Summary

본 변경 사항은 시스템 전반의 아키텍처 일관성을 강화하는 데 중점을 둡니다. 여러 곳에 중복 정의되었던 `OrderDTO`를 `modules/market/api.py`의 정의로 통합하여 단일 진실 공급원(SSOT) 원칙을 확립했습니다. 또한, `Firm` 및 `Household` 에이전트가 `_inventory` 속성에 직접 접근하던 관행을 제거하고, `IInventoryHandler` 프로토콜 인터페이스(`get_all_items`, `get_quantity` 등)를 사용하도록 강제하여 캡슐화와 프로토콜 순수성을 확보했습니다.

## 🚨 Critical Issues

**None.**
- API 키, 비밀번호, 시스템 절대 경로 등 보안에 민감한 정보의 하드코딩이 발견되지 않았습니다.
- 외부 레포지토리 참조와 같은 Supply Chain Attack 위험 요소는 없습니다.

## ⚠️ Logic & Spec Gaps

- **Interface Contract Change**: `simulation/firms.py`의 `FinanceProxy` 내부 클래스에서 `get_book_value_per_share`, `calculate_valuation` 메소드의 반환 값이 `float`에서 `{'amount': ..., 'currency': ...}` 형태의 `Dict`로 변경되었습니다. 이는 데이터의 명확성을 높이는 긍정적인 변화이지만, 이 프록시를 사용하는 다른 컴포넌트가 있을 경우 호환성 문제가 발생할 수 있는 'breaking change'에 해당합니다. 이번 PR의 범위 내에서는 문제가 없으나, 변경의 영향도를 인지해야 합니다.
- **Unrelated Test Change**: `tests/unit/test_stock_market.py`의 `StockMarket` 생성자에 `shareholder_registry` 모의(Mock) 객체를 추가하는 변경 사항은 본 PR의 핵심 주제인 '프로토콜 강제'와 직접적인 관련이 없습니다. 커밋의 원자성(atomicity)을 해치므로 별도의 PR로 분리하는 것이 이상적입니다.

## 💡 Suggestions

- **DTO Refactoring Follow-up**: 인사이트 보고서에서 정확히 지적했듯이, `OrderDTO` 내에 `monetary_amount: Optional[MoneyDTO]`와 `currency: CurrencyCode`가 공존하는 것은 기술 부채입니다. 이는 주문 유형(내부 투자 vs. 시장 주문)에 따라 다른 필드를 사용하는 것으로 보이며, 장기적으로는 단일화된 `MoneyDTO` 객체로 통합하여 표현의 일관성을 확보해야 합니다.

## 🧠 Implementation Insight Evaluation

- **Original Insight**:
```markdown
# PH9.2 Firm & Core Protocol Enforcement Report

## 1. Problem Phenomenon
- **Conflicting OrderDTO Definitions**: `OrderDTO` was defined in three different places (`modules/market/api.py`, `simulation/dtos/api.py`, `simulation/api.py`) with inconsistent fields (e.g., `currency` present in one but not others, `side` missing in some). This created ambiguity and potential type errors.
- **Protocol Bypass in Agents**:
    - `Firm` agent directly accessed `self._inventory` (a `BaseAgent` implementation detail) in methods like `liquidate_assets`, `calculate_valuation`, etc., violating the `IInventoryHandler` protocol.
    - `Household` agent bypassed encapsulation by aliasing `self._inventory = self._econ_state.inventory` in `__init__`, exposing internal state to the base class structure inappropriately.

## 2. Root Cause Analysis
- **Code Duplication**: `OrderDTO` was redefined in "public API" files (`simulation/api.py`) instead of being imported from the canonical source, leading to drift over time (e.g., Phase 33 updates applied only to one copy).
- **Inheritance vs Composition**: `Firm` inherits from `BaseAgent`, which exposes `_inventory` as a protected attribute. Developers naturally used it directly instead of the public protocol methods (`get_quantity`, `get_all_items`).
- **Legacy Patterns**: The `Household` alias was a legacy workaround to make `BaseAgent` methods work with `EconStateDTO`, but it broke the "pure state" abstraction.

## 3. Solution Implementation Details

### 3.1 OrderDTO Standardization
- **Central Source of Truth**: Established `modules.market.api.OrderDTO` as the canonical definition (aliased as `simulation.models.Order`).
- **Unified Imports**: Replaced local class definitions in `simulation/dtos/api.py` and `simulation/api.py` with aliases to `simulation.models.Order`.
- **Field Updates**: Added `currency: CurrencyCode = DEFAULT_CURRENCY` to the canonical `OrderDTO` to support Phase 33 requirements and standardize usage.

### 3.2 Firm Protocol Enforcement
- Refactored `Firm` methods (`liquidate_assets`, `get_agent_data`, `calculate_valuation`, `get_financial_snapshot`, `generate_transactions`, `clone`) to use `IInventoryHandler` methods:
    - Replaced `self._inventory.keys()` with `self.get_all_items().keys()`.
    - Replaced `self._inventory.items()` with `self.get_all_items().items()`.
    - Replaced `self._inventory.copy()` with `self.get_all_items()`.
- This ensures `Firm` logic is decoupled from the underlying storage mechanism of inventory.

### 3.3 Household Protocol Enforcement
- Removed the `self._inventory = self._econ_state.inventory` alias in `Household.__init__`.
- Updated `make_decision` to pass `self.get_all_items()` to the social component instead of raw state access.
- Confirmed `Household` overrides all `IInventoryHandler` methods, making the `BaseAgent._inventory` attribute effectively unused and irrelevant, which is cleaner.

## 4. Lessons Learned & Technical Debt
- **DTO Centralization**: DTOs should never be redefined for "convenience". Use imports or strictly typed aliases.
- **Protocol Usage**: When inheriting from a base class that implements a protocol (like `BaseAgent` implements `IInventoryHandler`), subclasses should strictly adhere to the protocol interface even for internal logic where possible, to facilitate future refactoring (e.g., changing storage backend).
- **Redundancy**: `OrderDTO` now contains both `currency` and `monetary_amount` (Optional). `monetary_amount` is used for internal firm orders (`INVEST_...`), while `currency` is used for market orders. Future refactoring should merge these into a single consistent monetary representation.
```
- **Reviewer Evaluation**:
  - **정확성**: 보고서는 실제 코드 변경 사항과 완벽하게 일치하며, 문제 현상(`OrderDTO` 중복, 프로토콜 위반)을 정확히 기술하고 있습니다.
  - **깊이**: '상속 vs. 구성'의 관점에서 `BaseAgent`의 `_inventory` 직접 접근 원인을 분석한 점은 매우 통찰력 있습니다. 이는 단순한 실수 지적을 넘어 구조적 문제의 근본 원인을 파고든 훌륭한 분석입니다.
  - **가치**: DTO 중앙화 및 프로토콜 인터페이스 준수라는 교훈은 프로젝트의 유지보수성과 확장성에 직접적으로 기여하는 핵심 원칙입니다. 스스로 새로운 기술 부채(`currency`와 `monetary_amount` 필드)를 식별하고 기록한 점은 매우 모범적입니다.

## 📚 Manual Update Proposal

- **Target File**: `design/2_operations/ledgers/ARCHITECTURAL_PATTERNS.md`
- **Update Content**: 아래 내용을 "Protocol Adherence" 섹션에 추가할 것을 제안합니다.

```markdown
### [PATTERN-017] Protocol Adherence over Implementation Inheritance

**Context:** An agent (`Firm`) inheriting from a base class (`BaseAgent`) was directly accessing a protected attribute (`_inventory`) of the base class. The base class itself was implementing a public protocol (`IInventoryHandler`) for inventory access.

**Problem:** This direct access couples the agent's logic to the base class's specific implementation details, making future refactoring (e.g., changing the inventory's data structure) brittle and error-prone. It violates the principle of depending on abstractions, not concretions.

**Solution:** Refactor the agent to exclusively use the methods defined in the `IInventoryHandler` protocol (`get_all_items()`, `get_quantity()`, etc.) for all its internal logic.

**Lesson:** When a class hierarchy involves protocols, child classes should **always** prefer interacting with the instance through the protocol interface, even for its "own" inherited state. This ensures that the logic is decoupled from the implementation and respects architectural boundaries.
```

## ✅ Verdict

**APPROVE**

필수 사항인 인사이트 보고서가 충실하게 작성되었으며, 코드 변경 사항이 시스템의 아키텍처 건전성을 크게 향상시킵니다. 지적된 사소한 문제들은 변경을 반려할 정도는 아니므로 승인합니다.