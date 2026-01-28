# [WORK ORDER] WO-057-B: The Sensory (Macro Data Pipeline)

> **Assignee**: Jules Bravo
> **Goal**: 정부가 정책 결정을 내릴 수 있도록 10틱 이동평균(SMA) 거시 데이터를 공급함.

## 📂 Context Table
| 분류 | 파일 리스트 | 활용 가이드 |
| :--- | :--- | :--- |
| **Source** | `simulation/engine.py` | 기존 시장 지표 수집 부위 확인 |
| **Contract** | `simulation/dtos.py` | `GovernmentStateDTO` 타입 준수 |
| **Destination**| `simulation/engine.py` | 데이터 정제 및 SMA 파이프라인 구축 |

## 🧩 구현 요구 사항 (Zero-Question)
1.  **SMA Buffer**: `engine.py` 내부에 `inflation`, `unemployment` 등의 지표를 저장할 `deque(maxlen=10)` 버퍼를 생성하십시오.
2.  **Data Translation**: 매 틱 수집된 정보를 SMA로 가공하여 `GovernmentStateDTO` 객체로 생성, 정부 에이전트에게 공급하는 루틴을 구현하십시오.
3.  **Noise Reduction**: 단기 틱 변동(Noise)이 아닌 추세(Trend)가 전달되도록 정교하게 평균을 계산하십시오.

## ⚠️ 제약 사항
- `Simulation` 클래스의 핵심 루프를 방해하지 않도록 최소한의 오버헤드로 구현할 것.
