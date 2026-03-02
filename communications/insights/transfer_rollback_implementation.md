### Transfer Rollback Implementation (역방향 트랜잭션을 통한 롤백)
- **현상**: 이체 트랜잭션 실패 또는 보상 트랜잭션 필요 시 롤백을 처리하는 로직이 미구현 상태였음.
- **원인**: `TransferHandler.rollback`이 `TODO`로 남아 작동하지 않음.
- **해결**: 원본 트랜잭션(`TransactionDTO`)의 Source와 Destination을 반전시킨 역방향 트랜잭션을 `LedgerEngine`을 통해 실행하도록 `rollback` 메서드 구현.
- **교훈**: 롤백 트랜잭션 실행 시 발생하는 예외(Exception)는 원상 복구 실패라는 치명적인 상태 불일치를 의미하므로, 예외를 조용히 무시(Swallow)하지 않고 반드시 상세히 로깅하여 추적 가능성을 확보해야 함.
