# Insight Report: Efficient Simulation Data Logging Infrastructure

## 현상 (Phenomenon)
- 시뮬레이션 실행 중 발생하는 대규모 데이터(수만 건의 에이전트 사고 과정 로그)를 실시간으로 데이터베이스에 기록할 때 발생하는 심각한 성능 저하.

## 원인 (Cause)
- 각 로그 발생 시마다 데이터베이스에 개별적인 INSERT 쿼리를 실행하여 과도한 I/O 및 트랜잭션 오버헤드가 발생함.

## 해결 (Solution)
- `SimulationLogger` 클래스를 구현하여 로그 데이터를 인-메모리 버퍼(리스트)에 수집.
- 주기적으로 `flush` 메소드를 호출하여 버퍼에 쌓인 다수의 로그를 단일 트랜잭션 내에서 `executemany`를 사용해 한번에 DB에 기록(Bulk Insert).
- SQLite의 `PRAGMA journal_mode=WAL;` 설정을 통해 쓰기 작업 중에도 읽기 작업이 블로킹되지 않도록 하여 동시성을 개선함.

## 교훈 (Lesson Learned)
- 대량의 쓰기 작업이 필요한 경우, 애플리케이션 레벨에서 버퍼링을 구현하고 DB의 Bulk Insert 기능을 활용하는 것이 성능 최적화에 필수적이다.
- 리소스(DB 커넥션, 파일 핸들 등)의 라이프사이클은 소멸자(`__del__`)에 의존하지 말고, Context Manager (`with` 구문)를 통해 명시적으로 관리해야 코드의 안정성과 예측 가능성이 높아진다.
