@echo off
setlocal
:: 터미널 출력 및 인자 전달 인코딩을 UTF-8로 설정
chcp 65001 > nul
set PYTHONIOENCODING=utf-8
:: ==============================================================================
:: Gemini-CLI HITL 2.0: Spec Drafting
:: ==============================================================================
::
:: +-----------------------------------------------------------------------------+
:: |  ANTIGRAVITY SELF-REFERENCE MANUAL                                          |
:: |  Available workers: spec, git, verify, context, scribe, audit               |
:: |  Usage: python scripts/gemini_worker.py <worker> "<instruction>" -c ...     |
:: |  << DIR CONTEXT >>: Dir path is allowed for -c (Auto-recurse all .py)       |
:: |  OUTPUT: design\gemini_output\spec_draft.md (or designated file)            |
:: +-----------------------------------------------------------------------------+
::
:: ==============================================================================
:: [CURRENT CONTEXT]
:: Target: [TD-007 Planning] Stress Test Config Automation & Migration
:: Task: Centralize Hardcoded Simulation Thresholds into config.py
:: ==============================================================================
set PYTHONIOENCODING=utf-8

if not exist "design\gemini_output" (
    mkdir "design\gemini_output"
)

echo [Gemini-CLI] Drafting Stress Test Config spec...
echo ============================================================

:: [COMMAND SLOT]
:: Target: WO-079 (Config Automation) - Action: DRAFT WORK ORDER
set JOB_ID=WO-079_Config_Automation
python scripts/gemini_worker.py spec "Draft 'design/work_orders/WO-079_Config_Automation.md' based on the 'Phase 2: Configuration Automation' section of the attached spec. Context: WO-078 (Engine SoC) is completed. Focus on TD-007 (Hardcoded Constants). Define 'SimulationConfig' class in 'simulation/config.py', JSON profile loading, and migration of constants from 'simulation/engine.py' & 'simulation/firms.py'. Include 'test_config_loading.py' blueprint." -c design/gemini_output/stress_test_config_spec.md > design\work_orders\WO-079_Config_Automation.md 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Gemini task execution failed. Check logs.
) else (
    echo [SUCCESS] Gemini spec drafting with Auto-Audit completed. Check design\gemini_output\household_soc_spec.md
)
endlocal
