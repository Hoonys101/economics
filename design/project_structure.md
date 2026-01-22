# 📁 프로젝트 구조 및 업무 지침서 (v2)

---

## 📦 1. 프로젝트 파일 시스템 구조

```bash
/project-root/
│
├── communications/         # 💬 팀 소통 채널
│   ├── announcements/      # PL -> 전체 공지
│   └── requests/           # 개발자 -> PL 요청
│
├── docs/                   # 📘 설계 및 API 문서 (설계자 전담)
│   └── spec.md
│
├── core/                   # ⚙️ 공통 기능 모듈 (설계자 전담)
│   └── utils.py
│
├── interface/              # 🔌 모듈 간 인터페이스 정의 (설계자 전담)
│   └── stock_interface.py
│
├── modules/                # 🧱 각 개발자 전담 모듈 디렉토리
│   ├── user/               # 사용자 관리 모듈 (개발자 A)
│   ├── stock/              # 주식 데이터 모듈 (개발자 B)
│   └── ...                 # 기타 기능별 모듈
│
├── tests/                  # ✅ 단위 테스트 디렉토리
│   ├── user_test.py
│   └── ...
│
├── config/                 # ⚙️ 설정 파일 (설계자/PL 전담)
│   └── settings.py
│
├── main.py                 # 🚀 실행 진입점 (PL이 관리)
├── README.md               # 🗂️ 프로젝트 개요
└── requirements.txt        # 📦 의존 패키지 리스트
```

---

## 🧭 2. 역할별 업무 가이드

### 🔷 설계자
- `/docs/spec.md`: 전체 시스템 설계 명세 관리
- `/interface/`: 각 모듈 간 인터페이스 정의 및 유지
- `/core/`: 공통 기능 모듈 (예: 로깅, 예외 처리, 유틸리티)
- `/config/`: 설정 값, 환경 변수 관리

### 🔶 개발자
- `/modules/<module>/` 폴더 내 기능 개발 전담
- 해당 모듈의 테스트 코드 `/tests/<module>_test.py` 작성
- **소통**: `/communications/requests/` 를 통해 PL에게 질문 및 리뷰 요청

### 🟩 PL
- 구조 설계 및 파일 시스템 통제
- `/main.py`, `README.md` 작성 및 통합 관리
- 코드 리뷰, 브랜치 병합, 배포/운영 관리
- **소통**: `/communications/announcements/` 를 통해 공지사항 전파

---

## 📋 3. 개발자 업무 프로세스

### ✅ 시작 전
- `/docs/spec.md` 및 `/interface/` 내 문서 숙지
- `/communications/announcements/` 공지 확인

### ✅ 개발 중
- 자신의 모듈 디렉토리 외 **타 영역 수정 금지**
- 함수/클래스에는 **docstring 작성 필수**
- 테스트 코드 동반 작성

### ✅ 완료 후
- `/communications/requests/` 에 리뷰 요청 파일 작성
  - `[To_PL_From_DevX]_[module]_리뷰요청.md`

---

## 🔐 4. Commit & Branching 전략

### Branching
- **`main`**: 최종 릴리즈 버전. 직접적인 commit 금지.
- **`develop`**: 개발 통합 브랜치. 모든 기능 브랜치의 최종 목적지.
- **`feature/<module>/<description>`**: 기능 개발 브랜치.
  - 예: `feature/stock/realtime-data-fetcher`

### Committing
- **커밋 메시지 형식**: `[<module>] <Subject>`
  - 예: `[stock] 실시간 데이터 Fetcher 클래스 구현`
- **PR (Pull Request)**: `feature` 브랜치에서 `develop` 브랜치로 요청.
  - PR 제목: `[<module>] 기능명 요약`
  - PR 본문: 변경 내용, 테스트 결과, 인터페이스 영향 여부 명시

---

## 📌 5. 핵심 원칙

