# Design Documentation Index

**최종 업데이트**: 2025-12-29
**상태**: Phase 1 Step 2 (Documentation Population) 완료

이 폴더는 프로젝트의 설계 및 관리 문서를 포함합니다. 모든 문서는 실제 코드베이스 분석을 기반으로 최신화되었습니다.

---

## 1. 핵심 설계 문서 (Core Specs)

| 문서 | 설명 | 분석 대상 코드 |
|---|---|---|
| [System Architecture](file:///c:/coding/economics/design/2_architecture/architecture.md) | 전체 시스템 구조 및 흐름 | `engine.py`, `repository.py` |
| [AI Agent Model](file:///c:/coding/economics/design/3_feature_design/ai_agent_model.md) | V2 Multi-Channel Aggressiveness AI | `ai/firm_ai.py`, `ai/household_ai.py` |
| [Firm Agent Spec](file:///c:/coding/economics/design/3_feature_design/firm_agent_design.md) | 기업 에이전트 채널별 로직 | `decisions/ai_driven_firm_engine.py` |
| [Household Agent Spec](file:///c:/coding/economics/design/3_feature_design/household_agent_design.md) | 가계 에이전트 채널별 로직 | `decisions/ai_driven_household_engine.py` |
| [Market Mechanism](file:///c:/coding/economics/design/3_feature_design/market_mechanism_design.md) | OrderBook 및 Stock 시장 | `markets/order_book_market.py`, `stock_market.py` |
| [Personality & Learning](file:///c:/coding/economics/design/3_feature_design/v2_agent_personality_and_learning_design.md) | 성격 기반 욕구 성장 | `core_agents.py`, `ai/enums.py` |
| [API Contract](file:///c:/coding/economics/design/api_contract.md) | 백엔드 API 명세 | `app.py`, `api.js` |

---

## 2. Folder Structure

| 폴더 | 내용 |
|---|---|
| `0_master_plan/` | 장기 비전 및 마스터 플랜 |
| `1_project_management/` | 프로젝트 관리, 상태 보고서 |
| `2_architecture/` | 시스템 아키텍처 |
| `3_feature_design/` | 개별 기능 상세 설계 (Specs) |
| `4_technical_design/` | 기술적 구현 상세 |
| `5_troubleshooting/` | 문제 해결 가이드 |
