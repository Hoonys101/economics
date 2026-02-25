```markdown
## 🔍 Summary
이번 PR은 `MonetaryLedger`의 방어적 프로그래밍을 강화하여 시스템 ID 하드코딩을 제거(`constants` 활용)하고, Agent ID 비교 시 안전한 정수 변환 로직을 도입했습니다. 또한 `bond_repayment` 트랜잭션 처리 시 메타데이터에서 `principal`을 안전하게 추출하여 통화 수축(Contraction)을 정확히 계산하도록 개선하였으며 관련된 테스트 코드가 성공적으로 추가되었습니다.

## 🚨 Critical Issues
- **None**: 보안 위반, 돈 복사 버그, 하드코딩 등의 치명적인 결함은 발견되지 않았습니다.

## ⚠️ Logic & Spec Gaps
- 로직 및 스펙 상의 누락이나 오류는 없습니다. 문자열 ID(예: `"household_1"`)가 들어오더라도 `normalize_id`에서 예외 처리를 통해 `-1`을 반환하므로, 시스템 ID(`ID_CENTRAL_BANK` 등)와의 오동작(False Positive) 매칭을 완벽히 방지하고 있습니다.

## 💡 Suggestions
- **성능 최적화 (루프 내 함수 정의 지양)**: 
  `process_transactions` 메서드의 `for tx in transactions:` 루프 내부에서 `def normalize_id(agent_id: Any) -> int:` 함수가 매 반복마다 새로 정의되고 있습니다. 이 함수를 루프 외부(메서드 최상단)나 클래스의 정적 메서드(`@staticmethod`)로 분리하면 오버헤드를 줄일 수 있습니다.

## 🧠 Implementation Insight Evaluation
- **Original Insight**:
  > - **Defensive Coding in Ledgers**: The `MonetaryLedger` was relying on implicit string conversions and potentially unsafe access to `Transaction` metadata. By enforcing `normalize_id` and strict `principal` extraction, we prevent `FloatIncursionError` and `AttributeError` which are critical in financial systems.
  > - **SSoT for Constants**: Moving `ID_PUBLIC_MANAGER` and `ID_CENTRAL_BANK` to `modules.system.constants` and importing them ensures a Single Source of Truth. The previous hardcoding of `"4"` for PublicManager was a fragile implementation detail that has now been removed.
  > - **Protocol Purity**: The refactor respects the `Transaction` protocol/dataclass structure, handling `metadata` (which is Optional) safely using `getattr` and dictionary `get` methods.
- **Reviewer Evaluation**: 
  원문 인사이트가 구현된 변경 사항의 핵심 가치를 매우 정확하게 포착했습니다. DTO의 `Optional` 메타데이터 속성 접근에 대한 방어적 패턴 적용(`getattr` 및 `or {}` 활용)은 시스템 안정성에 크게 기여하는 훌륭한 교훈입니다. 매직 넘버 하드코딩("4")을 SSoT 기반의 상수로 전환한 점 역시 아키텍처 원칙에 완벽히 부합합니다.

## 📚 Manual Update Proposal (Draft)
- **Target File**: `design/2_operations/ledgers/TECH_DEBT_HISTORY.md` (또는 코딩 스탠다드 문서)
- **Draft Content**:
```markdown
### [Resolved] Defensive Metadata Extraction & SSoT Enforcement
- **Date**: 2026-02-26
- **Mission Key**: WO-IMPL-MONETARY-HARDENING
- **Context**: `MonetaryLedger`에서 `Transaction` DTO의 `metadata`에 접근하거나 ID를 비교할 때 묵시적 형변환 및 `NoneType` 오류 위험이 존재했습니다.
- **Resolution**: 
  1. `Transaction.metadata`와 같은 `Optional[Dict]` 필드 접근 시 `getattr(tx, 'metadata', None) or {}` 패턴을 표준으로 적용하여 `AttributeError` 및 `TypeError`를 방어했습니다.
  2. 에이전트 ID 비교 시 시스템 전역의 `constants`(`ID_CENTRAL_BANK` 등)를 단일 진실 공급원(SSoT)으로 사용하고, 비교 전 `normalize_id`를 통한 명시적 정수 캐스팅을 강제했습니다.
```

## ✅ Verdict
**APPROVE**