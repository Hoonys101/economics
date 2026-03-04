# Mock Containment 2: Spec-enforce tests/utils/factories.py

## 1. Architectural Insights
The transition from `MagicMock` to `Mock` for core domain entities and configuration objects is a crucial step towards 'Mock Containment'. `MagicMock` automatically implements and returns values for magic methods like `__iter__`, `__len__`, `__getitem__`, and many others. This auto-generation can lead to deceptive test behavior where an object is silently treated as iterable or len-able when the real implementation is not. In this mission, applying `Mock` instead of `MagicMock` in the core factory defaults prevents configurations (which are DTOs/dictionaries) from being implicitly treated as iterables without failing fast, exposing potential logic gaps in test setups.

A prime example encountered was the `Bootstrapper` failing during `Firm` creation because it attempted `firm.specialization in config.GOODS`. With a `MagicMock`, iterating or checking containment silently succeeded, masking the fact that the `config` mock in the test was not configured with the necessary list. Changing this to `Mock` caused a hard `TypeError`, forcing tests to explicitly mock the `GOODS` dictionary correctly (`Mock(GOODS={})`).

## 2. Regression Analysis
During the conversion, a regression immediately surfaced in `tests/unit/test_firms.py` where a `Firm` creation failed via `RuntimeError: Failed to inject liquidity for Firm 1`. The root cause trace revealed:

```python
    if hasattr(config, "GOODS") and firm.specialization in config.GOODS:
```

Because `config_module` in `FirmFactory` was now initialized as a standard `Mock()` without an explicit `GOODS` attribute, the `hasattr` check actually passed (because `Mock` auto-generates child mocks for any attribute access), returning a child `Mock`. However, the subsequent `in` containment check failed because `Mock` instances (unlike `MagicMock`) do not implement the `__iter__` or `__contains__` magic methods by default, throwing a `TypeError: argument of type 'Mock' is not iterable`.

**The Fix:** We updated the `FirmFactory` instantiation within `tests/utils/factories.py` to correctly initialize the dummy configuration with the required attribute explicitly:

```python
    mock_config = Mock()
    mock_config.GOODS = {}

    factory = FirmFactory(config_module=config_registry if config_registry is not None else mock_config)
```
This forces the configuration to behave like a struct/DTO with explicitly defined bounds, aligning perfectly with the architectural goal of DTO Purity and Mock Fidelity.

Additionally, a pre-existing failing test in `tests/unit/modules/governance/test_system_processor.py::test_set_tax_rate_no_government_warning` was discovered due to mismatched log capture validation in an isolated environment. The tests were updated to enforce proper `caplog` error level checks.

## 3. Test Evidence

```
============================= test session starts ==============================
platform linux -- Python 3.12.12, pytest-9.0.2, pluggy-1.6.0
rootdir: /app
configfile: pytest.ini
plugins: mock-3.15.1, asyncio-1.3.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 742 items

...
tests/unit/test_wo157_dynamic_pricing.py::TestWO157DynamicPricing::test_record_sale_updates_tick PASSED [ 99%]
tests/unit/test_wo157_dynamic_pricing.py::TestWO157DynamicPricing::test_dynamic_pricing_reduction PASSED [ 99%]
tests/unit/test_wo157_dynamic_pricing.py::TestWO157DynamicPricing::test_dynamic_pricing_floor PASSED [ 99%]
tests/unit/test_wo157_dynamic_pricing.py::TestWO157DynamicPricing::test_dynamic_pricing_not_stale PASSED [ 99%]
tests/unit/test_wo157_dynamic_pricing.py::TestWO157DynamicPricing::test_transaction_processor_calls_record_sale PASSED [ 99%]
tests/unit/utils/test_config_factory.py::test_create_config_dto_success PASSED [ 99%]
tests/unit/utils/test_config_factory.py::test_create_config_dto_missing_field PASSED [100%]

======================= 742 passed in 308.68s (0:05:08) ========================
```
