from __future__ import annotations

import argparse
import re
import sys
from importlib import resources
from pathlib import Path

# --- templates ---

def _carregar_template(nome: str) -> str:
    return resources.files("rpa_core.templates").joinpath(nome).read_text(encoding="utf-8")

_BOT_PY          = _carregar_template("bot.py.template")
_MAIN_PY_NONE    = _carregar_template("main_none.py.template")
_MAIN_PY_MAESTRO = _carregar_template("main_maestro.py.template")
_SETTINGS_PY     = _carregar_template("settings.py.template")
_SETTINGS_INI    = _carregar_template("settings.ini.template")
_WORKFLOW_PY     = _carregar_template("workflow.py.template")

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

def init(orchestrator: str = "none") -> None:
    root = Path.cwd()

    existentes = [f for f in ["bot.py", "main.py", "settings.ini", "settings.py"] if (root / f).exists()]
    if existentes:
        print(f"Erro: já existem arquivos do projeto aqui ({', '.join(existentes)}).")
        sys.exit(1)

    print(f"\nInicializando projeto em '{root.name}'...\n")

    main_template = _MAIN_PY_MAESTRO if orchestrator == "maestro" else _MAIN_PY_NONE

    if orchestrator == "maestro":
        _criar_arquivo(root / "bot.py", _BOT_PY)

    _criar_arquivo(root / "main.py", main_template)
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

    if bot_py.exists():
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
        print(
            "Erro: bot.py não encontrado. "
            "Este projeto foi criado sem orquestrador. "
            "Use 'rpa-core init --orchestrator maestro' para projetos com BotCity Maestro."
        )
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

    # Atualiza settings.ini preservando formatação e linhas em branco entre seções
    ini_lines = settings_ini.read_text(encoding="utf-8").splitlines(keepends=True)
    result: list[str] = []
    in_section = False
    inserted = False
    pending_blanks: list[str] = []

    for line in ini_lines:
        stripped = line.strip()
        if stripped == f"[{secao}]":
            in_section = True
            result.extend(pending_blanks)
            pending_blanks = []
            result.append(line)
        elif stripped.startswith("[") and in_section:
            # Insere a nova chave antes das linhas em branco que precedem a próxima seção
            result.append(f"{chave} = {valor}\n")
            inserted = True
            in_section = False
            result.extend(pending_blanks)
            pending_blanks = []
            result.append(line)
        elif stripped == "" and in_section:
            pending_blanks.append(line)
        else:
            result.extend(pending_blanks)
            pending_blanks = []
            result.append(line)

    if in_section and not inserted:
        result.append(f"{chave} = {valor}\n")
        result.extend(pending_blanks)
        inserted = True

    if not inserted:
        result.extend(pending_blanks)
        result.append(f"\n[{secao}]\n{chave} = {valor}\n")

    settings_ini.write_text("".join(result), encoding="utf-8")
    print(f"  atualizado  settings.ini — [{secao}] {chave} = {valor}")

    # Atualiza settings.py
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

    init_p = subparsers.add_parser("init", help="Inicializa a estrutura base no diretório atual")
    init_p.add_argument(
        "--orchestrator",
        choices=["none", "maestro"],
        default="none",
        help="Orquestrador a integrar (default: none)",
    )

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
        init(orchestrator=args.orchestrator)
    elif args.comando == "new-workflow":
        new_workflow(args.nome)
    elif args.comando == "set-bot-workflow":
        set_bot_workflow(args.nome)
    elif args.comando == "add-setting":
        add_setting(args.secao, args.chave, args.tipo, args.valor)
    else:
        parser.print_help()
