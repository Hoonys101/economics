# 🔍 Git Diff 리뷰 보고서: WO-105 Tech Debt Liquidation

---

### 🔍 Summary
이 커밋은 WO-105 기술 부채 청산의 일환으로 진행된 리팩토링입니다. 주요 변경 사항은 다음과 같습니다:
- `household` 모듈에서 설정 값 접근 로직을 단순화했습니다.
- `fixture_harvester.py` 스크립트에서 테스트 유틸리티(`GoldenLoader`)에 대한 의존성을 강화하고, 폴백(fallback) 로직을 제거했습니다.
- `production_department`의 생산성(TFP) 계산 로직을 더 명확하게 개선했습니다.

---

### 🚨 Critical Issues
- **발견되지 않음.** 즉시 수정이 필요한 보안 취약점이나 데이터 무결성 문제는 없습니다.

---

### ⚠️ Logic & Spec Gaps
1.  **[Architecture] `scripts/` 모듈이 `tests/` 모듈에 의존 (SoC 위반)**
    - **파일**: `scripts/fixture_harvester.py`
    - **문제**: 운영/개발용 스크립트(`fixture_harvester.py`)가 테스트 코드(`tests.utils.golden_loader`)를 직접 `import`하고 있습니다. 이는 심각한 **관심사 분리(SoC) 원칙 위반**입니다. 테스트 코드는 프로덕션 코드나 운영 스크립트에서 사용되어서는 안 됩니다.
    - **영향**:
        - 향후 테스트 코드가 없는 환경(예: 경량 배포)에서 해당 스크립트가 실패하게 됩니다.
        - 테스트 유틸리티의 변경이 운영 스크립트에 예기치 않은 부작용을 일으킬 수 있습니다.

---

### 💡 Suggestions
1.  **`GoldenLoader` 유틸리티 위치 변경 제안**
    - `tests/utils/golden_loader.py`에 있는 `GoldenLoader` 클래스는 테스트와 스크립트 양쪽에서 모두 사용되는 공통 유틸리티로 보입니다.
    - 이 클래스를 프로젝트 루트의 `utils/`나 `modules/common/`과 같은 공용 디렉토리로 이동시키는 리팩토링을 강력히 권장합니다. 이를 통해 `scripts`와 `tests`가 아키텍처 경계를 침범하지 않고 안전하게 의존성을 공유할 수 있습니다.

2.  **설정 값 접근 단순화에 대한 참고사항**
    - **파일**: `modules/household/econ_component.py`
    - **내용**: 설정 값 로드 시 `isinstance`와 `int()` 캐스팅을 제거한 것은 코드를 간결하게 만들지만, 설정 파일(`config_module`)에 예기치 않은 타입(예: 문자열)이 들어왔을 때의 방어 로직이 사라졌습니다. 설정 값의 유효성 검사가 다른 곳에서 보장된다는 전제 하에 이 변경은 수용 가능합니다.

---

### ✅ Verdict
**REQUEST CHANGES**

**사유**: `scripts`가 `tests`에 의존하는 아키텍처 위반 사항은 프로젝트의 장기적인 유지보수성과 안정성을 위해 반드시 수정되어야 합니다. 제안된 리팩토링(공용 유틸리티 디렉토리로 `GoldenLoader` 이동)을 적용한 후 다시 리뷰를 요청해주십시오. 나머지 로직 개선 사항들은 긍정적입니다.
