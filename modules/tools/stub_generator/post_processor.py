import re
from modules.tools.stub_generator.api import IStubPostProcessor

class StubPostProcessor(IStubPostProcessor):
    """
    Post-processes stubs to preserve critical information like field defaults.
    """

    def process(self, stub_content: str) -> str:
        # 1. Preserve field = ... instead of field: type if it represents a critical default
        # (Though .pyi usually uses ...)
        
        # 2. Cleanup: Remove excessive empty lines or internal comments if any
        
        # 3. Future: Use LibCST for robust transformations
        
        processed = stub_content
        
        # Example fix: Ensure 'from __future__ import annotations' is present
        if "from __future__ import annotations" not in processed:
            processed = "from __future__ import annotations\n" + processed

        return processed
