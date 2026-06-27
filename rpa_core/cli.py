from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# --- templates ---

_BOT_PY = '''\
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

from botcity.maestro import AutomationTaskFinishStatus, BotMaestroSDK
from main import main

WORKFLOW_NAME = ""


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
from settings import Settings
from rpa_core import LoggerFactory, MaestroLogService, ProcessRunner

# [rpa-core] imports dos workflows
WORKFLOWS = {
    # [rpa-core] registro dos workflows
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

_SETTINGS_PY = '''\
from __future__ import annotations

from configparser import ConfigParser, Error as ConfigParserError
from dataclasses import dataclass
from pathlib import Path

DEFAULT_SETTINGS_PATH = Path(__file__).parent / "settings.ini"


@dataclass(frozen=True)
class Settings:
    environment: str
    timeout_seconds: int
    log_level: str
    log_directory: Path
    # [rpa-core] campos adicionais

    @classmethod
    def load(cls, path: str | Path | None = None) -> "Settings":
        settings_path = Path(path) if path else DEFAULT_SETTINGS_PATH
        if not settings_path.is_file():
            raise FileNotFoundError(f"settings.ini não encontrado em: {settings_path}")
        parser = ConfigParser()
        if not parser.read(settings_path, encoding="utf-8"):
            raise ValueError(f"Não foi possível ler: {settings_path}")
        try:
            return cls(
                environment=parser.get("application", "environment"),
                timeout_seconds=parser.getint("automation", "timeout_seconds"),
                log_level=parser.get("logging", "level").upper(),
                log_directory=Path(parser.get("logging", "directory")),
                # [rpa-core] leitura dos campos adicionais
            )
        except (ConfigParserError, KeyError, ValueError) as exc:
            raise ValueError(f"Erro ao carregar settings.ini: {exc}") from exc
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

_WORKFLOW_PY = '''\
from rpa_core import LoggerFactory
from settings import Settings


class {classe}:
    def __init__(self, logger: LoggerFactory, settings: Settings) -> None:
        self._logger = logger
        self._settings = settings

    def execute(self) -> None:
        pass
'''

# --- tipos suportados para add-setting ---

_TIPO_PY = {
    "str":   "str",
    "int":   "int",
    "float": "float",
    "bool":  "bool",
    "path":  "Path",
}

_PARSER_CALL = {
    "str":   lambda s, k: f'parser.get("{s}", "{k}")',
    "int":   lambda s, k: f'parser.getint("{s}", "{k}")',
    "float": lambda s, k: f'parser.getfloat("{s}", "{k}")',
    "bool":  lambda s, k: f'parser.getboolean("{s}", "{k}")',
    "path":  lambda s, k: f'Path(parser.get("{s}", "{k}"))',
}

# --- helpers ---

def _snake_to_pascal(nome: str) -> str:
    return "".join(part.capitalize() for part in nome.split("_"))


def _validar_nome(nome: str) -> None:
    if not re.match(r'^[a-z][a-z0-9_]*$', nome):
        print("Erro: o nome deve estar em snake_case (ex: extrator_nfe, max_retries).")
        sys.exit(1)


def _criar_arquivo(path: Path, conteudo: str) -> None:
    path.write_text(conteudo, encoding="utf-8")
    print(f"  criado  {path.relative_to(Path.cwd())}")


