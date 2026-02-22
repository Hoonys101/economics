# Architecture Detail: System Infrastructure & Interface

## 1. 개요
본 시뮬레이션의 근간이 되는 인프라 설계와 데이터 관리, 외부 사용자와의 인터페이스 구조를 다룹니다. 시스템은 독립적인 컴포넌트 간의 느슨한 결합(Loose Coupling)과 강력한 데이터 정합성을 목표로 합니다.

## 2. 엔진 및 데이터 인프라

### 2.1 Simulation Engine
- **기반**: 이산 사건 시뮬레이션(Discrete Event Simulation).
- **역할**: 시간(`tick`)의 흐름을 통제하고, 각 Phase의 실행 순서를 조율하는 오케스트레이터입니다.

### 2.2 Data Persistence (Persistence Layer)
- **DB**: SQLite. 시뮬레이션의 모든 거래 원장, 에이전트 상태, 거시 지표를 기록합니다.
- **Repository Pattern**: `SimulationRepository`를 통해 비즈니스 로직과 저수준 데이터베이스 접근 코드를 분리합니다.

### 2.3 Configuration Management (Unified Config)
- **Problem**: 기존의 `config.py`와 YAML 설정 파일의 이원화로 인한 관리 복잡성 및 정합성 위협.
- **Solution**: Pydantic 기반의 **Integrated Configuration System** (`modules/config`).
    - **Layers**: Default -> YAML Override -> Environment Variables -> Runtime Injection.
    - **Validation**: 로딩 시점에 엄격한 타입 검사와 범위 체크 수행.
    - **Dependency**: `ConfigurationComponent`를 통해 ECS 구조 내에서 상태 의존성 없이 설정 주입.
2.4 **Common Layer (Type Foundation)**:
    - **Purpose**: To prevent circular dependencies between Domain Modules (e.g., Household vs Labor).
    - **Content**: Stateless Enums, Global Constants, and shared Protocols that do not import from Domain Modules.
    - **Standard**: All cross-domain Enums (e.g., `IndustryDomain`) MUST reside in `modules/common/`.

## 3. 인터페이스와 프로토콜 (API-Driven)

모듈 간의 통합은 구체적인 클래스가 아닌 인터페이스(Protocol)를 통해 이루어집니다.

### 3.1 추상화 원칙 (Dependency Inversion)
- **Problem**: 다른 모듈의 내부 구현에 의존하면 작은 변경에도 전체 시스템이 깨질 수 있음.
- **Solution**: `modules/<name>/api.py`에 정의된 인터페이스 프로토콜에만 의존합니다.
- **예시**: 가계는 `Bank` 클래스가 아닌 `IBankService` 프로토콜을 구현한 어떤 객체와도 상호작용할 수 있습니다.

### 3.2 데이터 계약 (Data Contracts)
- 모든 시스템 간 통신은 명확하게 정의된 **DTO (Data Transfer Object)**를 통해서만 이루어집니다.
- 객체의 참조를 넘기는 대신, 필요한 데이터만 담긴 정적 구조를 전달하여 일관성을 확보합니다.

## 4. 프론트엔드 및 시각화 (Web Dashboard)

사용자는 실시간으로 변화하는 경제 지표를 대시보드를 통해 관찰할 수 있습니다.

- **Backend**: Flask API (`/api/simulation/tick` 등).
- **Frontend**: Vanilla JS 기반의 가벼운 SPA 구조.
- **Visualization**: Chart.js를 사용하여 GDP, 통화량, 인플레이션율 등을 시각화합니다.

## 5. 아키텍처적 의의
이 인프라 설계는 시뮬레이션의 **"확장 가능성"**과 **"관찰 가능성"**을 보장합니다. 새로운 정책 모듈이나 에이전트 타입을 추가할 때 기존 코드를 수정할 필요가 적으며(Open-Closed Principle), 시뮬레이션 과정에서 발생하는 모든 현상을 데이터로 투명하게 분석할 수 있습니다.
