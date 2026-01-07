# WO-018: Corporate Tax & Maintenance Fee Implementation

## 1. 개요
**목표**: 기업의 무분별한 증식과 좀비 존속을 억제하기 위해 비용 구조를 강화한다.

## 2. 구현 상세

### 2.1 Config Update (`config.py`)
```python
CORPORATE_TAX_RATE = 0.2  # 순이익의 20%
FIRM_MAINTENANCE_FEE = 50.0  # 틱당 고정 유지비
STARTUP_COST = 30000.0  # 창업 비용 상향 (기존 15,000)
```

### 2.2 Firm Logic (`simulation/firms.py`)
1. **유지비 지불 (`pay_maintenance`)**:
   - 매 틱 `FIRM_MAINTENANCE_FEE`를 지불한다.
   - 현금 부족 시 화폐 보유량을 0으로 만들고, 부족분은 일단 무시(파산 로직에서 처리됨).
   - 지불된 금액은 정부(`government.collect_tax`)로 귀속 (항목: `firm_maintenance`).

2. **법인세 지불 (`pay_taxes`)**:
   - `profit_this_tick = revenue - expenses` (유지비 포함)
   - `if profit_this_tick > 0`:
     - `tax = profit_this_tick * CORPORATE_TAX_RATE`
     - 정부에 납부 (항목: `corporate_tax`).

3. **`update` 메서드 수정**:
   - 기존 로직 마지막에 `pay_maintenance()`와 `pay_taxes()` 호출 추가.

### 2.3 Engine Update (`simulation/engine.py`)
1. **창업 로직 수정**:
   - `spawn_firm`에서 `startup_cost`를 `config.STARTUP_COST` (30000)로 사용.
   - `luxury_food`도 창업 분야에 추가 (랜덤 선택 리스트 확장).

## 3. 검증 계획
1. **단위 테스트**: `tests/verify_corporate_tax.py` 작성.
   - 고정비 차감 확인.
   - 이익 발생 시 법인세 차감 확인.
2. **효과 검증**:
   - 100틱 시뮬레이션 후 기업 수 증가 추세가 완화되었는지 확인.

## 4. 보고 요청
Jules는 구현 후 `reports/CORPORATE_TAX_REPORT.md`를 제출하라.
