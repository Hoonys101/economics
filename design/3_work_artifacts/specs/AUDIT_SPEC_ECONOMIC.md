# AUDIT_SPEC_ECONOMIC: Economic Integrity Audit (v3.0)

**목표**: 시뮬레이션 내 모든 가치 이동이 '복식부기'의 원칙과 '화폐 보존의 법칙'을 준수하며, 원자성(Atomicity)이 보장되는지 검증한다.

**관심사 경계 (SoC Boundary)**:
> 이 감사는 오직 **"화폐의 수학(Financial Math)"**만을 다룬다.
> - ✅ Zero-Sum Integrity (화폐 보존 법칙)
> - ✅ Transactional Atomicity (이체 원자성)
> - ✅ Float 오염/Penny Standard 준수
> - ✅ Lifecycle Money Tracking (탄생/소멸 시 자산 출처/목적지)
> - ✅ Saga Locked-Money 감시
> - ✅ M2 Flow Consistency (변동량 삼각검증)
> - ❌ Money-related 코드의 구조/결합도 → `AUDIT_STRUCTURAL`
> - ❌ Money-related 테스트의 Mock 품질 → `AUDIT_TEST_HYGIENE`
> - ❌ 메모리/객체 참조 누수 → `AUDIT_MEMORY_LIFECYCLE`

## 1. 용어 정의 (Terminology)
- **Zero-Sum Violation**: 시스템 전체의 총 자산(Money Supply)이 거래나 에이전트 생성/소멸 과정에서 허공으로 증발하거나 생성되는 현상.
- **Transactional Atomicity**: 구매자의 차변(Debit)과 판매자의 대변(Credit)이 '동시에' 또는 '전혀 안 되게' 수행되어야 하는 일관성 원칙.
- **Reflux Completeness (회수 완전성)**: 세금, 수수료, 파산 자산이 소멸하지 않고 다시 시스템(정부/은행)으로 100% 흘러 들어가는 상태.
- **Locked Money (잠긴 화폐)**: Saga 에스크로에 잠겨 유동성에서 사라졌으나 아직 해제/환불되지 않은 금액.

## 2. Severity Scoring Rubric

| Severity | 기준 | 예시 |
| :--- | :--- | :--- |
| **Critical** | 화폐 증발/생성이 발생하는 경로 | `self.assets += 100` (원천 불명의 자산 추가) |
| **High** | 복합 결제의 원자성 미보장 | 세금+물품대금이 별도 try-catch 없이 순차 실행 |
| **Medium** | Float 오염 (int 연산 필요 구간에 float 사용) | `float(repayment_details["principal"])` |
| **Low** | Reflux 경로의 문서화 부재 | 자산 목적지가 코드에만 있고 문서에 없음 |

## 3. 논리 전개 (Logical Flow)
1. **Transfer Path Tracking**: `BaseAgent` 또는 컴포넌트 내에서 `assets` 필드를 직접 수정하는 모든 쓰기 연산을 추적한다.
2. **Double-Entry Verification**: `finance/` 모듈 내의 이체 로직(`transfer`)이 좌우 합산이 0이 되는지 수학적으로 검토한다.
3. **Penny Standard Compliance**: 화폐 계산 경로에서 `float()` 사용 여부를 탐색한다.
   - 탐색 패턴: `grep -rE "float\(\s*(amount|price|balance|principal|interest)" simulation/ modules/`
4. **Lifecycle Audit**: 
   - 에이전트 탄생 시 자산의 출처(부모의 상속, 정부 보조금 등)가 명확한가?
   - 에이전트 소멸 시 자산의 목적지(`RefluxSystem`)가 명확히 지정되었는가?
5. **Saga Locked-Money Audit**: Saga 상태 전이(INITIATED→COMPLETED) 과정에서 에스크로에 잠긴 금액이 최종적으로 환수/정산되는지 확인.
6. **M2 Flow Consistency Check**: 매 tick에서 `ΔM2 = ΣTransactions ± Mint/Burn`이 성립하는지 변동량 추적.

## 4. 구체적 방법 예시 (Concrete Examples)
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

## 5. Output Configuration
- **Output Location**: `reports/audit/`
- **Recommended Filename**: `AUDIT_REPORT_ECONOMIC.md`