def _criar_pasta(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    (path / "__init__.py").write_text("")
    print(f"  criado  {path.relative_to(Path.cwd())}/")


# --- comandos ---

def init() -> None:
    root = Path.cwd()

    existentes = [f for f in ["bot.py", "main.py", "settings.ini", "settings.py"] if (root / f).exists()]
    if existentes:
        print(f"Erro: já existem arquivos do projeto aqui ({', '.join(existentes)}).")
        sys.exit(1)

    print(f"\nInicializando projeto em '{root.name}'...\n")

    _criar_arquivo(root / "bot.py", _BOT_PY)
    _criar_arquivo(root / "main.py", _MAIN_PY)
    _criar_arquivo(root / "settings.py", _SETTINGS_PY)
    _criar_arquivo(root / "settings.ini", _SETTINGS_INI)
    _criar_pasta(root / "services")
    _criar_pasta(root / "workflows")

    print("\nPronto. Use 'rpa-core new-workflow <nome>' para criar o primeiro workflow.")


def new_workflow(nome: str) -> None:
    _validar_nome(nome)

    root = Path.cwd()
    main_py = root / "main.py"
    bot_py = root / "bot.py"

    if not main_py.exists():
        print("Erro: main.py não encontrado. Execute 'rpa-core init' primeiro.")
        sys.exit(1)

    workflow_dir = root / "workflows" / nome
    if workflow_dir.exists():
        print(f"Erro: workflow '{nome}' já existe.")
        sys.exit(1)

    classe = _snake_to_pascal(nome)

    print(f"\nCriando workflow '{nome}'...\n")

    workflow_dir.mkdir(parents=True)
    (workflow_dir / "__init__.py").write_text("")
    _criar_pasta(workflow_dir / "tasks")
    _criar_arquivo(workflow_dir / f"{nome}.py", _WORKFLOW_PY.format(classe=classe))

    main_content = main_py.read_text(encoding="utf-8")
    import_line = f"from workflows.{nome}.{nome} import {classe}"
    main_content = main_content.replace(
        "# [rpa-core] imports dos workflows\n",
        f"# [rpa-core] imports dos workflows\n{import_line}\n",
    )
    entry_line = f'    "{nome}": {classe},\n'
    main_content = main_content.replace(
        "    # [rpa-core] registro dos workflows\n",
        f"    # [rpa-core] registro dos workflows\n{entry_line}",
    )
    main_py.write_text(main_content, encoding="utf-8")
    print(f"  atualizado  main.py")

    bot_content = bot_py.read_text(encoding="utf-8")
    if 'WORKFLOW_NAME = ""' in bot_content:
        bot_content = bot_content.replace('WORKFLOW_NAME = ""', f'WORKFLOW_NAME = "{nome}"')
        bot_py.write_text(bot_content, encoding="utf-8")
        print(f"  atualizado  bot.py")

    print(f"\nWorkflow '{nome}' criado. Implemente execute() em workflows/{nome}/{nome}.py")


def set_bot_workflow(nome: str) -> None:
    root = Path.cwd()
    bot_py = root / "bot.py"

    if not bot_py.exists():
        print("Erro: bot.py não encontrado. Execute 'rpa-core init' primeiro.")
        sys.exit(1)

    workflow_dir = root / "workflows" / nome
    if not workflow_dir.exists():
        print(f"Erro: workflow '{nome}' não existe. Use 'rpa-core new-workflow {nome}' para criá-lo.")
        sys.exit(1)

    bot_content = bot_py.read_text(encoding="utf-8")
    bot_content = re.sub(r'WORKFLOW_NAME\s*=\s*"[^"]*"', f'WORKFLOW_NAME = "{nome}"', bot_content)
    bot_py.write_text(bot_content, encoding="utf-8")

    print(f"bot.py atualizado: WORKFLOW_NAME = \"{nome}\"")


def add_setting(secao: str, chave: str, tipo: str, valor: str) -> None:
    _validar_nome(chave)

    if tipo not in _TIPO_PY:
        print(f"Erro: tipo '{tipo}' inválido. Use: {', '.join(_TIPO_PY)}")
        sys.exit(1)

    root = Path.cwd()
    settings_ini = root / "settings.ini"
    settings_py = root / "settings.py"

    if not settings_ini.exists() or not settings_py.exists():
        print("Erro: settings.ini/settings.py não encontrados. Execute 'rpa-core init' primeiro.")
        sys.exit(1)

    py_content = settings_py.read_text(encoding="utf-8")
    if re.search(rf'^\s+{chave}:', py_content, re.MULTILINE):
        print(f"Erro: campo '{chave}' já existe em settings.py.")
        sys.exit(1)

    # Atualiza settings.ini — insere na seção correta preservando o resto do arquivo
    ini_lines = settings_ini.read_text(encoding="utf-8").splitlines(keepends=True)
    result: list[str] = []
    in_section = False
    inserted = False

    for line in ini_lines:
        stripped = line.strip()
        if stripped == f"[{secao}]":
            in_section = True
        elif stripped.startswith("[") and in_section:
            result.append(f"{chave} = {valor}\n")
            inserted = True
            in_section = False
        result.append(line)

    if in_section and not inserted:
        result.append(f"{chave} = {valor}\n")
        inserted = True

    if not inserted:
        result.append(f"\n[{secao}]\n{chave} = {valor}\n")

    settings_ini.write_text("".join(result), encoding="utf-8")
    print(f"  atualizado  settings.ini — [{secao}] {chave} = {valor}")

    # Atualiza settings.py — adiciona campo no dataclass e leitura no load()
    tipo_py = _TIPO_PY[tipo]
    campo = f"    {chave}: {tipo_py}\n"
    py_content = py_content.replace(
        "    # [rpa-core] campos adicionais\n",
        f"{campo}    # [rpa-core] campos adicionais\n",
    )

    parser_call = _PARSER_CALL[tipo](secao, chave)
    leitura = f"                {chave}={parser_call},\n"
    py_content = py_content.replace(
        "                # [rpa-core] leitura dos campos adicionais\n",
        f"{leitura}                # [rpa-core] leitura dos campos adicionais\n",
    )

    settings_py.write_text(py_content, encoding="utf-8")
    print(f"  atualizado  settings.py — {chave}: {tipo_py}")


# --- entry point ---

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="rpa-core",
        description="CLI do rpa-core-framework",
    )
    subparsers = parser.add_subparsers(dest="comando")

    subparsers.add_parser("init", help="Inicializa a estrutura base no diretório atual")

    nw = subparsers.add_parser("new-workflow", help="Cria um novo workflow e registra no main.py")
    nw.add_argument("nome", help="Nome do workflow em snake_case (ex: extrator_nfe)")

    sw = subparsers.add_parser("set-bot-workflow", help="Define qual workflow o bot.py executa")
    sw.add_argument("nome", help="Nome do workflow")

    as_ = subparsers.add_parser("add-setting", help="Adiciona um campo ao settings.ini e settings.py")
    as_.add_argument("secao", help="Seção do settings.ini (ex: application, automation)")
    as_.add_argument("chave", help="Nome da chave em snake_case (ex: max_retries)")
    as_.add_argument("tipo", choices=list(_TIPO_PY), help="Tipo Python do campo: str, int, float, bool, path")
    as_.add_argument("valor", help="Valor padrão no settings.ini")

    args = parser.parse_args()

    if args.comando == "init":
        init()
    elif args.comando == "new-workflow":
        new_workflow(args.nome)
    elif args.comando == "set-bot-workflow":
        set_bot_workflow(args.nome)
    elif args.comando == "add-setting":
        add_setting(args.secao, args.chave, args.tipo, args.valor)
    else:
        parser.print_help()
