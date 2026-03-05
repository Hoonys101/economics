# AUDIT_SPEC_MEMORY_LIFECYCLE: Memory & Lifecycle Audit (v1.0)

**목표**: 런타임 자원 관리의 안전성을 검증하여, 순환 참조·미해제 객체·무한 성장 컬렉션 등이 시뮬레이션의 안정성과 성능을 저해하는 것을 방지한다.

**관심사 경계 (SoC Boundary)**:
> 이 감사는 오직 **"런타임 자원이 올바르게 관리되는가 (Runtime Resource Management)"**만을 다룬다.
> - ✅ 객체 생명주기 (생성 → teardown 완전성)
> - ✅ 런타임 순환 참조 탐지 (GC-level)
> - ✅ Unbounded Collection 감시
> - ✅ Agent Dispose 패턴
> - ✅ weakref 정합성
> - ❌ 정적 import 의존성 분석 → `AUDIT_STRUCTURAL`
> - ❌ 테스트의 teardown 위생 → `AUDIT_TEST_HYGIENE`
> - ❌ 화폐 누수 → `AUDIT_ECONOMIC`

## 1. 용어 정의 (Terminology)
- **Teardown Completeness**: `WorldState.teardown()`이 `__init__`에서 생성한 모든 시스템/서비스 인스턴스를 해제하는 상태.
- **Cyclic Reference (런타임 순환 참조)**: 두 개 이상의 객체가 강한 참조(Strong Reference)로 서로를 가리켜 GC가 해제할 수 없는 상태.
- **Unbounded Collection**: `.append()` 또는 `[key] = value` 이후 truncation/eviction 정책이 없어 무한히 성장하는 리스트/딕셔너리.
- **Ghost Reference**: 에이전트 사망 후에도 다른 시스템이 보유한 강한 참조로 인해 GC 대상에서 제외되는 "유령 객체".

## 2. Severity Scoring Rubric

| Severity | 기준 | 예시 |
| :--- | :--- | :--- |
| **Critical** | 순환 참조로 인한 GC Hang 또는 OOM | Engine↔Orchestrator↔WorldState 상호 참조 |
| **High** | Teardown 누락 (시스템 미해제) | `bank`, `central_bank` 가 teardown 목록에 없음 |
| **Medium** | Unbounded Collection 또는 Ghost Reference | `inactive_agents` 리스트의 무한 성장 |
| **Low** | weakref → strong ref 전환 가능한 미사용 참조 | 참조되지 않는 cached 프로퍼티 |

## 3. 감사 범위 (Audit Scope)

### 3.1 Teardown 완전성 감사
- **방법**: `WorldState.__init__`에서 할당되는 모든 시스템 속성 목록을 추출하고, `WorldState.teardown()` 내의 해제 목록과 대조.
- **탐지**: `__init__` 에 있으나 `teardown()`에 없는 속성은 "Teardown Gap"으로 보고.
- **동적 teardown 권고**: 하드코딩된 40-item 리스트 대신 `__dict__` 기반 동적 teardown 패턴 제안.

### 3.2 런타임 순환 참조 탐지
- **1차**: `weakref.ref` 대신 강한 참조를 사용하여 시스템 간 연결된 곳을 정적 검색.
  - 탐지: `grep -rn "self\.\w+ = \w+_system\|self\.\w+ = \w+_engine" simulation/`
- **2차**: `gc.get_referrers()` 기반의 런타임 그래프 순환 검사 (해당 스크립트의 존재 여부 확인).

### 3.3 Unbounded Collection 감사
- **탐지**: `.append(`, `[key] =` 패턴이 있으나 같은 컨텍스트에 `del`, `pop`, `clear`, 또는 max-size 제한이 없는 컬렉션.
- **특별 감시**: `AgentRegistry.inactive_agents`, 이벤트 큐, 로그 버퍼 등.

### 3.4 Agent Dispose 패턴 감사
- **검증**: 에이전트 사망 처리 시 `Agent.dispose()` 메서드를 통해 캡슐화된 정리가 수행되는지 확인.
- **Anti-Pattern**: `DemographicManager`가 직접 `agent._econ_state = None` 등으로 필드를 클리어하는 경우.
- **List Reference Leak**: `AgentRegistry.purge_inactive()`가 리스트를 교체(`=`)하는지, 제자리(in-place `[:]`)로 수정하는지 확인.

## 4. Output Configuration
- **Output Location**: `reports/audit/`
- **Recommended Filename**: `AUDIT_REPORT_MEMORY_LIFECYCLE.md`
