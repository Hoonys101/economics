# 📁 프로젝트 구조 및 업무 지침서 (v3.0)

---

## 📦 1. 프로젝트 파일 시스템 구조 (Antigravity Era)

```bash
/project-root/
│
├── _internal/              # ⚙️ 시스템 핵심 로직 및 백엔드 서비스
│   ├── registry/           # 미션 매니페스트 및 서비스 등록부
│   ├── scripts/            # Gemini/Jules 워커 실행 및 도구 스크립트
│   └── manuals/            # 각 워커별 페르소나 매뉴얼 (.md)
│
├── design/                 # 🏛️ 거버넌스 및 설계 (설계자/PL 전담)
│   ├── 1_governance/       # 아키텍처 원칙, 프로젝트 구조, 로드맵
│   ├── 2_operations/       # 기술 부채 관리, 세션 원장, 운영 가이드
│   ├── 3_work_artifacts/   # 미션 결과물 (Spec, Audit reports, Drafts)
│   └── 4_hard_planning/    # 위기 관리 및 중장기 전략 기획
│
├── modules/                # 🧱 비즈니스 도메인 모듈 (개발자 전담)
│   ├── finance/            # 금융 시스템, 은행, 정산
│   ├── government/         # 조세, 재정 정책
│   ├── household/          # 가계 소비, 노동 공급
│   └── ...                 # 기타 도메인별 기능
│
├── simulation/             # 🌍 시뮬레이션 엔진 및 공통 프레임워크
│   ├── core_agents.py      # 에이전트 베이스 클래스
│   ├── systems/            # 월드 시스템 (Settlement, Sensory 등)
│   └── components/         # 에이전트 부품 (Lifecycle, Demographics)
│
├── communications/         # 💬 팀 소통 및 로그 기록
│   ├── insights/           # 주요 의사결정 기록 (AID)
│   └── jules_logs/         # Jules 실행 상세 로그
│
├── tests/                  # ✅ 품질 검증 (Unit, Integration)
│
├── README.md               # 🗂️ 프로젝트 개요 및 운영 철학
├── main.py                 # 🚀 시뮬레이션 서버 진입점
└── *-go.bat                # ⚡ Antigravity 운영 런처 (gemini-go, jules-go 등)
```

---

## 🧭 2. 주요 디렉토리 책임

### 🔷 `_internal/` (System Core)
- **registry**: 미션의 장착(Mounting)과 상태 관리를 담당합니다.
- **scripts**: AI 에이전트와의 브릿지 역할을 하며, 자동화된 도구들을 포함합니다.
- **manuals**: 각 AI 워커가 수행해야 할 업무의 페르소나와 표준 절차를 규정합니다.

### 🔶 `design/` (Governance & Artifacts)
- **1_governance**: 프로젝트의 헌법과 같은 아키텍처 규칙이 보관됩니다.
- **2_operations**: **기술 부채(Tech Debt)** 및 **인사이트(Insights)**를 관리하여 지식의 영속성을 보장합니다.
- **3_work_artifacts**: 모든 협업 결과물(Spec, Audit)이 저장되는 '작업장'입니다.

### 📂 `modules/` & `simulation/` (Implementation)
- **modules**: 경제 도메인별 구체적 로직이 구현됩니다.
- **simulation**: 시뮬레이션의 인프라와 에이전트의 공통 행동 양식을 정의합니다.

---

## 📋 3. 운영 원칙 (Antigravity Protocol)

1. **Hierarchy of Truth**: `design/1_governance`의 원칙은 코드 구현보다 상위에 존재합니다.
2. **Artifact-Driven Development**: 모든 개발 작업은 `design/3_work_artifacts` 내의 `MISSION_spec`에서 시작되어야 합니다.
3. **Debt Second, Quality First**: 모든 작업 완료 후 발생하는 잔여 부채는 반드시 `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`에 기록됩니다.
4. **Internal Isolation**: `_internal/` 폴더 내의 로직은 사용자가 직접 수정하기보다 AI 도구를 통해 관리되는 것을 지향합니다.

---

## 🧠 교훈

> "구조가 지능을 결정한다. 정리된 파일 시스템은 AI 에이전트의 맥락 파악 능력을 비약적으로 향상시킨다."