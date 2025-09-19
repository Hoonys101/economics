# Gemini 프로젝트 지침 (Project Guide)

이 파일은 프로젝트의 핵심 설계 문서와 개발 지침을 안내하는 중앙 허브입니다.
새로운 개발을 시작하거나 기존 코드를 수정할 때, 아래 표를 참조하여 관련된 문서를 먼저 '임포트'(읽고 숙지)하여 프로젝트의 전체적인 아키텍처와 일관성을 유지해야 합니다.

---

## 설계 문서 '임포트' 목록 (Design Document 'Import' List)

| 파일 경로 (File Path) | 주요 내용 (Purpose / Description) | 관련 개념 (Keywords) |
| :--- | :--- | :--- |
| `design/개발지침.md` | 프로젝트의 전반적인 개발 규칙, 코딩 스타일, 사용할 도구(Git, Pytest) 등에 대한 지침입니다. | `PEP 8`, `Git`, `Pytest`, `코딩 스타일`, `개발 환경` |
| `design/경제시뮬레이션_가계_재능_역량_설계.md` | '가계(Household)' 에이전트의 속성(자산, 재능, 필요 등)과 행동(소비, 학습, 노동) 방식을 정의합니다. | `가계`, `에이전트`, `재능`, `역량`, `소비`, `학습` |
| `design/경제시뮬레이션_기업_재고_생산_개선_설계.md` | '기업(Firm)' 에이전트의 생산, 재고 관리, 가격 책정, 고용 등 핵심 로직을 설명합니다. | `기업`, `생산`, `재고`, `가격`, `고용`, `투자` |
| `design/경제시뮬레이션_시장_및_상호작용_설계.md` | 상품 시장과 노동 시장의 작동 원리, 즉 수요와 공급이 만나 가격이 결정되고 거래가 이루어지는 과정을 기술합니다. | `시장`, `수요`, `공급`, `가격 결정`, `상호작용` |
| `design/경제시뮬레이션_AI_모방_메커니즘_설계.md` | AI 에이전트가 다른 성공적인 에이전트를 모방하여 자신의 행동을 개선하는 학습 메커니즘을 설계합니다. | `AI`, `모방`, `학습`, `의사결정`, `에이전트 행동` |
| `design/경제시뮬레이션_UI_설계.md` | 시뮬레이션의 상태를 시각적으로 모니터링하고 제어하기 위한 웹 기반 UI를 설계합니다. | `UI`, `웹`, `대시보드`, `Flask`, `Chart.js` |

---

## 2. 핵심 개발 프로세스 (Core Development Process)

- **계획 확인 (Plan Confirmation)**: 개발 또는 프로젝트 계획을 수립한 후, 구현을 진행하기 전에 사용자로부터 확인을 받습니다.
- **임시 코드 변경 (Temporary Code Changes)**: 테스트 또는 디버깅을 위해 임시로 코드를 변경할 경우, 다음 주석 블록 형식을 사용합니다.
    ```
    # --- GEMINI_TEMP_CHANGE_START: [변경 목적 요약] ---
    # [원래 코드 (주석 처리)]
    # original_line_1
    # original_line_2

    # [임시 변경 코드]
    # temporary_line_1
    # temporary_line_2
    # --- GEMINI_TEMP_CHANGE_END ---
    ```
    *   `GEMINI_TEMP_CHANGE_START` / `GEMINI_TEMP_CHANGE_END`: 변경된 부분임을 명확히 나타내는 마커입니다.
    *   `[변경 목적 요약]`: 이 임시 변경을 왜 했는지 간략하게 설명합니다 (예: "가계 파산 디버깅을 위한 임시 고용 로직").
    *   `[원래 코드 (주석 처리)]`: 원본 코드를 주석 처리하여 보존합니다.
    *   `[임시 변경 코드]`: 임시로 적용할 코드를 작성합니다.

---

## 3. 도구 및 프레임워크 (Tools & Frameworks)

### 3.1. SuperGemini 프레임워크 (SuperGemini Framework)

이 프로젝트에서는 개발 생산성 향상을 위해 **SuperGemini 프레임워크**를 사용할 수 있습니다.

- **설치 (Installation)**:
  ```shell
  pip install SuperGemini
  ```

- **설정 (Setup)**:
  ```shell
  # 추천 설정 (Express setup)
  SuperGemini install --yes
  ```

- **사용법 (Usage)**:
  Gemini CLI 내에서 `/sg:` 접두사를 사용하여 고수준의 작업을 지시할 수 있습니다.

  - **코드 분석 예시**:
    ```
    /sg:analyze src/
    ```
  - **기능 구현 예시**:
    ```
    /sg:implement user authentication
    ```
