import os
import pytest
from pathlib import Path


@pytest.fixture
def in_tmp_dir(tmp_path):
    old = Path.cwd()
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(old)


# --- init --orchestrator none (default) ---

def test_init_none_cria_arquivos_base(in_tmp_dir):
    from rpa_core.cli import init
    init(orchestrator="none")
    assert (in_tmp_dir / "main.py").exists()
    assert (in_tmp_dir / "settings.py").exists()
    assert (in_tmp_dir / "settings.ini").exists()
    assert (in_tmp_dir / "services").is_dir()
    assert (in_tmp_dir / "workflows").is_dir()


def test_init_none_nao_gera_bot_py(in_tmp_dir):
    from rpa_core.cli import init
    init(orchestrator="none")
    assert not (in_tmp_dir / "bot.py").exists()


def test_init_none_main_sem_maestro(in_tmp_dir):
    from rpa_core.cli import init
    init(orchestrator="none")
    content = (in_tmp_dir / "main.py").read_text()
    assert "BotMaestroSDK" not in content
    assert "MaestroLogService" not in content


# --- init --orchestrator maestro ---

def test_init_maestro_gera_bot_py(in_tmp_dir):
    from rpa_core.cli import init
    init(orchestrator="maestro")
    assert (in_tmp_dir / "bot.py").exists()


def test_init_maestro_main_com_maestro(in_tmp_dir):
    from rpa_core.cli import init
    init(orchestrator="maestro")
    content = (in_tmp_dir / "main.py").read_text()
    assert "BotMaestroSDK" in content
    assert "MaestroLogService" in content


# --- add-setting: formatação do settings.ini ---

def test_add_setting_preserva_linha_em_branco_entre_secoes(in_tmp_dir):
    from rpa_core.cli import init, add_setting
    init(orchestrator="none")
    add_setting("application", "base_url", "str", "https://api.exemplo.com")
    content = (in_tmp_dir / "settings.ini").read_text()
    assert "base_url = https://api.exemplo.com\n\n[automation]" in content


def test_add_setting_atualiza_settings_py(in_tmp_dir):
    from rpa_core.cli import init, add_setting
    init(orchestrator="none")
    add_setting("automation", "max_retries", "int", "3")
    py_content = (in_tmp_dir / "settings.py").read_text()
    assert "max_retries: int" in py_content
    assert 'parser.getint("automation", "max_retries")' in py_content


def test_add_setting_nova_secao(in_tmp_dir):
    from rpa_core.cli import init, add_setting
    init(orchestrator="none")
    add_setting("credentials", "usuario", "str", "admin")
    ini_content = (in_tmp_dir / "settings.ini").read_text()
    assert "[credentials]" in ini_content
    assert "usuario = admin" in ini_content
