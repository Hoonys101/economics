# 분석 보고서: Gemini 미션 메모리 초과 원인 진단

## 1. 개요
4건의 명세 작성 미션 중 2건(`PROXY_CACHE`, `BATCH_NOTIFY`)은 성공했으나, 2건(`REGISTRY_LOCK`, `ADAPTER_OPT`)은 메모리 초과로 실패했습니다. 파일 크기 자체는 실패한 미션들이 훨씬 작음에도(2~4kb vs 15~40kb) 불구하고 발생한 역설적인 현상을 분석했습니다.

## 2. 근본 원인: 의존성 그래프의 무게 (Dependency Weight)

Gemini-CLI는 컨텍스트를 수집할 때 `import`문을 추적하여 연관 파일을 함께 읽어들입니다. 이번 실패의 핵심은 **`modules.finance.api`**에 있습니다.

### [실패한 미션들]
- **공통점**: 모두 `modules/finance/` 디렉토리에 있으며 `modules.finance.api`를 직접 참조합니다.
- **`modules.finance.api` 분석**: 
    - 파일 크기: **1,179 라인** (매우 큼)
    - 참조 범위: `Government`, `HR`, `Simulation Models`, `Engine API`, `Portfolio DTOs` 등을 모두 끌어들입니다.
    - 결과: `account_registry.py`는 단 50라인뿐이지만, 이를 분석하기 위해 Gemini-CLI가 수천 라인의 재무 관련 도메인 로직을 전부 컨텍스트로 로드하게 됩니다.

### [성공한 미션들]
- **`registry.py`**: 주로 `modules.system.api`를 참조합니다. 이 파일은 시스템 코어 프리미티브만 포함하고 있어 참조 그래프가 얕고 가볍습니다.
- **`initializer.py`**: 비록 파일은 크지만, 참조하는 `simulation/engine.py` 등은 이미 로드된 컨텍스트 내에서 중복되는 경우가 많고, 도메인 레이어(Finance/Gov)보다는 시뮬레이션 인프라 레이어에 집중되어 있어 메모리 임계치를 넘지 않았습니다.

## 3. 요인 요약 비교

| 항목 | 성공 미션 (System/Init) | 실패 미션 (Finance) |
|---|---|---|
| **파일 크기** | 15kb ~ 43kb | **2kb ~ 4kb** |
| **핵심 의존성** | `modules.system.api` (Light) | **`modules.finance.api` (Heavy)** |
| **의존성 깊이** | 인프라 중심, 얕음 | **도메인 결합도 높음, 매우 깊음** |
| **지시 사항** | 단일 목적 | 다중 목적 (`ADAPTER_OPT` 등) |

## 4. 향후 대응 전략
1. **의존성 격리**: `modules.finance.api`와 같이 무거운 파일을 참조하는 경우, `context_files`를 추가하지 말고 지시 사항에 해당 파일의 핵심 부분만 텍스트로 복사해서 전달하는 것이 안전합니다.
2. **미션 세분화**: 여러 목적이 섞인 `ADAPTER_OPT` (Phase D+E) 같은 경우, 이미 무거운 컨텍스트를 로드한 상태에서 추론 부하까지 겹쳐 실패할 확률이 높으므로 더 쪼개야 합니다.
3. **인터페이스 분리**: `IAccountRegistry` 등 꼭 필요한 인터페이스만 별도 파일로 분리하여 `modules.finance.api` 전체를 로드하지 않도록 아키텍처를 개선할 필요가 있습니다.
