File: communications/insights/protocol-lockdown-spec.md
```markdown
# Insight Report: Protocol Enforcement & Lockdown

| **Mission Key** | `protocol-lockdown-spec` |
| :--- | :--- |
| **Worker** | Gemini-Scribe |
| **Date** | 2026-02-17 |

## 1. Architectural Insights & Decisions

### 1.1. The "Private Access" Paradox
- **Observation**: Current Agents (Households/Firms) expose public attributes like `.inventory` and `.wallet` (Legacy behavior).
- **Issue**: Engines (`SalesEngine`, `FinanceEngine`) often access these directly, violating the **SEO Pattern** (Stateless Engine, Orchestrator).
- **Decision**: We cannot simply rename them to `_inventory` immediately without breaking the entire simulation.
- **Strategy**: Instead of runtime renaming, we will implement **Static AST Analysis** to forbid access to these attributes *outside* of the Agent's own module or specific DTOs.

### 1.2. Technical Debt Identification (New)
- **ID**: `TD-TOOL-AST-PARSER`
- **Description**: We lack a centralized AST parsing utility. Ad-hoc regex searches in `scripts/` are fragile.
- **Action**: The Lockdown tool should act as the foundational "Linter" for architectural rules, extensible for future rules (e.g., "No float math").

### 1.3. Existing Debt Alignment
- **TD-INT-PENNIES-FRAGILITY**: The lockdown script will explicitly flag usage of `hasattr(x, 'xxx_pennies')` to force migration to strict types.
- **TD-CRIT-FLOAT-SETTLE**: The script will flag assignment of `float` values to fields annotated as `int` (heuristic check).

## 2. Risk Assessment
- **False Positives**: AST checks might flag legitimate internal usage if not scoped correctly (e.g., `self.inventory` inside `Household` is fine).
- **Mitigation**: The rule engine must distinguish `self.access` from `instance.access`.

```

File: modules/architecture/api.py
```python
from __future__ import annotations
from enum import IntEnum, auto
from dataclasses import dataclass
from typing import List, Protocol, Optional, TypedDict

class ViolationSeverity(IntEnum):
    """
    Severity level of the architectural violation.
    """
    INFO = 0        # Style suggestion (e.g., "Consider using DTO")
    WARNING = 1     # Potential debt (e.g., "Float usage detected")
    ERROR = 2       # Pattern violation (e.g., "Direct attribute access")
    CRITICAL = 3    # Hard rule break (e.g., "Magic money creation")

@dataclass(frozen=True)
class CodeViolationDTO:
    """
    Data Transfer Object representing a single architectural violation found in the codebase.
    """
    rule_id: str
    file_path: str
    line_number: int
    column_offset: int
    message: str
    severity: ViolationSeverity
    context_code: str
    suggestion: Optional[str] = None

@dataclass(frozen=True)
class ArchitectureScanResultDTO:
    """
    Summary of a full architectural scan execution.
    """
    total_files_scanned: int
    total_violations: int
    violations: List[CodeViolationDTO]
    critical_count: int
    duration_ms: float
    success: bool  # True if critical_count == 0

class ScanContextDTO(TypedDict):
    """
    Context passed to individual rules during AST traversal.
    """
    file_path: str
    module_name: str
    is_test_file: bool
    source_code: str

class IArchitecturalRule(Protocol):
    """
    Interface for a single architectural enforcement rule.
    Uses AST analysis to detect violations.
    """
    @property
    def rule_id(self) -> str: ...

    @property
    def description(self) -> str: ...

    def check(self, tree: Any, context: ScanContextDTO) -> List[CodeViolationDTO]:
        """
        Analyzes the AST tree and returns a list of violations.
        """
        ...

class IArchitectureScanner(Protocol):
    """
    Interface for the main scanning engine.
    """
    def register_rule(self, rule: IArchitecturalRule) -> None: ...
    
    def scan_file(self, file_path: str) -> List[CodeViolationDTO]: ...
    
    def scan_directory(self, root_path: str, ignore_patterns: List[str]) -> ArchitectureScanResultDTO: ...
```

