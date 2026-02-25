import ast
import os
import logging
from pathlib import Path
from typing import List, Set, Dict, Optional, Any

from modules.tools.context_injector.api import (
    IContextInjectorService, IContextStrategy, ContextTier, 
    ContextNodeDTO, InjectionRequestDTO, InjectionResultDTO
)

from modules.tools.stub_generator.api import IStubGenerator, StubGenerationRequestDTO
from modules.tools.stub_generator.generator import StubGenerator

logger = logging.getLogger(__name__)

class DependencyGraphStrategy(IContextStrategy):
    """
    AST-based strategy to discover structural dependencies.
    """
    def resolve(self, request: InjectionRequestDTO, current_nodes: Set[str]) -> List[ContextNodeDTO]:
        base_dir = Path(os.getcwd())
        resolved = []
        to_process = list(request.target_files)
        depth = 0
        max_depth = request.max_dependency_depth

        processed = set()

        while to_process and depth <= max_depth:
            next_batch = []
            for file_path in to_process:
                abs_path = (base_dir / file_path).resolve()
                if not abs_path.exists() or str(abs_path) in processed:
                    continue
                
                processed.add(str(abs_path))
                
                imports = self._get_imports(abs_path, base_dir)
                for imp_path in imports:
                    rel_imp = os.path.relpath(imp_path, base_dir).replace('\\', '/')
                    if rel_imp not in current_nodes:
                        node = ContextNodeDTO(
                            file_path=rel_imp,
                            tier=ContextTier.STRUCTURAL,
                            description=f"Dependency of {file_path}",
                            source_node=file_path
                        )
                        resolved.append(node)
                        current_nodes.add(rel_imp)
                        next_batch.append(rel_imp)
            
            to_process = next_batch
            depth += 1
            
        return resolved

    def _get_imports(self, file_path: Path, base_dir: Path) -> List[Path]:
        if not file_path.suffix == '.py':
            return []
            
        try:
            tree = ast.parse(file_path.read_text(encoding='utf-8'))
        except Exception as e:
            logger.warning(f"Failed to parse {file_path}: {e}")
            return []

        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module:
                    resolved = self._resolve_module(node.module, file_path.parent, base_dir, node.level)
                    if resolved:
                        imports.append(resolved)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    resolved = self._resolve_module(alias.name, file_path.parent, base_dir, 0)
                    if resolved:
                        imports.append(resolved)
        return imports

    def _resolve_module(self, module_name: str, current_dir: Path, base_dir: Path, level: int) -> Optional[Path]:
        parts = module_name.split('.')
        
        if level > 0:
            target_dir = current_dir
            for _ in range(level - 1):
                target_dir = target_dir.parent
            potential_path = target_dir.joinpath(*parts).with_suffix('.py')
        else:
            potential_path = base_dir.joinpath(*parts).with_suffix('.py')

        if potential_path.exists():
            return potential_path
        
        potential_dir = potential_path.with_suffix('') / "__init__.py"
        if potential_dir.exists():
            return potential_dir
            
        return None

class TestContextStrategy(IContextStrategy):
    """
    Tier 3: Discovery of related tests and conftest.py fixtures.
    """
    def resolve(self, request: InjectionRequestDTO, current_nodes: Set[str]) -> List[ContextNodeDTO]:
        if not request.include_tests:
            return []
            
        base_dir = Path(os.getcwd())
        resolved = []
        
        for file_path in request.target_files:
            p = Path(file_path)
            if p.suffix == '.py' and 'tests' not in p.parts:
                test_file = base_dir / "tests" / f"test_{p.name}"
                if test_file.exists():
                    rel_test = os.path.relpath(test_file, base_dir).replace('\\', '/')
                    if rel_test not in current_nodes:
                        resolved.append(ContextNodeDTO(rel_test, ContextTier.TESTING, f"Test for {p.name}"))
                        current_nodes.add(rel_test)
            
            if 'tests' in p.parts:
                curr = (base_dir / p).parent
                while curr != base_dir and curr.parts:
                    conf = curr / "conftest.py"
                    if conf.exists():
                        rel_conf = os.path.relpath(conf, base_dir).replace('\\', '/')
                        if rel_conf not in current_nodes:
                            resolved.append(ContextNodeDTO(rel_conf, ContextTier.TESTING, "Fixture collection"))
                            current_nodes.add(rel_conf)
                    curr = curr.parent
        return resolved

