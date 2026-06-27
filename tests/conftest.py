import pytest
from pathlib import Path
from unittest.mock import MagicMock
from rpa_core.settings import Settings
from rpa_core.logger import LoggerFactory

_INI_BASE = """
[application]
environment = development

[automation]
timeout_seconds = 30

[logging]
level = INFO
directory = logs
"""


@pytest.fixture
def settings(tmp_path) -> Settings:
    ini = tmp_path / "settings.ini"
    ini.write_text(_INI_BASE)
    return Settings.load(ini)


@pytest.fixture
def logger() -> LoggerFactory:
    return MagicMock(spec=LoggerFactory)
