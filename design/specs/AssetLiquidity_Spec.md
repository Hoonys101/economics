이것은 `AssetLiquiditySystem`을 위한 상세 명세서와 인터페이스 초안입니다.

**작업 요약:**
1.  **`modules/liquidity/api.py`**: 자산 유동화 시스템의 인터페이스 및 DTO 정의.
2.  **`design/specs/liquidity_spec.md`**: 유동성 평가 및 강제 청산(Liquidation) 로직을 포함한 상세 설계서.

---

### 1. `modules/liquidity/api.py`

```python
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any

# ------------------------------------------------------------------------------
# Enums
# ------------------------------------------------------------------------------

class AssetType(Enum):
    CASH = "CASH"
    DEPOSIT = "DEPOSIT"
    STOCK = "STOCK"
    INVENTORY = "INVENTORY"
    REAL_ESTATE = "REAL_ESTATE"

class LiquidationPriority(Enum):
    """청산 우선순위 전략"""
    LEAST_LOSS = "LEAST_LOSS"       # 손실이 가장 적은 자산부터 (보통 현금 -> 주식)
    FASTEST = "FASTEST"             # 현금화가 가장 빠른 자산부터
    FIRE_SALE = "FIRE_SALE"         # 긴급 처분 (할인율 적용 감수)

# ------------------------------------------------------------------------------
# DTOs
# ------------------------------------------------------------------------------

@dataclass
class AssetValuationDTO:
    """개별 자산군의 가치 평가 결과"""
    asset_type: AssetType
    item_id: Optional[str]          # 재고 ID 또는 기업 ID, 부동산 ID
    quantity: float
    unit_price: float               # 현재 시장가
    valuation: float                # 총 평가액 (qty * price)
    liquidity_score: float          # 0.0 (비유동) ~ 1.0 (즉시 현금)
    haircut_rate: float             # 급매 시 예상 할인율 (0.0 ~ 1.0)

@dataclass
class LiquiditySnapshotDTO:
    """에이전트의 전체 유동성 상태 스냅샷"""
    agent_id: int
    tick: int
    total_assets_value: float       # 총 자산 가치
    liquid_assets_value: float      # 즉시 가용 유동성 (Cash + Deposits)
    illiquid_assets_value: float    # 비유동 자산 가치
    solvency_ratio: float           # 지급여력 비율 (Liquid / Total Liabilities)
    details: List[AssetValuationDTO]

@dataclass
class LiquidationRequestDTO:
    """자산 현금화 요청"""
    requester_id: int
    target_amount: float            # 확보 목표 금액
    priority: LiquidationPriority = LiquidationPriority.LEAST_LOSS
    allowed_asset_types: List[AssetType] = field(default_factory=lambda: [
        AssetType.DEPOSIT, AssetType.STOCK, AssetType.INVENTORY
    ])

@dataclass
class LiquidationResultDTO:
    """현금화 실행 결과"""
    success: bool
    amount_raised: float
    remaining_deficit: float        # 목표 금액 대비 부족분
    items_sold: List[Dict[str, Any]] # {"item_id": str, "qty": float, "price": float}
    transaction_logs: List[Any]     # 생성된 Transaction 객체 리스트 (후처리용)

# ------------------------------------------------------------------------------
# Interfaces
# ------------------------------------------------------------------------------

class ILiquiditySystem(ABC):
    """
    Asset Liquidity System Interface.
    Centralized hub for valuing assets and executing conversions to cash.
    """

    @abstractmethod
    def assess_liquidity(self, agent_id: int, agents_ref: Dict[int, Any], markets_ref: Dict[str, Any]) -> LiquiditySnapshotDTO:
        """
        특정 에이전트의 자산을 평가하고 유동성 스냅샷을 반환합니다.
        
        Args:
            agent_id: 대상 에이전트 ID
            agents_ref: 전체 에이전트 참조 (자산 접근용)
            markets_ref: 전체 시장 참조 (가격 조회용)
        """
        pass

    @abstractmethod
    def execute_liquidation(
        self, 
        request: LiquidationRequestDTO, 
        agents_ref: Dict[int, Any], 
        markets_ref: Dict[str, Any],
        current_tick: int
    ) -> LiquidationResultDTO:
        """
        요청된 금액만큼 자산을 매각하여 현금화합니다.
        
        Note:
            - 시장에 즉시가(Market Sell) 주문을 내거나, 시스템이 인수(Burn) 처리합니다.
            - 시장 깊이가 부족할 경우 Haircut(할인)이 적용될 수 있습니다.
        """
        pass

    @abstractmethod
    def check_withdrawal_limit(self, agent_id: int, amount: float, bank_ref: Any) -> bool:
        """
        은행의 인출 제한(Bank Run 방지)을 확인합니다.
        """
        pass
```

