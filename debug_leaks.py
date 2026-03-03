import gc
import sys
from collections import Counter
from unittest.mock import MagicMock

def check_leaks():
    print("--- Memory Leak Diagnostic ---")
    gc.collect()
    
    # Check for MagicMock objects
    all_objects = gc.get_objects()
    mock_count = 0
    for obj in all_objects:
        if isinstance(obj, MagicMock):
            mock_count += 1
    
    print(f"Total MagicMock objects in memory: {mock_count}")
    
    # Check for large lists/dicts
    large_collections = []
    for obj in all_objects:
        try:
            if isinstance(obj, (list, dict, set)) and len(obj) > 1000:
                large_collections.append((type(obj), len(obj), str(obj)[:100]))
        except:
            continue
            
    print(f"Large collections (>1000 items): {len(large_collections)}")
    for coll in sorted(large_collections, key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {coll[0]}: {coll[1]} items | {coll[2]}...")

    # Check for common leak targets
    try:
        from modules.finance.kernel.ledger import MonetaryLedger
        ledgers = [obj for obj in all_objects if isinstance(obj, MonetaryLedger)]
        print(f"Total MonetaryLedger objects: {len(ledgers)}")
    except ImportError:
        pass

if __name__ == "__main__":
    check_leaks()
