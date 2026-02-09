# 🧪 Scenario Cards: Social Phenomena Verification

> **목적**: 우리가 구현한 추상적 개념들이 실제 사회현상을 재현하는지 검증하기 위한 시나리오 카드 모음.

---

## SC-001: 여성 노동시장 참여율 (Female Labor Participation)

### 검증 대상 현상
산업화 이후 여성의 노동시장 참여율이 기술 발전(분유, 가전제품)과 함께 급증한 역사적 현상.

### 관련 추상 개념
| 구현체 | 역할 |
| :--- | :--- |
| `BioStateDTO.gender` | 에이전트 성별 (M/F) |
| `FORMULA_TECH_LEVEL` | 분유 기술 보급률 (0.0 ~ 1.0) |
| `home_quality_score` | 가전제품 보급 수준 |
| `decide_time_allocation()` | 가사/양육 시간 배분 결정 |

### 조작 변수 (Independent Variables)
- `FORMULA_TECH_LEVEL`: 0.0 (암흑기) vs 1.0 (현대)
- `home_quality_score`: 1.0 (기본) vs 2.0 (가전 보급)

### 관측 지표 (Dependent Variables / KPIs)
- 여성 에이전트 평균 노동 시간 (hours/day)
- 여성 에이전트 평균 소득 (vs 남성)
- 여성 에이전트 노동시장 진입률 (%)

### 검증 기준 (Success Criteria)
- `FORMULA = 0.0` 시: 여성 노동시간 < 남성의 50%
- `FORMULA = 1.0` 시: 여성 노동시간 ≈ 남성의 90%+

---

## SC-002: 출산율 저하 (Fertility Decline)

### 검증 대상 현상
선진국에서 소득과 주거비가 상승할수록 출산율이 하락하는 현상 (인구학적 전환).

### 관련 추상 개념
| 구현체 | 역할 |
| :--- | :--- |
| `decide_reproduction()` | NPV 기반 출산 결정 |
| `CHILD_MONTHLY_COST` | 자녀 양육 비용 |
| `OPPORTUNITY_COST_FACTOR` | 경력 단절 비용 계수 |
| `housing_price` | 주거비 압박 |

### 조작 변수
- `CHILD_MONTHLY_COST`: 500 (저비용) vs 2000 (고비용)
- `housing_price`: 초기값 x1 vs x3 (버블)

### 관측 지표
- 틱당 출산 이벤트 수
- 평균 출산 연령
- 자산 수준별 출산율 분포

### 검증 기준
- 양육비 4배 증가 시: 출산율 50%+ 감소
- 주거비 3배 증가 시: 출산율 30%+ 감소

---

## SC-003: 멜서스 함정 (Malthusian Trap)

### 검증 대상 현상
인구 증가가 식량 생산 증가를 초과하여 빈곤과 아사가 반복되는 전근대적 현상.

### 관련 추상 개념
| 구현체 | 역할 |
| :--- | :--- |
| `ProductionEngine.produce()` | 식량 생산 함수 |
| `fixed_land_factor` | ⚠️ **미구현** - 토지 고정 생산요소 |
| `TECH_HABER_BOSCH_ENABLED` | ⚠️ **미구현** - 비료 기술 해금 |
| `survival_need` | 기아 상태 추적 |

### 조작 변수
- `initial_population`: 50 vs 200
- `TECH_HABER_BOSCH_ENABLED`: False (18세기) vs True (20세기)
- `land_provision`: 고정값 100

### 관측 지표
- 인구 대비 식량 생산량 비율
- 아사(Starvation) 사망자 수
- 평균 실질 임금

### 검증 기준
- `HABER = False` + 인구 과다: 3세대 내 인구 붕괴 (고정 토지 제약에 따른 수확체감 발현)
- `HABER = True`: 비료(자본) 투입이 토지 생산성을 지수적으로 대체하여 임금 유지

### 🚧 필요 작업
> [Tier 2] **Land as SSoT**: 토지를 단순 상수가 아닌, 거래 불가능한 '자연 자본'으로 시스템에 등록.