- **모듈 책임 분리**: 자신이 맡은 디렉토리만 수정
- **문서 우선**: 명세 > 코드 > 통합
- **인터페이스 절대 준수**: 함부로 구조 변경 금지
- **단위 테스트 필수**: 모든 기능에 대한 테스트 작성
- **소통 기록**: 모든 요청과 공지는 `communications` 디렉토리에 기록

---

## 📎 참고

- 인터페이스 명세서: `/interface/`
- 전체 시스템 설계: `/docs/spec.md`
- 테스트 실행 방법: `pytest tests/`

---

## 🧠 교훈

> "명확한 책임 분리와 통합 기준이 있는 프로젝트는 팀 생산성을 극대화한다. 각자의 경계를 존중하되, 공통 기준은 강제하라."
## Actual Project Tree (Generated)

### Simulation

simulation
- __init__.py
- action_processor.py
- agents
- - central_bank.py
- - government.py
- ai
- - __init__.py
- - action_selector.py
- - ai_training_manager.py
- - api.py
- - engine_registry.py
- - enums.py
- - firm_ai.py
- - firm_system2_planner.py
- - government_ai.py
- - household_ai.py
- - household_system2.py
- - learning_tracker.py
- - model_wrapper.py
- - q_table_manager.py
- - reward_calculator.py
- - service_firm_ai.py
- - state_builder.py
- - system2_planner.py
- - vectorized_planner.py
- ai_model.py
- api.py
- bank.py
- base_agent.py
- brands
- - brand_manager.py
- components
- - agent_lifecycle.py
- - api.py
- - consumption_behavior.py
- - demographics_component.py
- - economy_manager.py
- - finance_department.py
- - hr_department.py
- - labor_manager.py
- - leisure_manager.py
- - market_component.py
- - production_department.py
- - psychology_component.py
- - sales_department.py
- core_agents.py
- core_markets.py
- db
- - database.py
- - db_manager.py
- - repository.py
- - schema.py
- decisions
- decisions.py
- - __init__.py
- - action_proposal.py
- - ai_driven_firm_engine.py
- - ai_driven_household_engine.py
- - base_decision_engine.py
- - corporate_manager.py
- - housing_manager.py
- - portfolio_manager.py
- - rule_based_firm_engine.py
- - rule_based_household_engine.py
- - standalone_rule_based_firm_engine.py
- dtos
- - __init__.py
- - api.py
- - firm_state_dto.py
- - scenario.py
- engine.py
- firms.py
- initialization
- - __init__.py
- - api.py
- - initializer.py
- interface
- - __init__.py
- - dashboard_connector.py
- interfaces
- - policy_interface.py
- loan_market.py
- markets
- - __init__.py
- - order_book_market.py
- - stock_market.py
- metrics
- - economic_tracker.py
- - inequality_tracker.py
- - stock_tracker.py
- models.py
- policies
- - smart_leviathan_policy.py
- - taylor_rule_policy.py
- portfolio.py
- schemas.py
- service_firms.py
- systems
- - __init__.py
- - api.py
- - bootstrapper.py
- - commerce_system.py
- - demographic_manager.py
- - event_system.py
- - firm_management.py
- - generational_wealth_audit.py
- - housing_system.py
- - immigration_manager.py
- - inheritance_manager.py
- - labor_market_analyzer.py
- - lifecycle_manager.py
- - ma_manager.py
- - ministry_of_education.py
- - persistence_manager.py
- - reflux_system.py
- - sensory_system.py
- - social_system.py
- - tax_agency.py
- - tech
- - technology_manager.py
- - transaction_processor.py
- tick_scheduler.py
- utils
- - __init__.py
- - golden_loader.py
- - shadow_logger.py
- viewmodels
- - agent_state_viewmodel.py
- - economic_indicators_viewmodel.py
- - market_history_viewmodel.py
- - snapshot_viewmodel.py
- world_state.py

### Modules

modules
- analysis
- - crisis_monitor.py
- analytics
- - __init__.py
- - loader.py
- common
- - config_manager
- finance
- - api.py
- - domain
- - system.py
- household
- - api.py
- - bio_component.py
- - dtos.py
- - econ_component.py
- - social_component.py
