# W-2 Work Order: ZeroDivisionError Hotfix

> **Assignee**: Jules  
> **Priority**: Critical  
> **Branch**: `hotfix/zero-division-error`  
> **Base**: `main`

---

## 📋 Issue Summary

1000틱 MVP 테스트 중 **ZeroDivisionError**가 발생하여 시뮬레이션이 중단됨.  
Brand Economy 로직(Phase 6)은 정상 작동하나, 기존 코드의 0으로 나누기 버그로 추정.

---

## 🔍 Evidence

### 정상 작동 확인 (에러 발생 전)
```
FIRM_BRAND_METRICS | Firm 20: Awareness=0.3723, Quality=0.9946, Premium=0.00
FIRM_BRAND_METRICS | Firm 21: Awareness=0.3723, Quality=1.2993, Premium=0.00
Production (Cobb-Douglas) for basic_food. Y=40.10 (A=10.68, L=1.2, K=54.0, α=0.70)
```

### 에러 발생
```
ZeroDivisionError: division by zero
```
정확한 위치는 터미널 출력 잘림으로 불확실.

---

## ✅ Tasks

### 1. Reproduce & Locate
1. `scripts/iron_test.py` 실행 (100틱으로 시작, 점진적 증가)
2. 에러 발생 시 정확한 스택 트레이스 확인
3. 에러 발생 파일 및 라인 번호 기록

### 2. Analyze Root Cause
**가능성 높은 원인들:**

| 파일 | 가능한 위치 | 이유 |
|------|------------|------|
| `engine.py` | `run_tick()` 내 보상 계산 | `total_shares` 또는 `assets`가 0일 때 |
| `firm_ai.py` | `calculate_reward()` | `firm.assets * 0.05` 분모 사용 시 |
| `core_agents.py` | `choose_best_seller()` | Utility 계산 시 `price = 0` |
| `government.py` | 세금/복지 계산 | GDP 또는 인구 0 |
| `order_book_market.py` | 평균가 계산 | 거래 0건 시 VWAP |

### 3. Fix & Validate
1. ZeroDivisionError 발생 지점에 방어 코드 추가
2. 예: `max(1, denominator)` 또는 `if denominator > 0` 체크
3. `scripts/iron_test.py` 1000틱 성공적으로 완료 확인

---

## 📐 Fix Pattern

```python
# Bad
result = numerator / denominator

# Good
result = numerator / max(0.01, denominator)
# OR
result = numerator / denominator if denominator > 0 else 0.0
```

---

## 🧪 Verification

1. `python scripts/iron_test.py` 실행
2. 1000틱 완료 시 **IRON TEST COMPLETE** 메시지 확인
3. `iron_test_summary.csv` 생성 확인

---

## 📁 Reference Files

- [iron_test.py](file:///c:/coding/economics/scripts/iron_test.py) - 테스트 스크립트
- [engine.py](file:///c:/coding/economics/simulation/engine.py) - 메인 시뮬레이션 루프
- [firm_ai.py](file:///c:/coding/economics/simulation/ai/firm_ai.py) - AI 보상 함수
- [government.py](file:///c:/coding/economics/simulation/agents/government.py) - 재정 정책

---

## ⚠️ Notes

- 방어 코드 추가 시 **경고 로그** 남길 것 (0으로 나누는 상황 발생 시 추적 가능하도록)
- 근본 원인이 데이터 무결성 문제라면 별도 이슈로 보고
