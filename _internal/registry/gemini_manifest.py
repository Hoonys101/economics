"""
🤖 [ANTIGRAVITY] GEMINI MISSION MANIFEST
========================================

역할: 로직 분석, 아키텍처 설계, MISSION_spec 작성, 코드 감사 및 보고서 생성 (No Coding).
핵심 가치: "코드가 아닌 시스템의 지능과 정합성을 관리한다."

📋 WORKER TYPES (worker 필드에 사용)
  [Reasoning Tier - gemini-3-pro-preview]
    'spec'          : 구현 명세(MISSION_SPEC) 작성. Jules가 실행할 상세 설계 문서 생성.
    'git-review'    : PR Diff 분석. 코드 리뷰 보고서 생성 (git-go.bat에서 자동 사용).
    'context'       : 프로젝트 상태 요약 및 스냅샷 생성.
    'crystallizer'  : 인사이트 결정화. 분산된 보고서를 통합 지식으로 압축.

  [Analysis Tier - gemini-3-flash-preview]
    'audit'         : 코드/아키텍처 감사. 기술부채 및 구조적 결함 진단.
    'report'        : 데이터 분석 및 보고서 생성. 시뮬레이션 결과 해석.
    'verify'        : 코드 검증. 아키텍처 규칙 준수 여부 확인.

📋 FIELD SCHEMA (GEMINI_MISSIONS)
    title (str)                : 미션 제목.
    worker (str)               : 워커 타입 (위 목록 참조, 필수).
    instruction (str)          : 상세 지시 사항.
    context_files (list[str])  : 분석에 필요한 소스 코드/문서 경로 목록.
    output_path (str, Optional): 결과물 저장 경로.
    model (str, Optional)      : 모델 오버라이드.

⚙️ LIFECYCLE
    1. 이 파일에 미션을 작성합니다.
    2. `gemini-go <KEY>` 실행 시 미션이 JSON으로 이관되고, 이 파일은 자동 리셋됩니다.
    3. 미션 성공 시 JSON에서도 자동 삭제됩니다.
    4. `reset-go` 실행 시 JSON만 초기화됩니다 (이 파일은 보존).
"""
from typing import Dict, Any

GEMINI_MISSIONS: Dict[str, Dict[str, Any]] = {
    "WO-FIX-MONETARY-DELTA": {
        "title": "Stage 4: Monetary Supply Delta Analytical Audit",
        "worker": "audit",
        "instruction": "Analyze the -618M penny delta anomaly starting at Tick 1. Audit WorldState.calculate_total_money perimeter vs Bootstrapper injections.",
        "context_files": [
            "simulation/world_state.py",
            "simulation/initialization/initializer.py",
            "simulation/systems/bootstrapper.py",
            "reports/diagnostic_refined.md"
        ],
        "output_path": "reports/MONETARY_AUDIT_REPORT.md"
    },
}
