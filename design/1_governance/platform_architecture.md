# Platform Architecture & Design Philosophy (Master Index)

## 1. 비전 (Vision)
본 플랫폼은 복잡한 거시경제 현상을 데이터와 지능형 에이전트의 상호작용으로 재구성하는 **"살아있는 경제 실험실"**입니다. 단순히 수치를 시뮬레이션하는 것을 넘어, 경제 주체들의 욕구와 전략이 부딪히며 만들어내는 창발적 질서를 관찰하는 것을 목적으로 합니다.

## 2. 아키텍처 계층 구조 (Structural Skeleton)

플랫폼의 핵심 설계는 추상적 철학에서 구체적 구현으로 이어지는 5대 핵심 도메인으로 나뉩니다. 상세한 동작 원리는 각 연결 문서를 참조하십시오.

### 2.1 [신성한 시퀀스 (Sacred Sequence)](architecture/ARCH_SEQUENCING.md)
- **개념**: 시뮬레이션의 물리적 시간과 인과율을 통제하는 8단계 오케스트레이션.
- **핵심**: "인지-계약-집행-정리"의 엄격한 순차 처리를 통한 데이터 정합성 보장.

### 2.2 [에이전트지능 및 가치 체계 (Agent Intelligence)](architecture/ARCH_AGENTS.md)
- **개념**: 매슬로 욕구 이론 기반의 가치관과 AI-유효성 검증 규칙의 2중 구조.
- **핵심**: Purity Gate와 Facade-Component 패턴을 통한 에이전트 독립성 확보.

### 2.3 [금융 무결성 및 시스템 정산 (Transactions)](architecture/ARCH_TRANSACTIONS.md)
- **개념**: 모든 가치 이동을 트랜잭션으로 관리하는 제로섬(Zero-Sum) 원칙.
- **핵심**: Settlement System을 통한 원자적 결제 및 "신비한 자금(Magic Money)" 원천 차단.

### 2.4 [지능 계층 및 최적화 (AI & Optimization)](architecture/ARCH_AI_ENGINE.md)
- **개념**: Q-Learning 기반의 전략 적응 및 NumPy를 활용한 대규모 벡터 연산.
- **핵심**: 고성능 연산 계층과 에이전트의 전략적 진화 메커니즘.

### 2.5 [시스템 인프라 및 API (System & Interface)](architecture/ARCH_SYSTEM_DESIGN.md)
- **개념**: 프로토콜 중심의 느슨한 결합과 실시간 관찰을 위한 웹 인터페이스.
- **핵심**: DTO 기반 데이터 계약 및 플러그인 가능한 모듈식 설계.

### 2.6 [청산 및 시스템 건전성 (Liquidation Protocols)](architecture/ARCH_TRANSACTIONS.md)
- **개념**: 좀비 기업(Zombie Agent)의 시장 교란을 방지하고 "Fast-Fail" 원칙에 따라 자원을 즉시 재분배.
- **핵심**: Liquidation Waterfall(TD-187)을 통한 5단계 자산 분배 우선순위(1.임금/퇴직금 -> 2.담보채무 -> 3.세금 -> 4.일반채무 -> 5.주주) 및 Systemic Liquidation Phase(Phase 4.5) 실행.

---

## 3. 핵심 설계 원칙 (Core Principles)

본 프로젝트의 모든 코드는 다음의 아키텍처 원칙을 준수해야 합니다.

1. **Arm the Tool, Do not be the Tool**: 모든 복잡한 작업은 에이전트와 도구에 위임하며, 관리자(Antigravity)는 구조와 의도를 설계한다.
2. **Purity over Convenience**: 개발의 편의성보다 데이터의 순수성과 정합성이 우선된다. (No Global Sinks, No Static Access)
3. **Traceability by Default**: 시스템 내에서 발생하는 모든 현상은 기록되어야 하며, 사후 분석(Forensics)이 가능해야 한다.

---

## 4. 문서 관리 지침 (Maintenance Role)

- **언제 업데이트하는가?**: 새로운 기능 명세(SPEC)를 작성하거나 중요한 기술 부채를 상환할 때, 해당 내용이 근원 아키텍처에 영향을 준다면 반드시 관련 상세 문서를 업데이트해야 합니다.
- **보고 체계**: 매일 생성되는 **정합성 보고서(Integrity Report)**를 통해 아키텍처 설계와 실제 구현의 괴리를 확인하고 이를 보정합니다.

> **"의도가 먼저고, 실행은 따르는 것이다."** - Architecture Protocol v3.0
