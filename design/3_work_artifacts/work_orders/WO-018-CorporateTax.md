# Corporate Tax & Maintenance Fee Implementation

## 1. 개요
**목표**: 기업의 무분별한 증식과 좀비 존속을 억제하고, 청산(Liquidation) 과정에서의 화폐 생성 버그를 수정하여 경제 시스템의 무결성을 확보한다.

## 2. 구현 상세

### 2.1 Config Update (`config.py`)
```python
CORPORATE_TAX_RATE = 0.2 # 순이익의 20%
FIRM_MAINTENANCE_FEE = 50.0 # 틱당 고정 유지비
STARTUP_COST = 30000.0 # 창업 비용 상향 (기존 15,000)
```

### 2.2 Critical Bug Fix: Money Creation in Liquidation (`simulation/firms.py`)
> **ISSUE**: 현재 `liquidate_assets`에서 재고와 설비를 매각 처리하며 **구매자 없이 현금을 생성**하는 버그가 있음 (Money Printing).
- **FIX**: `liquidate_assets` 메서드를 수정하여:
 1. 재고(`inventory`) 및 설비(`capital_stock`)는 현금화하지 않고 **즉시 폐기(0원)** 처리한다.
 2. `inventory.clear()`, `capital_stock = 0.0`.
 3. 오직 `self.assets`(보유 현금)만 반환한다.

### 2.3 Firm Logic Update (`simulation/firms.py`)
1. **유지비 지불 (`pay_maintenance`)**:
 - 매 틱 `FIRM_MAINTENANCE_FEE`를 지불한다.
 - `self.assets -= fee`.
 - `config_module.government.collect_tax(fee, "firm_maintenance", ...)` 호출.

2. **법인세 지불 (`pay_taxes`)**:
 - `profit_this_tick = revenue - expenses` (유지비 포함)
 - `if profit_this_tick > 0`:
 - `tax = profit_this_tick * CORPORATE_TAX_RATE`
 - `self.assets -= tax`
 - `config_module.government.collect_tax(tax, "corporate_tax", ...)` 호출.

3. **`update` 메서드 수정**:
 - 기존 로직 마지막에 `pay_maintenance()`와 `pay_taxes()` 호출 추가.

### 2.4 Engine Update (`simulation/engine.py`)
1. **창업 로직 수정**:
 - `spawn_firm`에서 `startup_cost`를 `config.STARTUP_COST` (30000)로 사용.
 - `specializations` 리스트에 `"luxury_food"` 추가 (랜덤 선택 시 포함).

## 3. 검증 계획 (Verification)
`tests/verify_corporate_tax.py`를 작성하여 다음을 검증하라:

1. **Tax & Fee Test**:
 - 기업이 매출 발생 시 법인세를 납부하는지 확인.
 - 기업이 매출 0일 때 유지비를 납부하는지 확인.
2. **Conservation Test**:
 - 기업 청산(Liquidation) 시나리오를 강제로 실행하고, 전후 시스템 전체 화폐 총량(Delta)이 **0.0000**인지 확인.

## 4. 보고 요청
Jules는 구현 및 검증 후 `reports/CORPORATE_TAX_REPORT.md`를 제출하라.
