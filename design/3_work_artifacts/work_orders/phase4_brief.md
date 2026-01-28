# 📜 WORK ORDER: Phase 4 - The Welfare State

**To**: Jules (Lead Implementer)  
**From**: Antigravity (Assistant Architect)  
**Status**: 🟢 **READY FOR DEVELOPMENT**  
**Priority**: Highest (Critical for Stability)

---

## 🏛️ Context: The "Twin Pillars" Strategy

**Congratuations on Phase 3.** 
은행(Bank)과 금리(Interest) 시스템이 성공적으로 도입되었습니다. 하지만 이것은 엔진(Engine)만 달린 자동차와 같습니다.

지금 상태에서 시뮬레이션을 장기 실행하면:
1.  **Snowballing Inequality**: 부자는 이자소득으로 더 부자가 되고, 빈자는 빚더미에 앉습니다.
2.  **Liquidity Trap**: 부자가 돈을 안 쓰고 쌓아두면(Savings), 시장에 돈이 말라 경제가 멈춥니다.
3.  **Mass Starvation**: 실직한 가정은 즉시 아사(Starvation)하여 인구가 소멸합니다.

이제 **브레이크(Brakes)와 에어백(Airbag)**을 설치할 차례입니다. 그것이 바로 **"정부(Government)와 재정 정책(Fiscal Policy)"**입니다.

---

## 🎯 Objective: "The Invisible Hand Needs a Visible Heart"

당신의 임무는 **`fiscal_policy_spec.md`**를 완벽하게 구현하여 다음 3대 기능을 활성화하는 것입니다.

### 1. Progressive Tax (누진세)
- **Problem**: 틱당 0.005%의 부유세는 연 65% 몰수라는 계산 실수였습니다.
- **Fix**: `ANNUAL_WEALTH_TAX_RATE = 0.02` (연 2%)를 틱으로 환산하여 적용해야 합니다.
- **Logic**: 소득세도 '평균 소득'이 아닌 **'생존 비용(Survival Cost)'** 기준으로 징수하여, 불황기에도 빈민을 뜯어가는 일이 없어야 합니다.

### 2. Social Safety Net (사회 안전망)
- **Problem**: 실직 = 죽음.
- **Solution**: 
    - **실업 급여**: 구직 중인 실업자에게 `SURVIVAL_COST * 0.8` 지급.
    - **재난 지원금**: GDP 폭락 시 헬리콥터 머니 살포.

### 3. Bankruptcy Court (파산과 회생)
- **Problem**: 빚을 못 갚으면 영원히 고통받거나 그냥 사라짐.
- **Solution**: **Credit Jail System**.
    - 빚은 탕감해주되, **1년(100틱)간 대출 금지**.
    - **지능 하락(XP Penalty)**: "파산은 공짜 점심이 아니다"라는 것을 AI에게 각인.

---

## 🛠️ Implementation Steps

참조 문서: `design/specs/fiscal_policy_spec.md` (이미 Repo에 있음)

1.  **Config Update**: `config.py`에 Tax Brackets, Wealth Tax Rate(Annual), Welfare Ratios 추가.
2.  **Government Update**: `agents/government.py`에 `run_fiscal_policy()` 메서드 구현.
    - `run_tick()`에서 매번 호출.
    - 예산 부족 시 적자 재정(Deficit Spending -> Money Printing) 허용 여부 결정.
3.  **Bankruptcy Update**: `Bank` 클래스에 `process_default(agent)` 구현.
    - 자산 몰수 -> 빚 탕감 -> Credit Jail 등록.

---

## ✅ Definition of Done (검증 기준)
- [ ] 부유층(상위 10%)의 자산 증가 속도가 둔화되는가? (Gini Coefficient 체크)
- [ ] 대공황 시나리오에서 하위 20%의 사망률이 감소하는가? (Survival Rate 체크)
- [ ] 파산한 에이전트가 100틱 동안 대출을 못 받는가?

**"우리는 단순한 코드를 짜는 것이 아닙니다. 문명을 설계하는 것입니다."**  
진행하십시오.