File: design/3_work_artifacts/specs/protocol_lockdown_spec.md
```markdown
# Spec: Architectural Protocol Lockdown (Phase 15)

## 1. Overview
This specification details the implementation of a **Static Analysis Tool (The "Architect's Hammer")** designed to enforce the project's strict architectural patterns—specifically the **SEO Pattern** (Stateless Engine & Orchestrator) and **Purity Rules**.

Unlike standard linters (Ruff/Flake8) which focus on syntax and PEP8, this tool enforces **Semantic & Structural Rules** unique to our simulation engine.

### Goals
1.  **Block Attribute Leaks**: Prevent external engines from accessing private Agent state (e.g., `agent.inventory`) directly.
2.  **Enforce Type Discipline**: Flag usage of `float` in financial contexts where `int` (Pennies) is required.
3.  **Deprecate Dynamic Access**: Ban `hasattr` and `getattr` on DTOs and Agents to solve **TD-INT-PENNIES-FRAGILITY**.

## 2. Technical Design

### 2.1. Component Structure
The system will be implemented as a standalone script package `modules/architecture/` invoked via `scripts/audit_architecture.py`.

- **Scanner Engine**: Iterates over files, parses AST.
- **Rule Registry**: Collection of `IArchitecturalRule` implementations.
- **Reporting**: Generates a GitHub-friendly Markdown report and exits with non-zero status on violations.

### 2.2. Core Rules (AST Logic)

#### Rule 1: `SEO-001` (Engine Purity)
- **Target**: Files in `simulation/components/engines/`
- **Logic**:
    - Visit `Attribute` nodes.
    - If accessing `.inventory`, `.wallet`, `.assets` on an object that is NOT `state` (DTO) or `self`.
    - **Violation**: "Direct access to Agent state detected in Engine. Use DTO or defined Interface."
    - **Exception**: Accessing properties of `context` or `state` arguments is allowed.

#### Rule 2: `DTO-001` (No Dynamic Access)
- **Target**: All `modules/**` and `simulation/**`
- **Logic**:
    - Visit `Call` nodes.
    - If func name is `hasattr` or `getattr`.
    - **Violation**: "Dynamic attribute access prohibited. Use strict Types/Interfaces." (Ref: TD-INT-PENNIES-FRAGILITY)

#### Rule 3: `FIN-001` (Float Containment)
- **Target**: `modules/finance` and `simulation/components/engines`
- **Logic**:
    - Visit `AnnAssign` (Type Annotation) nodes.
    - If annotation is `float` and variable name contains `price`, `cost`, `budget`, `balance`.
    - **Violation**: "Currency field typed as float. Must use int (Pennies)." (Ref: TD-CRIT-FLOAT-SETTLE)

### 2.3. Configuration & Exclusions
The tool will read `pyproject.toml` (or a dedicated `architecture.toml`) for exclusions.
```toml
[tool.gemini.architecture]
ignore = [
    "tests/**",          # Tests are allowed to probe internals (mostly)
    "scripts/**",        # Admin scripts have God-mode privileges
    "legacy/**"          # Ignore legacy folder until migration
]
```

## 3. Implementation Steps

### Phase 1: The Scanner Core (Jules Mission 1)
1.  Create `modules/architecture/scanner.py` implementing `IArchitectureScanner`.
2.  Create `modules/architecture/rules/base.py`.
3.  Implement CLI entry point `scripts/audit_architecture.py`.

### Phase 2: Rule Implementation (Jules Mission 2)
1.  Implement `SEO-001` (Private Access).
2.  Implement `DTO-001` (No Hasattr).
3.  Verify against `simulation/components/engines/sales_engine.py` (Should pass or flag known debts).

### Phase 3: CI Integration (Antigravity Task)
1.  Add `python scripts/audit_architecture.py` to GitHub Actions / Pre-commit hooks.
2.  Update `QUICKSTART.md` with instructions on how to run the audit locally.

## 4. Verification Plan

### 4.1. Self-Testing (The "Linter Test")
We will create a "Bad Code Fixture" to verify the scanner catches violations.

```python
# tests/architecture/fixtures/bad_engine.py
class BadEngine:
    def process(self, agent):
        # SEO-001 Violation
        agent.inventory['apple'] -= 1 
        
        # DTO-001 Violation
        if hasattr(agent, 'wallet'): 
            pass
```

### 4.2. Verification Command
```bash
# Verify the scanner catches the bad fixture
pytest tests/modules/architecture/test_scanner.py
```

### 4.3. Success Metrics
- Scanner correctly identifies 100% of seeded violations in `bad_engine.py`.
- Scanner runs on the entire `simulation/` directory in under 5 seconds.

## 5. Mocking Strategy
- **AST Nodes**: We do not mock AST nodes; we parse actual strings using `ast.parse()`.
- **File System**: Use `pyfakefs` or temporary directories for testing file iteration logic.

## 6. Debt Audit
- **TD-INT-PENNIES-FRAGILITY**: This tool is the *direct implementation mechanism* to resolve this debt by flagging all occurrences.
- **Pre-requisite**: None. This tool is additive.
```