---

### 2. `design/specs/liquidity_spec.md`

```markdown
# Spec: Asset Liquidity System (ALS)

## 1. 개요 (Overview)
**Asset Liquidity System (ALS)**는 시뮬레이션 내 존재하는 다양한 형태의 자산(현금, 예금, 주식, 부동산, 재고)을 통합적으로 평가하고, 필요 시 이를 **현금(Cash)**으로 전환하는 중앙화된 메커니즘을 제공합니다. 이는 에이전트가 파산 위기에 처하거나 긴급 자금이 필요할 때 수행하는 '자산 유동화' 과정을 체계화합니다.

## 2. 목표 (Goals)
1.  **통합 가치 평가**: 시장 가격을 기반으로 에이전트의 실질적인 지급 여력(Solvency)을 계산합니다.
2.  **자동화된 청산 (Waterfall)**: 유동성이 높은 자산부터 순차적으로 매각하는 로직을 표준화합니다.
3.  **시장 충격 완화**: 대량 매각 시 시장 가격 붕괴를 반영하거나(Slippage), 급매 할인(Haircut)을 적용합니다.

## 3. 데이터 구조 (Data Structures)

### 3.1 Valuation Hierarchy (가치 평가 계층)
자산별 유동성 점수(`liquidity_score`)와 할인율(`haircut_rate`)은 `config.py`에서 정의된 상수를 따릅니다.

| 자산 유형 | 가치 산정 기준 | 유동성 점수 | 기본 할인율 (Haircut) |
| :--- | :--- | :--- | :--- |
| **CASH** | 1.0 | 1.0 | 0.0% |
| **DEPOSIT** | Bank Balance | 1.0 | 0.0% (단, 인출 한도 내) |
| **STOCK** | `Market Price` (Last Traded) | 0.8 | 1.0% + Slippage |
| **INVENTORY** | `Market Price` * 0.8 | 0.5 | 20.0% (Fire Sale) |
| **REAL_ESTATE** | `Estimated Price` | 0.1 | 30.0% ~ 50.0% |

### 3.2 DTO Mapping
*   `modules/liquidity/api.py`에 정의된 `LiquiditySnapshotDTO`와 `LiquidationResultDTO`를 엄격히 준수합니다.

## 4. 핵심 로직 (Core Logic)

### 4.1 Liquidity Assessment (유동성 평가) (`assess_liquidity`)
1.  **Context Loading**: `agents_ref`를 통해 대상 에이전트 객체에 접근합니다.
2.  **Asset Iteration**:
    *   `cash`: 에이전트의 `assets` 속성.
    *   `stocks`: `shares_owned` 딕셔너리 순회 -> `StockMarket`에서 현재가 조회 -> 가치 합산.
    *   `inventory`: `inventory` 딕셔너리 순회 -> `Market`에서 평균가 조회 -> 가치 합산.
    *   `real_estate`: `owned_properties` 순회 -> `RealEstateUnit.estimated_value` 합산.
3.  **Aggregation**: 자산군별로 합산하여 `LiquiditySnapshotDTO` 생성.

### 4.2 Liquidation Waterfall (청산 워터폴) (`execute_liquidation`)
요청된 `target_amount`를 달성할 때까지 다음 순서로 자산을 매각합니다.

#### **Phase 1: Cash & Deposits**
*   **동작**: 은행 예금 인출 (`Bank.withdraw`).
*   **제약**: 은행의 지급준비율이나 인출 한도(`check_withdrawal_limit`) 확인.

#### **Phase 2: Securities (Stocks)**
*   **동작**: 보유 주식을 시장가로 매도 (`OrderType="SELL"`).
*   **로직**:
    *   `LiquidationPriority.LEAST_LOSS`: 손실이 가장 적거나, 수익률이 높은 주식부터 매도? (단순화를 위해 보유량이 많은 순서 또는 랜덤)
    *   **Market Interaction**: `StockMarket.place_order` 호출. 즉시 체결되지 않을 경우를 대비해, ALS는 `MarketMaker` 역할을 수행하여 **할인된 가격으로 즉시 인수(Absorption)** 후 시장에 천천히 풀 수도 있음 (또는 단순히 시장가 주문 후 체결된 만큼만 현금화).
    *   **단순화 모델**: 시장가 주문을 내고, 해당 틱에 체결된 금액을 반환.

#### **Phase 3: Inventory (Fire Sale)**
*   **동작**: 상품 시장에 "급매" 주문.
*   **가격 책정**: 시장 평균가(`avg_price`) * `(1.0 - FIRE_SALE_DISCOUNT)`.
*   **처리**: ALS가 즉시 소각(Destroy) 처리하고 현금을 주입하거나(정부 구제금융 방식), 시장 최저가로 매도 주문을 냄.
    *   *프로젝트 규칙 준수*: "Money Creation from thin air" 금지. 따라서 시장에 매도 주문을 내고 **체결된 만큼만** 현금화하는 것이 원칙.
    *   *예외*: `LiquidationPriority.FIRE_SALE` 모드에서는 시스템(Reflux System)이 50% 가격에 즉시 인수 가능 (옵션).

### 4.3 Withdrawal Limits (`check_withdrawal_limit`)
*   은행 런(Bank Run) 시나리오를 방지하기 위해 틱당 인출 한도를 둡니다.
*   `Limit = Min(RequestAmount, Bank.assets * 0.1)` (은행 총 자산의 10% 이상 인출 불가 등).

## 5. 예외 처리 (Error Handling)

*   **`InsufficientAssetsException`**: 모든 자산을 매각해도 목표 금액에 도달하지 못할 때 발생. 이 경우 `LiquidationResultDTO.success = False`를 반환하고, 확보된 금액만큼만 반환합니다.
*   **`MarketClosedException`**: 시장이 열리지 않아 매각이 불가능한 경우 (주식/부동산).

## 6. 통합 가이드 (Integration Guide)

*   **Bank Integration**: 대출 상환 기일이 지났을 때, Bank는 `ALS.execute_liquidation(borrower_id, debt_amount)`를 호출하여 강제 징수합니다.
*   **Firm Decision**: 기업이 파산을 면하기 위해 스스로 `ALS`를 호출하여 구조조정을 단행할 수 있습니다.
*   **Government**: 세금 체납 시 ALS를 통해 강제 징수합니다.

---

### 📢 Mandatory Reporting (Jules Instructions)
이 모듈을 구현하거나 사용할 때 발견되는 다음 사항들을 반드시 `communications/insights/`에 기록하십시오:
1.  **Liquidity Trap**: 자산은 많으나 시장 유동성이 없어 현금화에 실패하는 빈도.
2.  **Fire Sale Impact**: 급매가 시장 가격을 얼마나 폭락시키는지(Slippage)에 대한 관찰.
3.  **Code Optimization**: 자산 평가 로직(`assess_liquidity`)이 틱마다 호출될 경우의 성능 저하 여부.
```
