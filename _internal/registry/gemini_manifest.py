"""
🤖 [ANTIGRAVITY] GEMINI MISSION MANIFEST GUIDE (Manual)
=====================================================

1. POSITION & ROLE
   - 역할: 로직 분석, 아키텍처 설계, MISSION_spec 작성, 코드 감사 및 보고서 생성 (No Coding).
   - 핵심 가치: "코드가 아닌 시스템의 지능과 정합성을 관리한다."

5. SMART CONTEXT (New Feature)
   - 매뉴얼(.md) 내에 링크된 아키텍처 가이드 문항들은 미션 실행 시 자동으로 'context_files'에 장착됩니다.
   - 명시적으로 모든 파일을 나열하지 않아도 시스템이 워커의 전문 지식을 위해 관련 표준을 찾아 전달합니다.
   - **MANDATORY**: DAO/DTO의 스키마 변경 시, 해당 DTO/DAO를 참조하는 모든 구현체(Call Sites)를 찾아 `context_files`에 포함하십시오.

4. FIELD SCHEMA (GEMINI_MISSIONS)
   - title (str): 미션의 제목.
   - worker (str): 특정 작업 페르소나 선택 (필수).
     * [Reasoning]: 'spec', 'git', 'review', 'context', 'crystallizer'
     * [Analysis]: 'reporter', 'verify', 'audit'
   - instruction (str): 상세 지시 사항.
   - context_files (list[str]): 분석에 필요한 소스 코드 및 문서 경로 목록.
   - output_path (str, Optional): 결과물 저장 경로 (예: gemini-output/spec/MISSION_name_SPEC.md).
   - model (str, Optional): 모델 지정 ('gemini-3-pro-preview', 'gemini-3-flash-preview').
"""
from typing import Dict, Any

