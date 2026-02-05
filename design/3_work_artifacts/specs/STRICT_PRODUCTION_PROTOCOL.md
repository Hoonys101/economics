# Protocol: Strict Frontend Production (v1.0)

To resolve the "Hard-Fail" issues encountered by Jules, all frontend development missions must now adhere to the following **Zero-Tolerance Protocol**.

## 1. Pre-Flight Verification (Mandatory)
Before submitting a PR, Jules MUST execute the following check:
- **Build Cleanliness**: Run `npm run build` or `tsc --noEmit` within the project directory.
- **Fail Rule**: Any error in the build process is an absolute blocker. No "Work in Progress" code with syntax errors allowed.

## 2. Configuration Integrity
- **JSON Standard**: No leading spaces in keys in `package.json` or `tsconfig.json`.
- **CSS Hygiene**: CSS files must contain ONLY valid CSS rules. No Python paths, script fragments, or markdown content allowed.
- **Path Aliases**: Direct use of `@/` aliases is mandatory. Leading spaces (e.g., ` @/`) are strictly forbidden.

## 3. Contract Realism (TD-125)
- **Zero Divergence**: Before coding components, verify that the `interface` matches the Golden Sample JSON (`watchtower_full_mock_v2.json`).
- **Adapter Requirement**: If the Backend DTO structure is unsatisfactory, an `adapter.ts` MUST be implemented to transform data before state injection.

## 4. Submission Checklist
- [ ] `tsc --noEmit` passed?
- [ ] No Python paths in CSS?
- [ ] No leading spaces in JSON keys?
- [ ] TS Types aligned with the Golden Sample?