class DocumentationStrategy(IContextStrategy):
    """
    Tier 4: Pattern-based architectural manual injection.
    """
    def resolve(self, request: InjectionRequestDTO, current_nodes: Set[str]) -> List[ContextNodeDTO]:
        if not request.include_docs:
            return []
            
        mapping = {
            "modules/finance/": "design/1_governance/architecture/standards/FINANCIAL_INTEGRITY.md",
            "simulation/ai/": "design/1_governance/architecture/ARCH_AI_ENGINE.md",
            "simulation/orchestration/": "design/1_governance/architecture/ARCH_SEQUENCING.md",
            "tests/": "design/1_governance/architecture/standards/TESTING_STABILITY.md"
        }
        
        resolved = []
        for file_path in request.target_files:
            for pattern, manual in mapping.items():
                if pattern in file_path and manual not in current_nodes:
                    resolved.append(ContextNodeDTO(manual, ContextTier.DOCUMENTATION, "Architectural standard"))
                    current_nodes.add(manual)
        return resolved

class UniversalContractStrategy(IContextStrategy):
    """
    Tier 1 strategy for mandatory core contracts.
    """
    def resolve(self, request: InjectionRequestDTO, current_nodes: Set[str]) -> List[ContextNodeDTO]:
        universal = [
            "modules/system/api.py",
            "simulation/dtos/api.py",
            "design/2_operations/ledgers/TECH_DEBT_LEDGER.md"
        ]
        resolved = []
        for path in universal:
            if path not in current_nodes:
                resolved.append(ContextNodeDTO(
                    file_path=path,
                    tier=ContextTier.UNIVERSAL,
                    description="Core system contract"
                ))
                current_nodes.add(path)
        return resolved

class ContextInjectorService(IContextInjectorService):
    def __init__(self):
        self.strategies: List[IContextStrategy] = [
            UniversalContractStrategy(),
            DependencyGraphStrategy(),
            TestContextStrategy(),
            DocumentationStrategy()
        ]
        self.stub_generator: IStubGenerator = StubGenerator()
        self.stub_output_root = ".gemini/stubs"

    def analyze_context(self, request: InjectionRequestDTO) -> InjectionResultDTO:
        # 1. Collect all nodes using strategies
        current_paths = set(request.target_files)
        all_nodes = [
            ContextNodeDTO(file_path=f, tier=ContextTier.STRUCTURAL, description="Primary target")
            for f in request.target_files
        ]
        
        for strategy in self.strategies:
            nodes = strategy.resolve(request, current_paths)
            all_nodes.extend(nodes)
            
        # 2. Identify stub candidates
        stub_candidates = ["api.py", "dtos.py", "system.py", "service.py"]
        to_stub_requests = []
        node_mapping = {} # index in all_nodes -> request index

        for i, node in enumerate(all_nodes):
            if node.file_path.endswith(".py") and any(c in node.file_path for c in stub_candidates):
                abs_source = Path(os.getcwd()) / node.file_path
                to_stub_requests.append(StubGenerationRequestDTO(
                    source_path=str(abs_source),
                    output_dir=self.stub_output_root,
                    include_docstrings=True
                ))
                node_mapping[i] = len(to_stub_requests) - 1

        # 3. Batch generate stubs (Parallel)
        if to_stub_requests:
            stub_results = self.stub_generator.batch_generate(to_stub_requests)
            
            # 4. Update nodes with stub results
            final_nodes = []
            for i, node in enumerate(all_nodes):
                if i in node_mapping:
                    result = stub_results[node_mapping[i]]
                    if result.success and result.stub_path:
                        rel_stub = os.path.relpath(result.stub_path, os.getcwd()).replace('\\', '/')
                        final_nodes.append(ContextNodeDTO(
                            file_path=rel_stub,
                            tier=node.tier,
                            description=f"[STUB] {node.description or 'Interface Stub'}",
                            source_node=node.source_node,
                            is_stub=True,
                            original_path=node.file_path
                        ))
                    else:
                        final_nodes.append(node)
                else:
                    final_nodes.append(node)
        else:
            final_nodes = all_nodes

        return InjectionResultDTO(
            nodes=final_nodes,
            total_files=len(final_nodes),
            missing_files=[],
            strategy_used="Tiered-Orchestrator-Parallel-Stub"
        )
