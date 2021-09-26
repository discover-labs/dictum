from pathlib import Path

from nestor.store.schema import Config

config_path = Path(__file__).parent / "config_test.yml"


def test_config_loads_from_yaml():
    conf = Config.from_yaml(str(config_path))
