# Phase 1 Final Validation - The Crucible Test

## 1. 개요
**목표**: 금본위 모드(Gold Standard), 3-Pillars 모델, 투매(Fire Sale) 메커니즘이 통합된 환경에서 1000틱 장기 시뮬레이션을 수행하여 **경제의 안정성 및 자정 능력**을 검증한다.

## 2. 시뮬레이션 설정
- **모드**: `GOLD_STANDARD_MODE = True` (Full Reserve)
- **기간**: 1000 Ticks
- **참여 에이전트**: 모든 로직 (Reflux, 3-Pillars, Fire Sale) 활성화

## 3. 검증 항목 (Success Criteria)

### 3.1 버블 억제 (Anti-Bubble)
- 기업 수가 초기 대비 통제 불가능한 수준(예: 10배 이상)으로 폭증하지 않아야 함.
- 창업 자금 조달 실패(대출 거절 등)가 로그에 나타나야 함.

### 3.2 구조조정 (Creative Destruction)
- 수익성 악화 기업의 **투매(Fire Sale)** 및 **청산(Liquidation)** 이벤트가 발생해야 함.
- 청산 후 해당 자산(현금, 재고)이 가계나 다른 기업으로 재분배되어야 함.

### 3.3 화폐 보존 (Money Conservation)
- 시뮬레이션 시작부터 끝까지 `Money Supply Delta`는 `0.0000`이어야 함.

## 4. 제출물 (Deliverables)

Jules는 다음 결과물을 `reports/PHASE1_FINAL_REPORT.md` 및 첨부 파일로 제출해야 한다.

1. **시뮬레이션 요약 보고서 (`reports/PHASE1_FINAL_REPORT.md`)**
 - 기업 수 변화 추이 (시작 vs 끝)
 - 파산 및 청산 건수
 - 최종 인플레이션/디플레이션 여부 (가격 추이)
 - 화폐 보존 검증 결과

2. **주요 로그 발췌 (`reports/crucible_logs.txt`)**
 - `LOAN_REJECTED` (대출 거절) 샘플
 - `FIRE_SALE` (투매) 샘플
 - `FIRM_LIQUIDATION` (청산) 샘플
 - `MONEY_SUPPLY_CHECK` (화폐 보존 확인) 샘플

## 5. 실행 명령
```bash
python scripts/iron_test.py --num_ticks 1000
```
위 명령 실행 후 결과 데이터를 분석하여 보고서를 작성하라.
