from __future__ import annotations

import argparse
import sys
from pathlib import Path

# --- templates ---

_BOT_PY = '''\
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

from botcity.maestro import AutomationTaskFinishStatus, BotMaestroSDK
from main import main

WORKFLOW_NAME = "meu_workflow"


def bot_main() -> None:
    maestro = BotMaestroSDK.from_sys_args()

    try:
        execution = maestro.get_execution()
        print(f"[INFO] Execução via Orquestrador | Task ID: {execution.task_id}")
    except Exception:
        execution = None
        print("[INFO] Execução local detectada")

    try:
        main(workflow_name=WORKFLOW_NAME, maestro=maestro)

        if execution:
            maestro.finish_task(
                task_id=execution.task_id,
                status=AutomationTaskFinishStatus.SUCCESS,
                message="Task finalizada com sucesso",
            )

    except Exception as exc:
        if execution:
            maestro.finish_task(
                task_id=execution.task_id,
                status=AutomationTaskFinishStatus.FAILED,
                message=str(exc),
            )
        raise


if __name__ == "__main__":
    bot_main()
'''

_MAIN_PY = '''\
import argparse
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

from botcity.maestro import BotMaestroSDK
from rpa_core import Settings, LoggerFactory, MaestroLogService, ProcessRunner

# Importe e registre os workflows do projeto aqui
WORKFLOWS = {
    # "meu_workflow": MeuWorkflow,
}


def main(workflow_name: str | None = None, maestro: BotMaestroSDK | None = None) -> None:
    if workflow_name is None:
        parser = argparse.ArgumentParser(description="Executor de workflows RPA")
        parser.add_argument("workflow", choices=list(WORKFLOWS.keys()), help="Nome do workflow")
        workflow_name = parser.parse_args().workflow

    settings = Settings.load()
    logger = LoggerFactory(log_directory=settings.log_directory)

    if maestro is None:
        BotMaestroSDK.RAISE_NOT_CONNECTED = False
        maestro = BotMaestroSDK.from_sys_args()

    maestro_logger = MaestroLogService(maestro=maestro, process_name=workflow_name)

    workflow = WORKFLOWS[workflow_name](
        logger=logger,
        settings=settings,
    )

    ProcessRunner(logger=logger, maestro_logger=maestro_logger).run(workflow)


if __name__ == "__main__":
    main()
'''

_SETTINGS_INI = '''\
[application]
environment = development

[automation]
timeout_seconds = 30

[logging]
level = INFO
directory = logs
'''

_REQUIREMENTS_TXT = '''\
# framework base
rpa-core @ git+https://github.com/RafaelDeodato/rpa-core-framework.git@main

# ferramenta de automação (descomente a necessária)
# rpa-core[botcity-web] @ git+https://...
# rpa-core[botcity-core] @ git+https://...
# rpa-core[selenium] @ git+https://...
# rpa-core[playwright] @ git+https://...

# testes
pytest==9.1.1
'''

_GITIGNORE = '''\
__pycache__/
*.py[cod]
*.egg-info/
.venv/
venv/
logs/
.pytest_cache/
'''

_CONFTEST_PY = '''\
import pytest
from pathlib import Path
from unittest.mock import MagicMock
from rpa_core import Settings, LoggerFactory

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
'''

# --- scaffolding ---

def _criar_arquivo(path: Path, conteudo: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(conteudo, encoding="utf-8")
    print(f"  criado  {path}")


def _criar_pasta(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    init = path / "__init__.py"
    if not init.exists():
        init.write_text("")
    print(f"  criado  {path}/")


def init(nome: str) -> None:
    root = Path(nome)

    if root.exists():
        print(f"Erro: o diretório '{nome}' já existe.")
        sys.exit(1)

    print(f"\nCriando projeto '{nome}'...\n")

    _criar_arquivo(root / "bot.py", _BOT_PY)
    _criar_arquivo(root / "main.py", _MAIN_PY)
    _criar_arquivo(root / "settings.ini", _SETTINGS_INI)
    _criar_arquivo(root / "requirements.txt", _REQUIREMENTS_TXT)
    _criar_arquivo(root / ".gitignore", _GITIGNORE)

    _criar_pasta(root / "services")
    _criar_pasta(root / "workflows")
    _criar_pasta(root / "tests")
    _criar_arquivo(root / "tests" / "conftest.py", _CONFTEST_PY)

    print(f"""
Projeto criado com sucesso!

Próximos passos:
  cd {nome}
  pip install -r requirements.txt
  python main.py <workflow>
""")


# --- entry point ---

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="rpa-core",
        description="CLI do rpa-core-framework",
    )
    subparsers = parser.add_subparsers(dest="comando")

    init_parser = subparsers.add_parser("init", help="Cria a estrutura base de um novo projeto")
    init_parser.add_argument("nome", help="Nome do projeto / pasta a criar")

    args = parser.parse_args()

    if args.comando == "init":
        init(args.nome)
    else:
        parser.print_help()
