import os
import time
import subprocess
import logging
from pathlib import Path
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor
from modules.tools.stub_generator.api import (
    IStubGenerator, StubGenerationRequestDTO, StubGenerationResultDTO
)

logger = logging.getLogger(__name__)

class StubGenerator(IStubGenerator):
    """
    Implementation of IStubGenerator using mypy's stubgen.
    """

    def generate_stub(self, request: StubGenerationRequestDTO) -> StubGenerationResultDTO:
        start_time = time.time()
        source_path = Path(request.source_path)
        
        if not source_path.exists():
            return StubGenerationResultDTO(
                source_path=str(source_path),
                stub_path=None,
                success=False,
                error_message=f"Source file not found: {source_path}"
            )

        # 1. Determine output path
        # We mirror the directory structure relative to PROJECT_ROOT in output_dir
        # For simplicity in this implementation, we'll use a flattened or mirrored structure
        # Based on the spec: Side-by-side or shadow directory
        output_dir = Path(request.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Mirror structure logic:
        # If source is c:/coding/economics/modules/finance/api.py
        # and output_dir is .gemini/stubs
        # result should be .gemini/stubs/modules/finance/api.pyi
        
        # Try to find common project root
        project_root = Path("c:/coding/economics")
        try:
            rel_path = source_path.relative_to(project_root)
        except ValueError:
            rel_path = Path(source_path.name)

        stub_path = (output_dir / rel_path).with_suffix(".pyi")
        stub_path.parent.mkdir(parents=True, exist_ok=True)

        # 2. Lazy check (caching)
        if stub_path.exists() and stub_path.stat().st_mtime >= source_path.stat().st_mtime:
            return StubGenerationResultDTO(
                source_path=str(source_path),
                stub_path=str(stub_path),
                success=True,
                is_cached=True,
                generation_time_ms=(time.time() - start_time) * 1000
            )

        # 3. Execution via stubgen
        try:
            # We use subprocess to call mypy stubgen
            # -o output_dir: we use a temp dir and then move to avoid stubgen's naming constraints
            # -p package: or just provide file
            # --include-docstrings
            
            cmd = [
                "stubgen",
                str(source_path),
                "-o", str(output_dir),
                "--no-import" # We want to keep it simple
            ]
            
            if request.include_docstrings:
                cmd.append("--include-docstrings")

            # Note: stubgen output path logic is slightly varied. 
            # It usually puts it in [output_dir]/filename.pyi
            # or [output_dir]/package/module.pyi if provided as package.
            # For simplicity, we'll let it run and then check if the file moved.
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return StubGenerationResultDTO(
                    source_path=str(source_path),
                    stub_path=None,
                    success=False,
                    error_message=f"stubgen failed: {result.stderr}",
                    generation_time_ms=(time.time() - start_time) * 1000
                )

            # Move/verify the expected stub_path
            # By default stubgen for a file might put it in [output_dir]/[filename].pyi
            # We want it to be mirrored. 
            # If stubgen put it elsewhere, we might need to find it.
            
            # Simple check:
            if not stub_path.exists():
                # Stubgen might have placed it just in output_dir
                generated_simple = output_dir / source_path.with_suffix(".pyi").name
                if generated_simple.exists() and generated_simple != stub_path:
                    os.replace(generated_simple, stub_path)

            if not stub_path.exists():
                return StubGenerationResultDTO(
                    source_path=str(source_path),
                    stub_path=None,
                    success=False,
                    error_message=f"stubgen succeeded but stub not found at expected location: {stub_path}",
                    generation_time_ms=(time.time() - start_time) * 1000
                )

            return StubGenerationResultDTO(
                source_path=str(source_path),
                stub_path=str(stub_path),
                success=True,
                generation_time_ms=(time.time() - start_time) * 1000
            )

        except Exception as e:
            return StubGenerationResultDTO(
                source_path=str(source_path),
                stub_path=None,
                success=False,
                error_message=f"Exception during stub generation: {str(e)}",
                generation_time_ms=(time.time() - start_time) * 1000
            )

    def batch_generate(self, requests: List[StubGenerationRequestDTO]) -> List[StubGenerationResultDTO]:
        with ThreadPoolExecutor(max_workers=os.cpu_count() or 4) as executor:
            results = list(executor.map(self.generate_stub, requests))
        return results
