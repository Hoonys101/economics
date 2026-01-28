# W-11 Revised: Operation "Forensics" (법의학적 부검)

> **상태**: Draft
> **목표**: 에이전트 사망 원인을 정밀 분석(Autopsy)하여 경제 붕괴의 근본 원인(Root Cause)을 규명함.

## 1. 개요 (Overview)
현재 시뮬레이션에서 에이전트들이 대거 사망하며 경제가 붕괴(Vegetative State)하고 있습니다. 파라미터 튜닝만으로는 "부자 아빠 효과(초기 자금 빨)"인지 "시스템 안정성"인지 구분할 수 없습니다. 따라서 사망 시점에 "왜 죽었는가?"를 분류하는 정밀 로그 체계를 도입합니다.

## 2. 진단 분류 체계 (Diagnostic Taxonomy)

우리는 에이전트의 사망 원인을 다음 3가지 유형으로 분류합니다.

### Type A: 구조적 실업 (Structural Unemployment)
*   **증상**: 일하고 싶어 함 (Labor Offer > 0) + 일자리가 없음 (Market Vacancy ≈ 0).
*   **해석**: "기업 생태계 붕괴". 기업이 망했거나 고용 여력이 없음.

### Type B: 매칭 실패 및 자발적 실업 (Mismatch / Voluntary Unemployment)
*   **증상**: 일자리가 있음 (Market Vacancy > 0) + 매칭되지 않음.
*   **세부 원인**:
    *   **B-1 (배부름)**: 자산이 충분하여 노동 공급을 안 함 (Labor Offer = 0).
    *   **B-2 (학습 실패)**: "일하면 돈 번다"는 Q-Learning 연결 실패.
    *   **B-3 (임금 격차)**: 기업 제시 임금(Wage) < 가계 희망 임금(Reservation Wage).

### Type C: 소비 실패 (Consumption Failure / Starvation)
*   **증상**: 식량이 있음 (Market Inventory > 0) + 돈도 있음 (Has Cash) + 굶어 죽음.
*   **세부 원인**:
    *   **C-1 (학습 실패)**: "돈 쓰면 배부르다"는 Q-Learning 연결 실패.
    *   **C-2 (구매력 부족)**: 보유 현금 < 시장 가격 (Price > Cash).
    *   **C-3 (유통 마비)**: 시장에 물건이 아예 없음 (Inventory = 0).

## 3. 구현 요구사항 (Implementation Requirements)

### 3.1 `log_death_event` (신규 메서드)
`Household` 클래스 내 `die()` 메서드가 호출될 때, 다음 정보를 구조화하여 로깅해야 합니다.

```python
# simulation/core_agents.py (Pseudo-code)

def log_death_event(self, market_data, labor_market_data):
    death_report = {
        "agent_id": self.id,
        "tick": self.current_tick,
        "cause": "starvation",  # 현재는 거의 기아
        "assets_at_death": self.assets,
        "needs_status": self.needs,
        "last_labor_offer_tick": self.last_labor_offer_tick,
        "market_context": {
            "food_price": market_data["basic_food"].price,
            "food_inventory": market_data["basic_food"].inventory,
            "job_vacancies": labor_market_data.total_vacancies,
            "avg_wage": labor_market_data.avg_wage
        }
    }
    # 파일 또는 메모리에 저장
    DeathRegistry.record(death_report)
```

### 3.2 `ForensicsReport` (분석 리포트 생성기)
시뮬레이션 종료 후(또는 주기적으로), 수집된 `DeathRegistry` 데이터를 분석하여 3가지 유형으로 분류 통계를 냅니다.

*   **출력 형식**: `reports/AUTOPSY_REPORT.md`
*   **내용**:
    *   총 사망자 수
    *   Type A/B/C 비중
    *   사망자들의 평균 자산 분포

## 4. 실행 계획
1.  **로그 강화**: `Household.die()` 메서드에 로깅 로직 주입.
2.  **시뮬레이션 실행**: 기존 파라미터(복지 0, Low Cash) 유지. 100~200 틱 실행.
3.  **부검 리포트 생성**: 유형별 분류 결과 확인.

## 5. 검증 기준
*   `reports/AUTOPSY_REPORT.md`가 생성되어야 함.
*   사망 원인이 명확히 A, B, C 중 하나로 분류되어야 함 (모호한 경우 'Unknown' 처리).
