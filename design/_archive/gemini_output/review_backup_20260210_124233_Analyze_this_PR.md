# PR Review: Refactor Household Decision Unit Test Imports

### 🔍 Summary

해당 변경은 `test_decision_unit.py` 테스트 파일 내에서 사용되는 `MarketSnapshotDTO`, `HousingMarketSnapshotDTO`, `LoanMarketSnapshotDTO`, `LaborMarketSnapshotDTO`의 import 경로를 `modules.household.api`에서 `modules.system.api`로 변경하는 리팩토링입니다. 이는 시스템 전반의 데이터를 `system` 모듈 API에서 제공하도록 하는 올바른 아키텍처 방향입니다.

### 🚨 Critical Issues

- 해당 사항 없음.

### ⚠️ Logic & Spec Gaps

- **[Process Fail]** **인사이트 보고서 누락**: `communications/insights/[Mission_Key].md` 파일이 Diff에 포함되지 않았습니다. 아키텍처 경계를 정리하는 리팩토링은 중요한 설계 결정이며, 그 배경과 효과에 대한 인사이트 기록이 반드시 필요합니다. 이는 명백한 프로세스 위반입니다.

### 💡 Suggestions

- 코드 변경 자체는 긍정적입니다. 시스템 관련 DTO를 `system` 모듈에서 가져오는 것은 모듈 간 결합도를 낮추고 역할과 책임을 명확하게 하는 좋은 설계입니다.

### 🧠 Implementation Insight Evaluation

- **Original Insight**: [제출된 인사이트 파일이 없어 평가 불가]
- **Reviewer Evaluation**: 리팩토링의 이유, 즉 왜 `household` API가 아닌 `system` API에서 시장 정보를 가져와야 하는지에 대한 기술적 배경, 그리고 이 변경이 향후 다른 모듈에 미칠 영향(예: 의존성 구조 개선, 테스트 용이성 증가 등)에 대한 분석이 포함된 인사이트 작성이 필요합니다.

### 📚 Manual Update Proposal
- **Target File**: `design/2_operations/ledgers/ARCHITECTURE_DECISIONS.md`
- **Update Content**: 인사이트가 제출되면, 이 리팩토링을 "모듈 간 API 책임 분리" 원칙을 강화하는 결정의 예시로 기록할 것을 제안합니다.

### ✅ Verdict

**REQUEST CHANGES (Hard-Fail)**

**사유**: 코드 변경의 방향성은 올바르나, **프로세스의 핵심 요구사항인 인사이트 보고서가 누락**되었습니다. 모든 코드 변경, 특히 아키텍처에 영향을 미치는 리팩토링은 반드시 그 의도와 결과를 문서화해야 합니다. `communications/insights/`에 관련 문서를 추가한 후 다시 리뷰를 요청하십시오.
