The goal of this task is to execute a structural audit based on `design/3_work_artifacts/specs/AUDIT_SPEC_STRUCTURAL.md`. The audit requires scanning for God Classes (>800 lines of code) and tracing raw agent leaks into decision engines.

Here is the plan:
1.  **Analyze the current state**:
    -   We have already run an initial scan script that identified the following:
        -   **God Classes**:
            -   `simulation/firms.py: Firm (1765 lines)`
            -   `simulation/core_agents.py: Household (1181 lines)`
            -   `simulation/systems/settlement_system.py: SettlementSystem (966 lines)`
        -   **Abstraction Leaks (Raw Agent Leaks)**:
            -   `simulation/agents/government.py: run_welfare_check` and `execute_social_policy` and `run_public_education` accept `agents: List[Any]`
            -   `modules/government/api.py: run_welfare_check` accepts `agents: List[IAgent]`
            -   `modules/government/engines/execution_engine.py: execute`, `_execute_social_policy`, `_execute_firm_bailout` accept `agents: List[Any]`
            -   `modules/government/services/welfare_service.py: run_welfare_check` accepts `agents: List[IAgent]`

2.  **Generate the audit report**:
    -   Create a new file `reports/audit/AUDIT_REPORT_STRUCTURAL.md` following the template and guidelines in `AUDIT_SPEC_STRUCTURAL.md`.
    -   Include the God Classes found and their line counts.
    -   Document the abstraction leaks found in `modules/government` and `simulation/agents/government.py`, where `List[Any]` or `List[IAgent]` is passed directly to decision engines or services like `WelfareService` and `PolicyExecutionEngine`.
    -   Follow the required sections: `1. 용어 정의`, `2. 논리 전개`, `3. 구체적 방법 예시`, `4. 구조적 모듈 현황 진단`, `5. Output Configuration`.

3.  **Complete pre-commit steps**:
    -   Complete pre commit steps to make sure proper testing, verifications, reviews and reflections are done.

4.  **Submit the change**:
    -   Submit the newly created report.

