# 🏺 HERITAGE ASSETS: Legacy Inventory

프로젝트 진행 과정에서 생성되었으나, 현재는 우선순위 밀림으로 "유기"된 자산들을 정리합니다. 이들은 언제든 부활시켜 시뮬레이션을 보강할 수 있는 소중한 자산입니다.

## 🖥️ 1. Dashboard v1 (Visualization)
*   **Backend (`app.py`)**: Flask 기반의 API 서버. 시뮬레이션의 스냅샷과 지표를 실시간으로 서빙하도록 설계됨.
*   **Frontend (`frontend/`)**: Vite + React 기반의 대시보드. GDP, 실업률, 빈부격차 등을 시각화하는 차트 포함.
*   **ViewModel**: `SnapshotViewModel`, `EconomicIndicatorsViewModel` 등 데이터 가공 레이어 존재.
*   **활용 방안**: 현재의 CLI/JSON 중심 분석을 넘어, 시각적인 모니터링이 필요할 때 재활성화 가능.

## 📊 2. Analysis Suite (Scripts)
*   **Crucible Test (`scripts/iron_test.py`)**: 1000틱 이상의 장기 생존성과 화폐 보존을 검증하는 핵심 검증기.
*   **Operation Darwin (`scripts/operation_darwin.py`)**: 에이전트들의 유전적 진화와 적응을 추적하는 실험용 스크립트.
*   **Visualizer (`scripts/visualize_economy.py`)**: Matplotlib을 사용해 시뮬레이션 결과 데이터를 PNG 차트로 생성.
*   **Auto-Reporter (`scripts/generate_phase1_report.py`)**: 시뮬레이션 종료 후 자동으로 Markdown 리포트를 생성하는 엔진.

## 📝 3. Reporting Engine
*   **Reports (`reports/`)**: 과거 시뮬레이션의 "부검 리포트(Autopsy)" 및 "금본위제 검증 리포트" 등 다수 저장.
*   **History JSON**: `fiscal_history.json` 등 시각화용 데이터 덤프 처리 로직.

## 🗃️ 4. AI Training & Lab
*   **Mitosis Spec**: 과거에 설계되었으나 유보된 '세포 분열(Mitosis)'과 '부모-자녀 상속' 모델 (`mitosis_inheritance_spec.md`).
*   **API Lab**: `simulation/ai/api.py`에 정의된 페르소나와 전술 정의 레이어.

---

> [!TIP]
> **부활 가이드**: 유기된 자산들은 대부분 `SimulationRepository`와 `ViewModel`에 의존합니다. 이 인터페이스들을 현재의 `main` 브랜치에 맞춰 업데이트하면 즉시 작동 가능합니다.
