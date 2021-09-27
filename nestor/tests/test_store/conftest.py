from pathlib import Path

import pytest

from nestor import Store
from nestor.store.schema import Config
from tests.test_store import configs

full_config_path = Path(configs.__file__).parent / "full_correct.yml"


@pytest.fixture(scope="session")
def config_full():
    return Config.from_yaml(full_config_path)


@pytest.fixture(scope="session")
def store_full(config_full: Config):
    return Store(config_full)
