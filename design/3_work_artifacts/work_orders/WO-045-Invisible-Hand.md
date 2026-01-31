# Work Order: - The Invisible Hand (Market-Based Labor Share)

**Phase:** 21.6
**Priority:** HIGH
**Date:** 2026-01-11
**Architect Prime Directive:** Rule-Based 가드레일 제거, 순수 시장 메커니즘으로 노동분배율 수렴

---

## 1. Problem Statement

현재 노동분배율 56.88%는 **하드코딩 가드레일**로 달성됨:
- `LABOR_ELASTICITY_MIN = 0.3` (강제)

이것은 **커브 피팅**이지, 시스템의 자연 균형이 아님.

**진짜 질문:**
> "왜 현실 세계에서 자본가의 탐욕에도 불구하고 노동분배율이 50-60%를 유지하는가?"

---

## 2. Objective

**가드레일 없이 시장 메커니즘만으로 노동분배율 30%+ 달성**

---

## 3. Target Metrics

| Metric | Current (Guardrail) | Target (Market) |
|---|---|---|
| Labor Share | 56.88% (강제) | **30%+** (자연) |
| Mechanism | Rule-Based | Market-Based |
| `LABOR_ELASTICITY_MIN` | 0.3 | **0.0** |

---

## 4. 3가지 시장 메커니즘

### Mechanism 1: Reservation Wage (정보 기반 거부)
**현재:** 굶으면 어떤 임금이든 수락
**변경:** 노동자가 시장 평균 임금을 알고, 너무 낮으면 거부

```python
# ActionProposalEngine._propose_sell_labor
market_avg_wage = market_data.get("labor", {}).get("avg_wage", 10.0)
firm_profitability = market_data.get("avg_firm_profit", 0.0)

# 시장 평균의 70% 미만이면 거부
if offered_wage < market_avg_wage * 0.7:
 return None # 노동 공급 거부
```

### Mechanism 2: Competitive Bidding (임금 경쟁)
**현재:** 기업이 임금 고정
**변경:** 기업들이 노동자 확보를 위해 경쟁 입찰

```python
# CorporateManager._manage_hiring
# 노동 부족 시 임금 인상
labor_scarcity = demand / supply
offer_wage = base_wage * (1.0 + (labor_scarcity - 1.0) * 0.5)
```

### Mechanism 3: Poaching (이직 활성화)
**현재:** 이직 비활성
**변경:** 더 높은 임금 제안 시 즉시 이직

```python
# engine.py - 매 틱
for employed_hh in employed_households:
 best_offer = labor_market.get_best_bid()
 if best_offer > employed_hh.current_wage * 1.1:
 employed_hh.switch_employer(best_offer)
```

---

## 5. Implementation Plan

### Track A: Reservation Wage (1st Priority)
1. `config.py` - 가드레일 제거: `LABOR_ELASTICITY_MIN = 0.0`
2. `simulation/decisions/action_proposal.py` - 시장 정보 기반 거부 로직

### Track B: Competitive Bidding (2nd Priority)
1. `simulation/decisions/corporate_manager.py` - 노동 희소성 기반 임금 조정

### Track C: Poaching (3rd Priority)
1. `simulation/engine.py` - 이직 메커니즘

---

## 6. Verification

```bash
# 가드레일 제거 후 테스트
python scripts/iron_test.py --ticks 100
```

**Success Criteria:**
- Labor Share > 30% (가드레일 없이)
- Wage Growth > 0 (상승 추세)
- 자연 균형점 관측

---

## 7. Experiment Design

| 실험 | 설정 | 측정 |
|---|---|---|
| Baseline | 가드레일 제거만 | 자연 하락점 측정 |
| +Reservation | Track A 추가 | 노동 공급 탄력성 |
| +Bidding | Track A+B | 임금 상승 효과 |
| +Poaching | All | 최종 균형점 |

---

## 8. Jules Assignment

| Track | Task | Complexity | 파일 |
|---|---|---|---|
| **A** | Reservation Wage | 낮음 | `action_proposal.py` |
| **B** | Competitive Bidding | 중간 | `corporate_manager.py` |
| **C** | Poaching | 높음 | `engine.py` |

**순차 실행 권장:** A → 테스트 → B → 테스트 → C → 테스트
