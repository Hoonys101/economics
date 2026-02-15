"""
🤖 [ANTIGRAVITY] GEMINI MISSION MANIFEST GUIDE (Manual)
=====================================================

1. POSITION & ROLE
   - 역할: 로직 분석, 아키텍처 설계, MISSION_spec 작성, 코드 감사 및 보고서 생성 (No Coding).
   - 핵심 가치: "코드가 아닌 시스템의 지능과 정합성을 관리한다."

5. SMART CONTEXT (New Feature)
   - 매뉴얼(.md) 내에 링크된 아키텍처 가이드 문항들은 미션 실행 시 자동으로 'context_files'에 장착됩니다.
   - 명시적으로 모든 파일을 나열하지 않아도 시스템이 워커의 전문 지식을 위해 관련 표준을 찾아 전달합니다.

4. FIELD SCHEMA (GEMINI_MISSIONS)
   - title (str): 미션의 제목.
   - worker (str): 특정 작업 페르소나 선택 (필수).
     * [Reasoning]: 'spec', 'git', 'review', 'context', 'crystallizer'
     * [Analysis]: 'reporter', 'verify', 'audit'
   - instruction (str): 상세 지시 사항.
   - context_files (list[str]): 분석에 필요한 소스 코드 및 문서 경로 목록.
   - output_path (str, Optional): 결과물 저장 경로.
   - model (str, Optional): 모델 지정 ('gemini-3-pro-preview', 'gemini-3-flash-preview').
"""
from typing import Dict, Any

GEMINI_MISSIONS: Dict[str, Dict[str, Any]] = {
    "worker-concept-audit": {
        "title": "워커별 역할 개념 정의 및 문서 참조 능력 검증 (장착됨)",
        "worker": "audit",
        "instruction": """
사용자의 혼란을 해소하기 위해 다음 개념적/실무적 질문에 대해 명확한 답변과 개선 가이드를 작성하라.

1. 'git' vs 'review' 워커의 차이점:
   - 각 워커의 주된 책임(Operator vs Reviewer)과 결과물의 차이를 기술하라.
2. 'verify' 및 'context' 워커의 실무 활용 시나리오:
   - 사용자가 이들을 언제, 어떻게 사용해야 하는지 구체적인 예시를 제시하라. (예: 설계 변경 전 context 요약, 구현 후 verify 검증 등)
3. 'spec' 및 'review' 워커의 문서 참조 능력 분석:
   - Gemini가 명세서 작성이나 리뷰 시 'context_files'에 포함된 대량의 문서를 어떻게 찾아 읽는지(RAG 또는 Full Context 활용 방식) 설명하라.
   - 사용자가 별도의 명령 없이도 Gemini에게 "관련 문서를 알아서 찾아 읽으라"고 지시했을 때 이것이 가능한지, 혹은 어떤 제약이 있는지 기술하라.

[결과물]
- 사용자가 한눈에 이해할 수 있는 '워커 활용 퀵 가이드'를 포함하라.
""",
        "context_files": [
            "_internal/scripts/gemini_worker.py",
            "_internal/registry/mission_protocol.py",
            "_internal/manuals/",
            "design/3_work_artifacts/specs/",
            "design/3_work_artifacts/audits/"
        ]
    },
    "dto-audit": {
        "title": "DTO 및 API 데이터 흐름 정합성 정밀 감사",
        "worker": "audit",
        "instruction": """
프로젝트 내 데이터 흐름의 혈관인 DTO(Data Transfer Object)와 신경망인 API(Interface) 간의 계약(Contract) 정합성을 면밀히 감사하라.

1. **DTO 무결성 분석**:
   - 정의된 DTO 필드들이 실제 비즈니스 로직(Service/API)에서 빠짐없이 소비되고 있는지, 혹은 불필요한 필드(Dead Data)가 존재하는지 확인하라.
   - `simulation/dtos/`의 공용 DTO와 `modules/*/dtos.py`의 모듈 전용 DTO 간의 관계가 명확한지, 중복 정의나 타입 불일치가 없는지 점검하라.

2. **API 계약 이행 분석**:
   - `api.py` (Interface)에 정의된 시그니처가 `service.py` (Implementation)에서 정확히 구현되고 있는지 확인하라.
   - 데이터 생산자(Producer)와 소비자(Consumer) 사이의 파이프라인에서 데이터가 누락되거나 변질될 가능성이 있는 구간을 식별하라.

3. **Layer Violation Check**:
   - DTO가 엔티티(Entity)나 로직을 포함하고 있지는 않은지(순수 데이터 컨테이너 원칙 위배) 확인하라.
   - 상위 모듈이 하위 모듈의 DTO를 직접 참조하는 등의 의존성 역전 원칙 위반 사례를 찾아라.

[결과물]
- 위반 사항이 발견된 파일과 라인을 구체적으로 명시한 감사 보고서를 작성하라.
- 개선 권고 사항을 리스크 레벨(Critical, High, Medium, Low)로 분류하여 제시하라.
""",
        "context_files": [
            # Core Shared DTOs
            "simulation/dtos/",
            "modules/common/dtos.py",
            
            # Module DTOs & APIs (Focus on Flow)
            "modules/finance/dtos.py", "modules/finance/api.py",
            "modules/household/dtos.py", "modules/household/api.py",
            "modules/government/dtos.py", "modules/government/api.py",
            "modules/firm/api.py", # Firm DTO might be in simulation/dtos
            
            # Service Implementations (Sample for usage check)
            "modules/finance/service.py",
            "modules/household/services.py",
            "modules/system/services/command_service.py" 
        ]
    }
}
