# Work Order: WO-054-Public-Education-System

**Date:** 2026-01-12
**Phase:** Phase 23 (The Great Expansion)
**Assignee:** Jules (Worker AI)
**Status:** APPROVED
**Objective:** 정부 주도의 공교육 시스템을 도입하여, (1) 계층 이동의 사다리를 복원하고, (2) 국가 전체의 기술 수용 능력(Absorptive Capacity)을 향상시킨다.

---

## 1. System Architecture: The "Brain" of the Economy

**Endogenous Growth Theory (내생적 성장이론)** 적용.
인적 자본(Human Capital) 투자를 통한 경제 효율 향상.

### A. Module Expansion: `Government`

* **New Method:** `run_public_education(agents)`
* **Key Metric:** `Average_Education_Level` (국가 평균 학력)

### B. Core Mechanics

#### 1. Free Basic Education (의무 교육)

| 항목 | 내용 |
|------|------|
| **Target** | `Education_Level` 0 → 1 (문맹 퇴치) |
| **기존** | 1단계 승급 비용 500 필요 (가난하면 불가) |
| **변경** | 정부가 `Government.budget`에서 비용 **전액 부담** |
| **Effect** | 극빈층 자녀도 최소한의 노동 능력 확보 |

#### 2. Meritocratic Scholarship (희망 사다리)

| 항목 | 내용 |
|------|------|
| **Target** | `Education_Level` 2+ 진입 시 |
| **조건** | 부모 자산 하위 20% + 높은 잠재력 (Hidden Trait) |
| **보조율** | 학비의 **80%** 정부 보조 |
| **Effect** | IGE 0.96 (완벽한 계층 고착화) 타파 |

#### 3. Human Capital & Tech Diffusion Feedback Loop

```
effective_diffusion_rate = base_diffusion_rate * (1 + 0.2 * (AvgEdu - 1.0))
```

* `AvgEdu > 1.0` → 기술 확산 속도 증가
* *의미:* 국민 학력 ↑ → 신기술(화학 비료, 증기기관) 채택 속도 ↑

---

## 2. Implementation Steps

### Step 1: Government.run_public_education()

```python
# simulation/agents/government.py

def run_public_education(self, agents: List[Household], config_module: Any) -> None:
    """의무 교육 및 장학금 집행"""
    budget_ratio = getattr(config_module, "PUBLIC_EDU_BUDGET_RATIO", 0.20)
    edu_budget = self.assets * budget_ratio
    
    for agent in agents:
        if not agent.is_active:
            continue
            
        # 1. Free Basic Education (Level 0 → 1)
        if agent.education_level == 0:
            cost = config_module.EDUCATION_COST_PER_LEVEL.get(1, 500)
            if edu_budget >= cost:
                agent.education_level = 1
                edu_budget -= cost
                self.assets -= cost
                
        # 2. Meritocratic Scholarship (Level 2+)
        elif agent.education_level >= 1:
            # Check: Bottom 20% wealth + High potential
            if self._is_scholarship_eligible(agent, agents):
                next_level = agent.education_level + 1
                cost = config_module.EDUCATION_COST_PER_LEVEL.get(next_level, 1000)
                subsidy = cost * 0.8  # 80% 보조
                if edu_budget >= subsidy:
                    agent.assets -= (cost - subsidy)  # 20% 자기 부담
                    agent.education_level = next_level
                    edu_budget -= subsidy
                    self.assets -= subsidy
```

### Step 2: TechnologyManager.set_human_capital_index()

```python
# simulation/systems/technology_manager.py

def set_human_capital_index(self, avg_education: float) -> None:
    """국가 평균 학력에 따른 확산율 조정"""
    self.human_capital_index = avg_education

def _get_effective_diffusion_rate(self, tech_id: str) -> float:
    """인적 자본 보정된 확산율 반환"""
    base_rate = self.technologies[tech_id].get("diffusion_rate", 0.1)
    hci = getattr(self, 'human_capital_index', 1.0)
    
    # Formula: effective_rate = base_rate * (1 + 0.2 * (AvgEdu - 1.0))
    return base_rate * (1 + 0.2 * (hci - 1.0))
```

### Step 3: Config 추가

```python
# config.py

# --- Phase 23: Public Education System (WO-054) ---
PUBLIC_EDU_BUDGET_RATIO = 0.20  # 정부 예산의 20%를 교육에 투자
EDUCATION_COST_PER_LEVEL = {
    1: 500,    # 기초 교육
    2: 2000,   # 중등 교육
    3: 5000,   # 고등 교육
    4: 15000,  # 대학
    5: 50000   # 대학원/전문직
}
SCHOLARSHIP_WEALTH_PERCENTILE = 0.20  # 하위 20%
SCHOLARSHIP_POTENTIAL_THRESHOLD = 0.7  # 잠재력 상위 30%
```

---

## 3. Verification Criteria

| 지표 | 기대값 | 검증 방법 |
|------|--------|-----------|
| **IGE (계층 이동성)** | 0.96 → **0.6~0.7** | `scripts/experiments/education_roi_analysis.py` |
| **기술 확산 속도** | AvgEdu↑ → Diffusion↑ | `TechnologyManager` 로그 확인 |
| **Positive Feedback Loop** | 학력↑ → 임금↑ → 세수↑ → 교육투자↑ | 500 tick 시뮬레이션 |

---

## 4. Dependencies

* **WO-053:** `TechnologyManager` (완료)
* **WO-049:** 상속 시스템 (완료)
* **WO-052:** Education ROI Analysis (완료)

---

## 5. Dispatch Command

> "Jules, 이제 에이전트들의 두뇌를 업그레이드할 시간이다. **공교육 시스템**을 구축하여 계층의 사다리를 복원하고, 인적 자본과 기술 확산의 피드백 루프를 가동하라. 맬서스의 굴레에서 벗어난 인류가 이제 **계몽(Enlightenment)**의 시대로 진입한다."

**Execute.**