GEMINI_MISSIONS: Dict[str, Dict[str, Any]] = {
    "MISSION_spec_liquidation_wave5": {
        "title": "Wave 5: Political Economy & Monetary Rules Spec",
        "worker": "spec",
        "instruction": "ARCH_POLITICAL_ECONOMY.md의 설계 철학을 바탕으로 고도화된 정치-통화 시스템 스펙을 작성하십시오.\n\n### 핵심 요구사항:\n1. **개별 투표 시스템 (Voting)**: `IPoliticalOrchestrator`를 완성하여 가계가 `VoteRecordDTO`를 발행하고, 이를 기반으로 정부 지지율 및 보상(Reward)이 결정되게 하십시오.\n2. **이익 집단 (Lobbying)**: `InterestGroup` 및 로비 파이프라인을 설계하여 기업이나 특정 집단의 로비가 정책 결정 가중치에 반영되게 하십시오.\n3. **정부 AI (Populist RL)**: 정부의 보상 함수를 단순 지표 중심에서 '투표자 만족도(Mandate Utility)' 중심으로 고도화하십시오.\n4. **중앙은행 (Cold Machine)**: 통화 정책 준칙을 전략 패턴(Strategy Pattern)으로 리팩토링하십시오. (Taylor, Friedman, McCallum 준칙 등 지원)\n5. **기술적 무결성**: 모든 금융 거래는 Penny Standard(int)를 준수하며, 정치적 격동 속에서도 Zero-Sum Integrity가 유지되어야 합니다.\n\n결과물은 모듈별(Government, Politik, Bank, AI)로 명확히 분리된 구현 가이드여야 합니다.",
        "context_files": [
            "docs/concepts/ARCH_POLITICAL_ECONOMY.md",
            "modules/government/api.py",
            "modules/government/dtos.py",
            "simulation/agents/government.py",
            "simulation/agents/central_bank.py",
            "simulation/agents/household.py",
            "simulation/ai/enums.py",
            "simulation/policies/smart_leviathan_policy.py",
            "simulation/ai/government_ai.py"
        ],
        "output_path": "gemini-output/spec/MISSION_liquidation_wave5_SPEC.md"
    },
    "MISSION_spec_wave5_politics": {
        "title": "Wave 5 Sub-Spec: Political Orchestration & Voting Infrastructure",
        "worker": "spec",
        "instruction": "MISSION_liquidation_wave5_SPEC.md를 바탕으로 정치 오케스트레이터의 상세 스펙을 작성하십시오.\n\n### 상세 지침:\n1. **API/DTO 규정**: `IPoliticalOrchestrator`, `VoteRecordDTO`, `LobbyingEffortDTO`, `PoliticalClimateDTO`의 최종 필드와 메서드 시그니처를 확정하십시오.\n2. **투표 로직 (Pseudocode)**: 가계가 자신의 효용(Utility)을 어떻게 평가하여 `approval_value`와 `primary_grievance`를 산출하는지에 대한 상세 알고리즘을 작성하십시오.\n3. **로비 시스템**: 기업의 로비 자금이 정부 국고로 Zero-Sum 이관되는 원자적 처리 절차를 명시하십시오.\n4. **방향성**: 'Head-count' 방식에서 'Weighted Vote' 방식으로의 전환 로직(Status/Wealth 가중치)을 상세히 기술하십시오.",
        "context_files": [
            "gemini-output/spec/MISSION_liquidation_wave5_SPEC.md",
            "docs/concepts/ARCH_POLITICAL_ECONOMY.md",
            "modules/government/api.py",
            "modules/government/dtos.py",
            "simulation/agents/household.py",
            "modules/government/politics_system.py"
        ],
        "output_path": "gemini-output/spec/MISSION_W5_POLITICS_DETAIL.md"
    },
    "MISSION_spec_wave5_gov_ai": {
        "title": "Wave 5 Sub-Spec: Populist Government AI & Reward Hardening",
        "worker": "spec",
        "instruction": "MISSION_liquidation_wave5_SPEC.md와 MISSION_W5_POLITICS_DETAIL.md를 바탕으로 정부 AI 브레인의 보상 함수 및 상태 공간 확장 스펙을 작성하십시오.\n\n### 상세 지침:\n1. **보상 함수 (Reward Hardening)**: `PoliticalClimateDTO.overall_approval_rating`(Politics Spec에서 정의됨)을 제1 보상으로, 거시 안정성을 제약(Penalty)으로 사용하는 구체적인 수학적 모델을 정의하십시오.\n2. **상태 공간 확장**: Q-Table에 '민심 상태'와 '로비 압력' 변수가 어떻게 discretize되어 인코딩되는지 명시하십시오.\n3. **학습 루프**: 정책 결정 후 지지율 변화가 AI의 다음 학습 단계에 반영되는 타임라인(Reward Lag)을 설계하십시오.\n4. **방향성**: 정부 AI가 '표를 얻기 위한 포퓰리즘' 행동을 하도록 유도하는 하이퍼파라미터 가이드를 포함하십시오.",
        "context_files": [
            "gemini-output/spec/MISSION_liquidation_wave5_SPEC.md",
            "gemini-output/spec/MISSION_W5_POLITICS_DETAIL.md",
            "simulation/ai/government_ai.py",
            "simulation/policies/smart_leviathan_policy.py"
        ],
        "output_path": "gemini-output/spec/MISSION_W5_GOV_AI_DETAIL.md"
    },
    "MISSION_spec_wave5_monetary": {
        "title": "Wave 5 Sub-Spec: Central Bank Multi-Rule Strategy Pattern",
        "worker": "spec",
        "instruction": "MISSION_liquidation_wave5_SPEC.md, MISSION_W5_POLITICS_DETAIL.md, 그리고 MISSION_W5_GOV_AI_DETAIL.md를 바탕으로 중앙은행의 전략 패턴 도입 및 다중 준칙 구현 스펙을 작성하십시오.\n\n### 상세 지침:\n1. **전략 패턴 (`IMonetaryRule`)**: Taylor, Friedman, McCallum 준칙의 구체적인 구현 클래스 구조와 인터페이스를 정의하십시오.\n2. **MonetaryEngine 리팩토링**: 기존 엔진이 특정 준칙에 의존하지 않고 주입된 전략을 매틱하게 실행하는 구조(`Decoupling`)를 설계하십시오.\n3. **M2 제어 메커니즘**: Friedman 준칙 등에서 M2 타겟 달성을 위해 채권 매입/매각(QE/QT)이 수행되는 원자적 로직을 기술하십시오.\n4. **방향성**: 중앙은행이 정치적 외풍에 흔들리지 않는 '수학적 닻'으로 동작하기 위한 엄격한 데이터 소스(SSoT) 활용 방안을 명시하십시오.",
        "context_files": [
            "gemini-output/spec/MISSION_liquidation_wave5_SPEC.md",
            "gemini-output/spec/MISSION_W5_POLITICS_DETAIL.md",
            "gemini-output/spec/MISSION_W5_GOV_AI_DETAIL.md",
            "simulation/agents/central_bank.py",
            "simulation/policies/taylor_rule_policy.py",
            "modules/finance/api.py"
        ],
        "output_path": "gemini-output/spec/MISSION_W5_MONETARY_DETAIL.md"
    },
    # Add missions here
}
