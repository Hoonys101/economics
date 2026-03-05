# Context Metadata Injection Policy Design (WO-SPEC-CONTEXT-METADATA)

## 1. Architectural Insights & Design
The goal is to append actionable metadata guidelines to context files before passing them into the LLM context window. To respect the Single Responsibility Principle (SRP) and keep resolution decoupled from presentation, we introduce a formatting layer: `IContextFormatter`.

### Proposed Classes & Modules:
1.  **`_internal/scripts/core/context_injector/api.py`**
    -   Introduce `FormattedContextNodeDTO` to hold the final injected text.
    -   Introduce `IContextFormatter` Protocol.
2.  **`_internal/scripts/core/context_injector/formatter.py` (New File)**
    -   Implement `ContextFormatter` conforming to `IContextFormatter`.
    -   Responsible for taking `ContextNodeDTO`s and the raw file content, evaluating the `.tier` and `.is_stub` attributes, and prepending the required Markdown header block.
3.  **`_internal/scripts/gemini_worker.py`**
    -   Modify `run_gemini()` to utilize `ContextInjectorService` and `ContextFormatter` instead of blindly reading `context_files` from disk as raw text strings.

## 2. API & DTO Outlines

### `_internal/scripts/core/context_injector/api.py`
```python
from dataclasses import dataclass
from typing import Protocol, List
from pathlib import Path

@dataclass
class FormattedContextNodeDTO:
    """
    Represents a context node that has been formatted with metadata guidelines.
    """
    original_node: 'ContextNodeDTO'
    formatted_content: str

@runtime_checkable
class IContextFormatter(Protocol):
    """
    Protocol for formatting context nodes with tier-specific guidelines.
    """
    def format_node(self, node: 'ContextNodeDTO', raw_content: str) -> FormattedContextNodeDTO:
        ...
        
    def build_context_block(self, nodes: List['ContextNodeDTO'], base_dir: Path) -> str:
        ...
```

### `_internal/scripts/core/context_injector/formatter.py`
```python
from pathlib import Path
from typing import List
from _internal.scripts.core.context_injector.api import (
    IContextFormatter, ContextNodeDTO, FormattedContextNodeDTO, ContextTier
)

class ContextFormatter(IContextFormatter):
    def _get_guideline(self, node: ContextNodeDTO) -> str:
        if node.is_stub:
            return "INTERFACE REFERENCE ONLY. This file is a stub (`.pyi`) injected to reduce token usage. Do not attempt to modify it. Use it only to understand available methods, types, and docstrings of dependencies."
        
        guidelines = {
            ContextTier.UNIVERSAL: "MANDATORY CORE CONTRACT. Any modifications or new logic must strictly adhere to these interfaces and rules.",
            ContextTier.TESTING: "VERIFICATION CONTEXT. Use this to understand current test coverage and expected behaviors. Do not break these tests.",
            ContextTier.DOCUMENTATION: "ARCHITECTURAL RULEBOOK. Follow the principles outlined in this document."
        }
        return guidelines.get(node.tier, "STRUCTURAL DEPENDENCY. Use this for context on imported modules and dependencies.")

    def format_node(self, node: ContextNodeDTO, raw_content: str) -> FormattedContextNodeDTO:
        tier_name = node.tier.name
        role_desc = f"Tier {node.tier.value} ({tier_name.capitalize()})"
        if node.is_stub:
            role_desc += " [STUB]"

        guideline = self._get_guideline(node)
        formatted_text = (
            f"# {'='*42}\n"
            f"# FILE: {node.file_path}\n"
            f"# ROLE: {role_desc}\n"
            f"# GUIDELINE: {guideline}\n"
            f"# {'='*42}\n"
            f"{raw_content}"
        )
        return FormattedContextNodeDTO(node, formatted_text)

    def build_context_block(self, nodes: List[ContextNodeDTO], base_dir: Path) -> str:
        context_block = "\n\n<CONTEXT_FILES>\n"
        for node in nodes:
            abs_path = base_dir / node.file_path
            if abs_path.exists() and abs_path.is_file():
                raw_content = abs_path.read_text(encoding='utf-8')
                formatted_node = self.format_node(node, raw_content)
                context_block += f'<FILE path="{node.file_path}">\n{formatted_node.formatted_content}\n</FILE>\n'
        context_block += "</CONTEXT_FILES>\n"
        return context_block
```

### `_internal/scripts/gemini_worker.py` (Integration Logic)
```python
# Modifications in BaseGeminiWorker.run_gemini

# 1. Imports Added
from _internal.scripts.core.context_injector.api import InjectionRequestDTO
from _internal.scripts.core.context_injector.service import ContextInjectorService
from _internal.scripts.core.context_injector.formatter import ContextFormatter

# 2. Replaced Context Building Logic
context_block = "\n\n<CONTEXT_FILES>\n</CONTEXT_FILES>\n"

if context_files:
    try:
        # Determine worker type (fallback to 'spec' if undefined)
        worker_type = getattr(self, "worker_type", "spec")
        
        # 1. Resolve nodes via context injector
        injector = ContextInjectorService()
        request = InjectionRequestDTO(target_files=context_files, worker_type=worker_type)
        injection_result = injector.analyze_context(request)
        
        # 2. Format nodes into context block
        formatter = ContextFormatter()
        context_block = formatter.build_context_block(injection_result.nodes, BASE_DIR)
        
        print(f"📖 Attached {len(injection_result.nodes)} context files using Smart Context Injector.")
    except Exception as e:
        print(f"⚠️ Context Injection failed: {e}")
```

## 3. Tech Debt & Risk Assessment (Pre-Implementation Audit)
- **Token Overhead**: Adding a ~5-line header to every injected file increases token usage slightly. For 20 injected files, this translates to roughly ~1000 extra characters (approx 250 tokens). The strict token budget limit implemented in `ContextInjectorService._apply_token_budget` safely handles total file restrictions to prevent blowing up context sizes.
- **DTO Adherence**: The creation of `FormattedContextNodeDTO` cleanly isolates formatted state strings from the pure configuration mapping of `ContextNodeDTO`, adhering strictly to DTO Purity rules.
- **Protocol Purity**: The extraction of template formatting to an explicit `IContextFormatter` protocol respects Logic Separation and prevents UI/Text formatting concerns from leaking into the data resolution layers of the Context Injector.

## 4. Regression Analysis & Testing Mandate
- **No API Breakage**: `ContextInjectorService.analyze_context` interface behavior remains completely unchanged, guaranteeing existing external call sites do not drift.
- **Testing Fidelity**: 
  - Ensure integration tests parsing `gemini_worker.py` prompts are resilient to the newly introduced text headers within `<FILE path="...">` XML blocks.
  - Test evidence must demonstrate that existing AST and dependency tree extraction functionality is not halted by formatting exceptions.

## 5. Implementation Command Path
Once ready for execution, developers must ensure tests complete with absolute parity:
```bash
pytest tests/
```
Output literal evidence of this pass rate in the final handover to validate protocol obedience.