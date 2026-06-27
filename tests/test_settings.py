from pathlib import Path
import pytest
from rpa_core.settings import Settings


def _write_ini(tmp_path, content: str) -> Path:
    ini = tmp_path / "settings.ini"
    ini.write_text(content)
    return ini


def test_timeout_convertido_para_int(tmp_path):
    ini = _write_ini(tmp_path, """
[application]
environment = development

[automation]
timeout_seconds = 60

[logging]
level = INFO
directory = logs
""")
    assert Settings.load(ini).timeout_seconds == 60


def test_log_level_em_maiusculo(tmp_path):
    ini = _write_ini(tmp_path, """
[application]
environment = development

[automation]
timeout_seconds = 30

[logging]
level = debug
directory = logs
""")
    assert Settings.load(ini).log_level == "DEBUG"


def test_arquivo_inexistente_levanta_erro():
    with pytest.raises(FileNotFoundError):
        Settings.load("nao_existe.ini")


def test_secao_ausente_levanta_erro(tmp_path):
    ini = _write_ini(tmp_path, "[application]\nenvironment = development\n")
    with pytest.raises(ValueError):
        Settings.load(ini)
