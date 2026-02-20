# Mission 4.1-A: AI Information Asymmetry & Sensitivity Planning

> [!IMPORTANT]
> **To: Senior Architect (Prime)**  
> **Subject: Detailed Proposal for Composite AI Intelligence (Asymmetry & Sensitivity)**

## 1. 개요 (Overview)
현실 경제의 '정보 비대칭성'과 '심리적 반응의 이질성'을 구현하기 위해, 새로운 속성을 추가하는 대신 기존 **기초 속성(Education, Wealth, Age)**을 조합하여 에이전트별 인지 모델을 차별화합니다.

## 2. 설계 방식 (Design Patterns - [VERDICT ADOPTED])

### 2.1 동적 통찰력 엔진 (The Dynamic Insight Engine)
'학력'이라는 정적 지표를 폐기하고, 에이전트의 경험과 학습에 의해 요동치는 **'Market Insight (시장 통찰력)'**를 핵심 변수로 도입합니다.

#### **3대 업데이트 메커니즘 (The 3 Pillars of Insight)**
1. **실전 학습 (Active Learning):** RL 루프의 `TD-Error` 절댓값에 비례해 Insight 경험치 획득. "실패와 성공을 통해 깨달음."
2. **서비스 소비 (Service Boosting):** '교육/컨설팅' 서비스 구매 시 Insight 즉시 부스팅.
3. **망각 곡선 (Decay):** 매 틱 일정 비율($\delta$)로 Insight 감소 ($I_{t+1} = I_t + \Delta Q + \Delta S - \delta$).

#### **인지 필터 의사코드 (Perception Filter Pseudo-code)**
```python
def _filter_macro_context(self, context: DecisionContext):
    insight = context.state.market_insight 
    policy = context.government_policy
    
    if insight > 0.8:
        # Smart Money: 실시간 데이터 (0-Tick Lag)
        context.perceived_debt_ratio = policy.debt_ratio
    elif insight > 0.3:
        # Laggards: 3틱 이동평균 (추세 오판)
        context.perceived_debt_ratio = self.history.get_moving_average('debt_ratio', window=3)
    else:
        # Lemons: 5틱 전 과거 데이터 + 5% 가우시안 노이즈 (공포와 관성)
        past_val = self.history.get_offset('debt_ratio', -5)
        noise = random.gauss(mu=1.0, sigma=0.05)
        context.perceived_debt_ratio = past_val * noise
```

### 2.3 노동 시장 고도화 (Labor Market Re-architecture: "Market for Lemons")
- **Utility-Priority Matching**: `Value = Perception(Productivity | Insight) / Wage`
- **Signaling Game**: 구직자는 `education_level`을 신호로 보내고, 고통찰력 기업은 이를 정확히 간파하나 저통찰력 기업은 '레몬'을 비싸게 채용함.

### 2.4 군집 행동 및 패닉 전파 (Herd Behavior & Panic Index)
개별 에이전트 간의 직접 통신 대신, 시장의 거시적 공포를 지표화하여 전파합니다.

- **Panic Index ($PI$):** 매 틱 `Total_Withdrawals / Total_Deposits`를 계산하여 0.0~1.0 사이의 값으로 산출.
- **가중치 로직 (Utility Weighting):**
  - **고통찰력 ($I > 0.8$):** 의사결정 시 펀더멘털($F$) 가중치 높음 (예: $U = 0.9F + 0.1PI$).
  - **저통찰력 ($I < 0.3$):** 펀더멘털보다 패닉 지수($PI$)에 민감하게 반응 (예: $U = 0.3F + 0.7PI$).
- **효과:** 지표가 소폭 꺾였을 때 '스마트 머니'가 소리 없이 빠져나가면, 뒤늦게 이를 `Panic Index`로 인지한 군중이 투매를 시작하며 뱅크런(Bank Run) 시나리오 창발.

## 3. 구현 세부 명세 (Technical Specifications)

### 3.1 AITrainingManager 연동
- `AITrainingManager`의 `run_learning_cycle`에서 각 에이전트의 `market_insight`를 업데이트하는 Hook 추가.

### 3.2 뱅크런(Bank Run) 및 공포 전파
- **Market Panic Index**: `WithdrawalVolume / TotalDeposits` 비율을 `GovernmentPolicyDTO`를 통해 매 틱 브로드캐스트.
- 통찰력이 낮은 에이전트일수록 펀더멘털보다 `panic_index`에 높은 가중치를 비중을 두어 투매(Sell-off)를 결정.

### DTO 확장
```python
@dataclass
class GovernmentPolicyDTO:
    income_tax_rate: float
    # ... 기존 필드
    system_debt_to_gdp_ratio: float  # 추가
    market_panic_index: float        # 추가 (0.0 ~ 1.0)
    system_liquidity_index: float    # 추가
    fiscal_stance_indicator: str     # "STABLE", "SOS", "AUSTERITY"
```

---
**Verified by**: Antigravity
**Timestamp**: 2026-02-20
