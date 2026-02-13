# AUDIT_SPEC_ECONOMIC: Economic Purity Audit (v2.0)

**목표**: 시뮬레이션 내 모든 가치 이동이 '복식부기'의 원칙과 '화폐 보존의 법칙'을 준수하며, 원자성(Atomicity)이 보장되는지 검증한다.

## 1. 용어 정의 (Terminology)
- **Zero-Sum Violation**: 시스템 전체의 총 자산(Money Supply)이 거래나 에이전트 생성/소멸 과정에서 허공으로 증발하거나 생성되는 현상.
- **Transactional Atomicity**: 구매자의 차변(Debit)과 판매자의 대변(Credit)이 '동시에' 또는 '전혀 안 되게' 수행되어야 하는 일관성 원칙.
- **Reflux Completeness (회수 완전성)**: 세금, 수수료, 파산 자산이 소멸하지 않고 다시 시스템(정부/은행)으로 100% 흘러 들어가는 상태.

## 2. 논리 전개 (Logical Flow)
1. **Transfer Path Tracking**: `BaseAgent` 또는 컴포넌트 내에서 `assets` 필드를 직접 수정하는 모든 쓰기 연산을 추적한다.
2. **Double-Entry Verification**: `finance/` 모듈 내의 이체 로직(`transfer`)이 좌우 합산이 0이 되는지 수학적으로 검토한다.
3. **Lifecycle Audit**: 
   - 에이전트 탄생 시 자산의 출처(부모의 상속, 정부 보조금 등)가 명확한가?
   - 에이전트 소멸 시 자산의 목적지(`RefluxSystem`)가 명확히 지정되었는가?

## 3. 구체적 방법 예시 (Concrete Examples)
- **부정 사례 (Money Leak)**:
  ```python
  # BAD: 자산을 직접 더함 (시스템 통계 누락 및 원천 불명)
  self.assets += 100 
  ```
- **정상 사례 (Atomic Transfer)**:
  ```python
  # GOOD: 중앙화된 시스템을 통해 양자의 장부를 동시에 갱신
  FinanceSystem.transfer(from_agent=buyer, to_agent=seller, amount=price)
  ```

## 4. 구조의 검증 및 훈련 모듈 (Util Status)
- **Consistency Checks**: `tests/verification/verify_zero_sum.py`와 같은 구조적 검증 모듈이 실시간으로 활성화되어 있는가?
- **Data Integrity Util**: `fixture_harvester.py`를 통해 추출된 데이터 샘플에서 `total_assets`의 합계가 틱(Tick) 간에 일관성을 보이고 있는가?
- **Input/Output Data**: 경제적 무결성 감사 결과는 `LEAK_REPORT.json` 형태로 출력되어, 향후 AI 정부 요원(`Leviathan`)의 재정 정책 훈련 데이터로 활용될 수 있는가?

## 5. Output Configuration
- **Output Location**: `reports/audit/`
- **Recommended Filename**: `AUDIT_REPORT_ECONOMIC.md`
