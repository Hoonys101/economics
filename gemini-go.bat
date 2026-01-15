@echo off
setlocal
:: ==============================================================================
:: Gemini-CLI HITL 2.0: Spec Drafting
:: ==============================================================================
::
:: +-------------------------------------------------------------------------+
:: |  ANTIGRAVITY SELF-REFERENCE MANUAL                                      |
:: |  Available workers: spec, git, verify, context, scribe                  |
:: |  Usage: python scripts/gemini_worker.py <worker> "<instruction>" -c ... |
:: |  OUTPUT: design\gemini_output\spec_draft.md                             |
:: +-------------------------------------------------------------------------+
::
:: ==============================================================================
:: [CURRENT CONTEXT]
:: Target: (Antigravity fills this dynamically)
:: Task: (Antigravity fills this dynamically)
:: ==============================================================================
set PYTHONIOENCODING=utf-8

if not exist "design\gemini_output" (
    mkdir "design\gemini_output"
)

echo [Gemini-CLI] Drafting spec...
echo ============================================================

:: [COMMAND SLOT]
:: Target: TD-024 Test Path Fix
:: Task: Pytest 경로 오류 진단 및 해결 Spec 작성

python scripts/gemini_worker.py spec "TD-024: Test Path Correction Spec. Mission: 'Phase 26 복잡 금융 로직 테스트 전, 검증 도구(Pytest)의 칼날을 갈아라.' Goals: 1) pytest 경로 오류 원인 진단 및 해결. 2) 로컬/CI 환경 모두에서 100% 신뢰성 있게 테스트가 실행되도록 보장. Include: 현재 디렉토리 구조 분석, conftest.py 점검, pytest.ini 또는 pyproject.toml 설정 확인, 해결 의사코드." -c tests/ conftest.py pyproject.toml pytest.ini setup.py > design\gemini_output\spec_draft.md 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Spec drafting failed.
) else (
    echo [SUCCESS] Spec draft saved to design\gemini_output\spec_draft.md
)
endlocal
