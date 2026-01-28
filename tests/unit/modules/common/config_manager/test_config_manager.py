import pytest
from pathlib import Path
from types import ModuleType
from modules.common.config_manager.impl import ConfigManagerImpl

@pytest.fixture
def legacy_config():
    config = ModuleType('legacy_config')
    config.MY_LEGACY_VALUE = 'legacy'
    config.ANOTHER_VALUE = 123
    return config

@pytest.fixture
def config_dir(tmp_path: Path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "test.yaml").write_text("""
    a:
      b:
        c: 1
    d: 2
    """)
    (config_dir / "other.yaml").write_text("""
    x:
      y: "hello"
    """)
    return config_dir

def test_load_yaml(config_dir: Path):
    cm = ConfigManagerImpl(config_dir)
    assert cm.get('test.a.b.c') == 1
    assert cm.get('test.d') == 2
    assert cm.get('other.x.y') == 'hello'

def test_get_with_default(config_dir: Path):
    cm = ConfigManagerImpl(config_dir)
    assert cm.get('nonexistent.key', 'default_value') == 'default_value'
    assert cm.get('test.a.nonexistent', 'another_default') == 'another_default'

def test_hybrid_fallback(config_dir: Path, legacy_config: ModuleType):
    cm = ConfigManagerImpl(config_dir, legacy_config)
    assert cm.get('test.a.b.c') == 1  # From YAML
    assert cm.get('my.legacy.value') == 'legacy' # From legacy config
    assert cm.get('another.value') == 123

def test_set_value_for_test(config_dir: Path):
    cm = ConfigManagerImpl(config_dir)
    assert cm.get('test.a.b.c') == 1
    cm.set_value_for_test('test.a.b.c', 99)
    assert cm.get('test.a.b.c') == 99
    cm.set_value_for_test('new.key.value', 'test_value')
    assert cm.get('new.key.value') == 'test_value'
