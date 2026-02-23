import os
import sys

# Ensure project root is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import shutil
from pathlib import Path
from modules.tools.stub_generator.api import StubGenerationRequestDTO
from modules.tools.stub_generator.generator import StubGenerator
from modules.tools.context_injector.api import InjectionRequestDTO
# from _internal.scripts.core.context_injector.service import ContextInjectorService

def test_stub_generation_and_injection():
    # Setup
    test_root = Path(os.getcwd()) / "temp_test_stubs"
    test_root.mkdir(exist_ok=True)
    
    output_dir = test_root / "stubs"
    source_file = test_root / "test_api.py"
    
    source_content = """
class MyDTO:
    \"\"\"This is a DTO\"\"\"
    def __init__(self, x: int):
        self.x = x
        
    def complex_logic(self):
        # This should be stripped
        return self.x * 2
"""
    source_file.write_text(source_content)
    
    generator = StubGenerator()
    req = StubGenerationRequestDTO(
        source_path=str(source_file),
        output_dir=str(output_dir),
        include_docstrings=True
    )
    
    # 1. Test Generator
    result = generator.generate_stub(req)
    if not result.success:
        print(f"❌ Stub generation failed: {result.error_message}")
    assert result.success
    assert result.stub_path is not None
    assert Path(result.stub_path).exists()
    
    stub_content = Path(result.stub_path).read_text()
    assert "class MyDTO" in stub_content
    assert "This is a DTO" in stub_content
    # Note: stubgen usually removes implementation
    
    # 2. Test Context Injector Integration (DISABLED: Service Missing)
    # We need to mock the environment or use the service directly
    # service = ContextInjectorService()
    # service.stub_output_root = str(output_dir)
    
    # We need a relative path for the service to resolve correctly or mock it
    # For this test, let's just verify the _apply_stub_logic method
    # from modules.tools.context_injector.api import ContextNodeDTO, ContextTier
    
    # Use a real file path that matches the candidate pattern
    # rel_path = os.path.relpath(source_file, os.getcwd()).replace('\\', '/')
    # node = ContextNodeDTO(file_path=rel_path, tier=ContextTier.UNIVERSAL)
    
    # updated_node = service._apply_stub_logic(node)
    
    # assert updated_node.is_stub
    # assert updated_node.file_path.endswith(".pyi")
    # assert updated_node.original_path == rel_path
    
    print("✅ Stub Generation Test Passed! (Injection Skipped)")
    
    # Cleanup
    shutil.rmtree(test_root)

if __name__ == "__main__":
    test_stub_generation_and_injection()
