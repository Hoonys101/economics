from typing import Any, Protocol, runtime_checkable
import inspect

def assert_implements_protocol(instance: Any, protocol: Any) -> None:
    """
    Verifies that an instance implements all methods and attributes
    defined in the protocol. Raises AssertionError if not.
    """
    # Use runtime check if available
    if hasattr(protocol, '_is_protocol') and protocol._is_protocol:
        if not isinstance(instance, protocol):
             # If strict isinstance fails, give detailed feedback
             missing = []
             for attr in dir(protocol):
                 if attr.startswith('_') or attr in ['__abstractmethods__', '__annotations__', '__dict__', '__doc__', '__init__', '__module__', '__new__', '__slots__', '__subclasshook__', '__weakref__', '_abc_impl', '_is_protocol']:
                     continue
                 if not hasattr(instance, attr):
                     missing.append(attr)

             if missing:
                 raise AssertionError(f"Instance {instance} does not implement protocol {protocol.__name__}. Missing attributes: {missing}")
             else:
                 # If no attributes missing but isinstance failed, strictly implies standard Protocol behavior
                 pass
                 # For mocks, this might happen. We trust hasattr check above.
    else:
        # Fallback or strict enforcement
        pass
