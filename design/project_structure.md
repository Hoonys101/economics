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