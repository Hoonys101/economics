# 🔍 Git Diff Review: PH6-Watchtower-Scaffold

## 1. 🔍 Summary
This pull request introduces the initial scaffolding for the "Watchtower" frontend, a Next.js application designed to monitor the simulation in real-time. The changes include setting up the project structure, creating core dashboard pages (Overview, Finance, Politics, System), implementing a Zustand-based state management store with a WebSocket connector, and providing a comprehensive insight report and a Playwright verification script.

## 2. 🚨 Critical Issues
- **[Hard-Fail] Invalid CSS Content:** The file `watchtower/src/app/globals.css` contains hardcoded, Windows-style file paths (`@scripts\fix_test_imports.py "tailwindcss";` and `@design\3_work_artifacts\specs\D_REMEDIATION_TD116_117_118.md (...)`). These lines are not valid CSS and will cause the application build to fail. They must be removed.
- **[Hard-Fail] Broken TypeScript Path Alias:** The `tsconfig.json` defines the `paths` alias with a leading space: `" @/*"`. This is incorrect. Consequently, all aliased imports throughout the application (e.g., `import ... from " @/store/..."`) are broken and will cause module resolution to fail during compilation. The space must be removed from both the `tsconfig.json` definition and all import statements.
- **[Hard-Fail] Invalid `package.json` Keys:** In `watchtower/package.json`, several keys under `devDependencies` have a leading space (e.g., `" @tailwindcss/postcss"`). This is not valid and can cause issues with package management tools. These spaces must be removed.

## 3. ⚠️ Logic & Spec Gaps
- There are no significant logic or specification gaps *within the defined scope* of scaffolding. The code correctly anticipates a disconnected state from the backend, which aligns with the mission's scope. The primary logic gap—the missing WebSocket endpoint—has been correctly identified and documented in the insight report.

## 4. 💡 Suggestions
- The systematic errors with leading spaces in the `tsconfig.json` alias and `package.json` keys suggest a potential copy-paste or automated script issue. It would be beneficial to review the workflow that generated these files to prevent similar errors in the future.

## 5. 🧠 Implementation Insight Evaluation
- **Original Insight**:
  ```
  # Watchtower Frontend Implementation [PH6-WT-001]

  ## Technical Debt & Mismatches

  ### 1. Contract Divergence
  - **Severity:** HIGH
  - **Issue:** The TypeScript interface defined in `PH6_WATCHTOWER_CONTRACT.md` differs significantly from the existing Python DTO in `simulation/dtos/watchtower.py`.
  - **Detail:** Frontend Expectation: `politics.approval_rating` (number), `politics.party` (string enum). Backend DTO: `politics` is a Dict containing nested keys like `approval` and `status`.
  - **Impact:** Direct JSON serialization from the current backend DTO will fail schema validation or cause runtime errors in the frontend.
  - **Recommendation:** Update `simulation/dtos/watchtower.py` to match the agreed-upon `PH6-WT-001` contract, or implement an adapter layer.
  
  ### 2. Missing WebSocket Implementation
  - **Severity:** MEDIUM
  - **Issue:** The frontend attempts to connect to `ws://localhost:8000/ws/live`, but the backend WebSocket endpoint logic was not part of this mission's scope.
  ```
- **Reviewer Evaluation**: The insight report is **excellent**. The identification of the "Contract Divergence" between the frontend's TypeScript types and the backend's Python DTO is a critical architectural finding that correctly highlights a major integration risk. This demonstrates proactive analysis beyond the immediate task. The report is clear, actionable, and accurately assesses the severity of the issues.

## 6. 📚 Manual Update Proposal
The lesson from the "Contract Divergence" insight is valuable and should be generalized for the project's knowledge base.

- **Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`
- **Update Content**:
  ```markdown
  - **Debt ID:** TD-125
  - **현상 (Phenomenon):** Frontend-Backend Contract Mismatch. During the Watchtower UI scaffolding, a significant discrepancy was discovered between the data structure expected by the frontend TypeScript interfaces and the one provided by the backend Python DTOs.
  - **원인 (Cause):** Lack of a synchronized, single source of truth for the API contract before implementation. The frontend was built against a specification that was not reflected in the backend's data-producing code.
  - **해결 (Solution):** A follow-up mission is required to either update the backend DTO to match the contract or implement an Adapter Pattern to transform the data before it is sent to the client.
  - **교훈 (Lesson Learned):** API contracts between services (especially frontend-backend) must be rigorously synchronized before and during development. For future cross-language interfaces, consider using a shared schema definition (e.g., OpenAPI, Protobuf) to auto-generate types and prevent this class of error.
  ```

## 7. ✅ Verdict
**REQUEST CHANGES (Hard-Fail)**

While the planning, verification script, and insight documentation are of high quality, the submitted code contains multiple build-breaking configuration and syntax errors. The application in its current state is non-functional. The critical issues listed above must be resolved before this PR can be considered for approval.
