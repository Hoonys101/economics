# [To_Architect_Prime] 다음 작업 우선순위 확인 요청

**요청자**: Antigravity (Team Leader / Second Architect)  
**날짜**: 2026-01-16 22:23  
**상태**: 🔶 대기 (Awaiting Architect Decision)

---

## 1. 요약 (Executive Summary)

현재 **두 개의 상이한 작업 방향**이 존재합니다:

| 출처 | 지시 작업 | Phase |
|------|-----------|-------|
| `HANDOVER_2026-01-16.md` | **TD-008**: Advanced Finance System (Altman Z-Score) | Phase 27 |
| `설계도_계약들/specs/w2_dashboard_spec.md` | **W-2 대시보드 고도화** (Laffer Curve 실험 지원) | Phase 5 실험 |

수석 아키텍트의 **명확한 우선순위 결정**을 요청드립니다.

---

## 2. 현재 프로젝트 상태 (Context)

### 2.1 최근 완료된 작업 (Phase 27: Architecture Consolidation)
| Work Order | 내용 | 상태 |
|------------|------|------|
| WO-079 | Config Automation v2 (YAML 중앙 설정) | ✅ 완료 |
| TD-044 | Household God Class Refactoring (SoC) | ✅ 완료 |
| TD-045 | Firm God Class Refactoring (SoC) | ✅ 완료 |
| TD-046 | Hardcoded Constants Migration | ✅ 완료 |

### 2.2 핸드오버 문서 지시 (다음 작업)
```
## 3. 🚩 다음 세션 첫 번째 할 일 (Top Priority)
### [TD-008] Advanced Finance System (Altman Z-Score) 구현
- **상태**: 명세서(`design/specs/TD-008_Finance_Upgrade_Spec.md`) 작성 완료.
- **다음 작업**: 
    1. `command_registry.json`의 `jules` 섹션에 TD-008 미션 내용 '장전'.
    2. `.\jules-go.bat` 실행 요청하여 발주.
```

### 2.3 신규 발견된 작업 지시 (w2_dashboard_spec.md)
현재 워크스페이스에 열린 파일들이 **다른 방향**을 지시하고 있습니다:

**파일**: `설계도_계약들/specs/w2_dashboard_spec.md`
- **목표**: Phase 5 실험 결과(시간 배분, 래퍼 곡선 효과)를 실시간으로 모니터링하기 위한 대시보드 고도화
- **작성자**: Architect Prime / Antigravity (공동)

**명시된 작업 범위**:
| 담당자 | 작업 |
|--------|------|
| **Jules** | `dtos.py` 확장 및 `SnapshotViewModel` 집계 로직 고도화 |
| **Assistant** | `HUD.tsx`, `SocietyTab.tsx`, `GovernmentTab.tsx` 컴포넌트 수정 |

**추가할 HUD 지표**:
- `avg_tax_rate` (평균 실효세율) - 실험의 X값
- `avg_leisure_hours` (평균 여가 시간) - 실험의 Y값 1
- `parenting_rate` (육아 참여율) - 실험의 Y값 2

---

## 3. 충돌 분석 (Conflict Analysis)

### 3.1 방향성 차이
| 항목 | TD-008 (Altman Z-Score) | W-2 대시보드 고도화 |
|------|-------------------------|---------------------|
| **목적** | 금융 시스템 고도화 (기업 부도 예측) | 실험 UI 고도화 (Laffer Curve 시각화) |
| **대상 모듈** | `modules/finance/` | `frontend/`, `simulation/viewmodels/` |
| **우선순위 근거** | 핸드오버 문서 명시 | Spec 파일 발견 (미병합?) |

### 3.2 의존성 질문
- **Q1**: Phase 5 Laffer Curve 실험이 **TD-008 금융 지표**에 의존하는가?
  - 만약 의존한다면: TD-008 → W-2 순서
  - 독립적이라면: 병렬 진행 또는 별도 우선순위 결정 필요

- **Q2**: `w2_dashboard_spec.md`는 언제 작성된 것인가?
  - 핸드오버 이후 신규 기획인지, 이전에 작성되어 병합 대기 중인지 불명확

### 3.3 현재 프론트엔드 상태 점검
`App.tsx` 분석 결과, 이미 다음 지표들이 **HUD에 구현되어 있음**:
- `avg_tax_rate` (평균 세율) ✅
- `avg_leisure_hours` (평균 여가) ✅
- `parenting_rate` (육아 비율) ✅

→ 이미 Phase 5 지표가 일부 구현된 상태로, W-2 Spec이 **부분 완료**되었을 가능성이 있음.

---

## 4. 확인 요청 사항 (Questions for Architect Prime)

### 🔴 P1: 우선순위 결정
> **TD-008 (Altman Z-Score)** vs **W-2 대시보드 고도화** 중 어느 작업을 먼저 진행해야 합니까?

### 🟠 P2: W-2 Spec 상태 확인
> `w2_dashboard_spec.md`의 현재 상태는 무엇입니까?
> - [ ] 아직 착수하지 않음 (미발주)
> - [ ] 부분 완료 (HUD 지표 반영됨, 나머지 탭 미완료)
> - [ ] 완료 (핸드오버에서 누락)
> - [ ] 폐기 (더 이상 유효하지 않음)

### 🟡 P3: 의존성 확인
> Phase 5 Laffer Curve 실험 진행을 위해 **TD-008 금융 지표(Z-Score)**가 필요합니까?

### 🟢 P4: 역할 분담 재확인
> W-2 Spec에 명시된 역할 분담(Jules: Backend / Assistant: Frontend)이 여전히 유효합니까?
> 또는 Guardian Protocol에 따라 **전체를 Jules에게 발주**해야 합니까?

---

## 5. 제안 (Recommendation)

### Option A: TD-008 우선 (핸드오버 준수)
- **근거**: 핸드오버 문서가 최신 합의된 계획이므로 이를 따름.
- **결과**: W-2 대시보드 작업은 TD-008 완료 후 백로그로 이동.

### Option B: W-2 먼저 완료 (실험 지원 우선)
- **근거**: Phase 5 실험이 시급하고, 프론트엔드 작업은 이미 부분 완료됨.
- **결과**: 잔여 작업(GovernmentTab 등)만 빠르게 마무리 후 TD-008 착수.

### Option C: 병렬 진행
- **근거**: 두 작업이 서로 다른 모듈(Finance vs Frontend)을 대상으로 함.
- **결과**: W-2 Frontend는 Antigravity가, TD-008은 Jules가 동시 진행.
- **위험**: 리소스 분산으로 인해 집중도 저하 가능.

---

## 6. 후속 조치

수석의 결정 후:
1. **핸드오버 문서 업데이트**: 최신 우선순위 반영
2. **command_registry.json 장전**: 결정된 작업에 맞게 Jules 미션 구성
3. **Spec 상태 정리**: 폐기 또는 진행 중인 Spec 명확화

---

**Antigravity, Team Leader**  
*"준비가 전부다. 모호함은 기술부채의 원천."*
