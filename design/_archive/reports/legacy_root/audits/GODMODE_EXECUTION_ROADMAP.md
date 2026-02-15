# 🖋️ Project Roadmap: God-Mode Watchtower (Simulation Cockpit)

**Status**: Master Execution Plan (Scribe Draft)  
**Ref Version**: v1.1.0 (2026-02-13)  
**Mission Key**: GODMODE-WATCHTOWER-EXECUTION  
**Orchestrator**: Antigravity (Architect Prime)

---

## 1. 개요 (Executive Summary)

본 로드맵은 시뮬레이션의 실시간 제어 및 관측을 위한 `God-Mode Watchtower` 구축을 위한 단계별 실행 계획입니다. 수석 아키텍트의 지침에 따라 **'Foundation First'** 원칙을 고수하며, 엔진의 무결성을 보장하는 동시에 프론트엔드와 백엔드 개발을 병렬화하여 속도를 극대화합니다.

### 1.1 Critical Path (핵심 병목 지점)
- **GlobalRegistry 구현**: 하드코딩된 상수(`economy_params.yaml` 등)를 런타임 수정 가능한 객체로 전환하는 작업이 모든 `SET_PARAM` 명령의 선행 조건임.
- **Phase 34 (Operation Clean Hands)**: 정부 모듈의 거대 객체(God Class) 분리가 완료되어야 시나리오 개입 시 부수 효과를 예측 가능함.

---

## 2. 병렬 수행 전략 (Parallel Strategy)

| Layer | Focus Area | Interface Contract |
| :--- | :--- | :--- |
| **Backend** | Registry, Intercept Logic, Telemetry Harvesting | `GodCommandDTO`, `WatchtowerV2-DTO` |
| **Frontend** | Streamlit UI, Dynamic Sliders, Visualizers | `GodCommandDTO`, `WatchtowerV2-DTO` |

**계약 중심 개발 (Contract-Driven)**: `api.py`와 `dtos.py` 명세를 최우선으로 확정하여, 백엔드 로직이 완성되기 전에도 프론트엔드가 Mock 데이터를 기반으로 UI 구성을 완료할 수 있도록 합니다.

---

## 3. 세부 미션 정의 (Detailed Missions)

### Phase 1: Foundation (The Bedrock) - 기초 공사 및 무결성 확보
| 미션 키 | 목표 | 의존성 | 예상 결과물 |
| :--- | :--- | :--- | :--- |
| **FOUND-01** | `GlobalRegistry` 구현 및 기존 상수 마이그레이션 | None | `modules/system/registry.py` |
| **FOUND-02** | Government 모듈 서비스 분리 (Tax, Welfare) | TD-226~229 | `modules/government/services/` |
| **FOUND-03** | Sacred Sequence Phase 0 (Intercept) 슬롯 확보 | Scheduler | `TickScheduler.phase_0_intercept()` |

### Phase 2: Data & Protocol (The Nervous System) - 신경망 구축
| 미션 키 | 목표 | 의존성 | 예상 결과물 |
| :--- | :--- | :--- | :--- |
| **DATA-01** | `GodCommandDTO` 명세 확정 (`failure_reason`, `rollback` 포함) | FOUND-03 | `simulation/dtos/commands.py` |
| **DATA-02** | On-Demand Telemetry 엔진 (선택적 데이터 수집) | FOUND-01 | `TelemetryCollector.harvest(mask: List[str])` |
| **DATA-03** | `ScenarioVerifier` 실시간 판정 엔진 구현 | Scenario Cards | `modules/analysis/scenario_verifier.py` |

### Phase 3: Dashboard & UX (The Cockpit) - 조종석 시각화
| 미션 키 | 목표 | 의존성 | 예상 결과물 |
| :--- | :--- | :--- | :--- |
| **UI-01** | Streamlit 기반 Watchtower Scaffolding | DATA-01 | `dashboard/app.py` (Shell) |
| **UI-02** | Registry 기반 동적 슬라이더 생성기 구현 | FOUND-01 | `dashboard/components/controls.py` |
| **UI-03** | 실시간 KPI 게이지 및 히트맵 컴포넌트 개발 | DATA-02 | `dashboard/components/visuals.py` |

### Phase 4: Integration (The Final Link) - 통합 및 검증
| 미션 키 | 목표 | 의존성 | 예상 결과물 |
| :--- | :--- | :--- | :--- |
| **INT-01** | WebSocket 기반 명령-응답 루프 연결 | UI-01, DATA-01 | 실시간 통신 인터페이스 완성 |
| **INT-02** | 시나리오 스트레스 테스트 (Macro Shock Injection) | All | `reports/audits/STRESS_TEST_REPORT.md` |

---

## 4. 아키텍처 상세 지침 반영 (Scribe's Instruction)

### 4.1 God-Mode 명령 처리 로직 (Safety-First)
- **Atomic Execution**: 모든 `GodCommand`는 `SettlementSystem`의 원자적 트랜잭션 내에서 실행되거나, 상태 변경 후 반드시 `Audit`을 통과해야 함.
- **Rollback Mechanism**: `SET_PARAM` 명령 수행 전 현재 상태를 `UndoStack`에 저장. 실패 시 `failure_reason`과 함께 즉시 롤백.
- **Graceful Failure**: 엔진은 유효하지 않은 명령을 수신했을 때 크래시되지 않고, 에러 DTO를 Watchtower로 즉시 반환해야 함.

### 4.2 Telemetry 최적화 (On-Demand)
- **Subscription Model**: Watchtower가 현재 보고 있는 화면에 필요한 데이터 필드만 `mask` 형태로 요청.
- **Frequency Control**: 거시 데이터는 매 틱(1Hz), 미시 히트맵은 10틱당 1회(0.1Hz) 등으로 전송 빈도 차별화.

---

## 5. Risk & Rollback Strategy

| 위험 요소 | 영향도 | 대응 방안 |
| :--- | :--- | :--- |
| **Magic Money 생성** | High | `SettlementSystem`의 `total_m2_audit`을 Phase 0 직후 강제 실행. |
| **UI 통신 지연** | Medium | 명령 큐(Command Queue)를 로컬스토리지에 캐싱하고 지연 발생 시 UI 경고 표시. |
| **Registry 충돌** | Low | 파라미터별 '소유권(Ownership)' 정의. God-Mode가 수정한 변수는 엔진 내 다른 로직이 덮어쓰지 못하도록 Lock 설정. |

---

## 6. Mandatory Reporting Verification

본 로드맵 설계 과정에서 식별된 다음의 사항을 인사이트 리포트로 기록함.
- **파일 위치**: `communications/insights/WATCHTOWER_ROADMAP_INSIGHTS.md`
- **기록 항목**:
    - `GlobalRegistry` 도입에 따른 `config.py`와의 역할 중복 해결 방안.
    - `Government` God Class 해체 시나리오 중 `Welfare` 기금 고갈 시의 God-Mode 개입 규칙.
    - 실시간 데이터 스트리밍 시 Python `asyncio`와 `Simulation Loop` 간의 컨텍스트 스위칭 오버헤드 예측.

> **"구조가 명확하면 구현은 수단일 뿐이다. 조종석을 만들기 전에 먼저 비행기가 추락하지 않을 정합성을 확보하라."** - Administrative Scribe's Final Note