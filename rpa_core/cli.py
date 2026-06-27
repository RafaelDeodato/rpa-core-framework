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

# --- scaffolding ---

def _criar_arquivo(path: Path, conteudo: str) -> None:
    path.write_text(conteudo, encoding="utf-8")
    print(f"  criado  {path.name}")


def _criar_pasta(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    (path / "__init__.py").write_text("")
    print(f"  criado  {path.name}/")


def init() -> None:
    root = Path.cwd()

    arquivos_existentes = [
        f for f in ["bot.py", "main.py", "settings.ini"]
        if (root / f).exists()
    ]
    if arquivos_existentes:
        print(f"Erro: já existem arquivos do projeto aqui ({', '.join(arquivos_existentes)}).")
        sys.exit(1)

    print(f"\nInicializando projeto em '{root.name}'...\n")

    _criar_arquivo(root / "bot.py", _BOT_PY)
    _criar_arquivo(root / "main.py", _MAIN_PY)
    _criar_arquivo(root / "settings.ini", _SETTINGS_INI)
    _criar_pasta(root / "services")
    _criar_pasta(root / "workflows")

    print("\nPronto. Adicione seus workflows em workflows/ e registre em main.py.")


# --- entry point ---

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="rpa-core",
        description="CLI do rpa-core-framework",
    )
    subparsers = parser.add_subparsers(dest="comando")

    subparsers.add_parser("init", help="Inicializa a estrutura base no diretório atual")

    args = parser.parse_args()

    if args.comando == "init":
        init()
    else:
        parser.print_help()