---

## SC-004: 뱅크런 (Bank Run)

### 검증 대상 현상
금융기관에 대한 신뢰 붕괴로 인한 대규모 예금 인출 사태.

### 관련 추상 개념
| 구현체 | 역할 |
| :--- | :--- |
| `Bank.reserve_ratio` | 지급준비율 |
| `SocialStateDTO.trust_score` | 금융기관 신뢰도 |
| `SettlementSystem.withdraw` | 인출 처리 |

### 조작 변수
- `BANK_RESERVE_RATIO`: 0.05 (위험) vs 0.20 (안전)
- 강제 이벤트: 대형 대출 부도 발생

### 관측 지표
- 틱당 인출 요청 수
- 은행 유동성 잔고
- 뱅크런 발생 여부 (유동성 0 도달)

### 검증 기준
- 지급준비율 5% + 부도 이벤트: 10틱 내 뱅크런 발생

---

## SC-005: 베블린재 / 과시 소비 (Veblen Effect - Esteem Need)

### 검증 대상 현상
가격이 오를수록 수요가 증가하는 사치재 현상. 이는 단순한 과시가 아니라 **매슬로우의 '존경(Esteem)의 욕구'**인 사회적 신분 상승 욕구를 충족시키기 위한 합리적 투자로 해석됨.

### 관련 추상 개념
| 구현체 | 역할 |
| :--- | :--- |
| `SocialStateDTO.social_rank` | 신분 등급 (Esteem 지표) |
| `Agent.decision_engine` | 지위 유지를 위한 '투자성 소비' 결정 |
| `ESTEEM_NEED_SATISFACTION` | 사치재 소비가 존경 욕구에 기여하는 가중치 |

### 조작 변수
- `luxury_price`: x1 vs x3
- `social_mobility_difficulty`: 신분 상승의 난이도 (가점/감점 속도)

### 관측 지표
- 가격 상승 시 사치재 수요의 역탄력성 발생 여부
- 소비자가 획득하는 `social_rank`와 그에 따른 금융/정치적 이득

### 검증 기준
- 상품 가격이 지위 상징성(Signal)을 강화할 때, 가격 상승에도 불구하고 지위 유지를 위한 소비가 증가함.

---

## SC-006: 네트워크 효과 (Network Effects - Belonging Need)

### 검증 대상 현상
사용자 수가 늘어날수록 상품의 가치가 기하급수적으로 증가하는 현상. 이는 **매슬로우의 '사회적 소속감(Belonging)의 욕구'**를 충족시키기 위한 동기에서 창발됨.

### 관련 추상 개념
| 구현체 | 역할 |
| :--- | :--- |
| `Belonging_Need` | ⚠️ **기획 필요** - 소속감 욕구 변수 |
| `User_Base_Size` | 해당 상품/서비스의 총 사용자 수 |
| `Utility_Emergence` | 1:1 통신이 아닌 N:N 연결성에 따른 효용 창발 |

### 조작 변수
- `INITIAL_USER_SEED`: 초기 사용자 수
- `EXCLUSIVITY_PENALTY`: 소속되지 못했을 때 발생하는 소외 비용

### 관측 지표
- 임계점(Critical Mass) 도달 후의 폭발적 수요 증가
- 특정 표준(Standard)으로의 시장 쏠림 현상(Winner-take-all)

### 검증 기준
- 사용자 수가 증가함에 따라 개별 에이전트가 느끼는 '소외 비용'이 증가하여, 소속감을 얻기 위한 행동이 강제됨.

---

## 템플릿: 신규 시나리오 카드

```markdown
## SC-XXX: [현상 이름]

### 검증 대상 현상
[설명]

### 관련 추상 개념
| 구현체 | 역할 |
| :--- | :--- |

### 조작 변수
- 

### 관측 지표
- 

### 검증 기준
- 

### 🚧 필요 작업 (Optional)
> [Tier X] ...
```
