# rpa-core-framework

Framework interno de RPA em Python — configuração, logging, integração com BotCity Maestro e services para BotCity Web/Core, Selenium e Playwright.

---

## O que é

`rpa-core` é um framework Python para projetos de automação RPA. Ele fornece a infraestrutura comum que toda automação precisa — configuração, logging, integração com orquestrador e ciclo de vida de execução — para que cada projeto foque apenas na lógica da automação em si.

Cada projeto de automação instala o `rpa-core` como dependência e escolhe quais ferramentas de automação precisa via extras.

---

## Instalação

```bash
# Apenas a base (configuração, logging, Maestro, ProcessRunner)
pip install git+https://github.com/RafaelDeodato/rpa-core-framework.git@v0.1.0

# Com BotCity Web (automação de browser)
pip install "rpa-core[botcity-web] @ git+https://github.com/RafaelDeodato/rpa-core-framework.git@v0.1.0"

# Com Selenium
pip install "rpa-core[selenium] @ git+https://github.com/RafaelDeodato/rpa-core-framework.git@v0.1.0"

# Com Playwright
pip install "rpa-core[playwright] @ git+https://github.com/RafaelDeodato/rpa-core-framework.git@v0.1.0"

# Com BotCity Core (automação desktop)
pip install "rpa-core[botcity-core] @ git+https://github.com/RafaelDeodato/rpa-core-framework.git@v0.1.0"

# Combinando mais de uma ferramenta
pip install "rpa-core[botcity-web,pyautogui] @ git+https://github.com/RafaelDeodato/rpa-core-framework.git@v0.1.0"
```

No `requirements.txt` do projeto:

```
rpa-core[botcity-web] @ git+https://github.com/RafaelDeodato/rpa-core-framework.git@v0.1.0
```

---

## CLI — Inicializar um projeto

Crie a pasta do projeto, instale o `rpa-core` e rode:

```bash
mkdir minha-automacao
cd minha-automacao
pip install "rpa-core @ git+https://github.com/RafaelDeodato/rpa-core-framework.git"
rpa-core init
```

O comando cria no diretório atual:

```
minha-automacao/
├── bot.py        # Entry point do BotCity Runner (Maestro)
├── main.py       # Entry point local e Docker
├── settings.ini  # Configurações base
├── services/
│   └── __init__.py
└── workflows/
    └── __init__.py
```

---

## Componentes

### `Settings`

Carrega configurações de um arquivo `settings.ini`. Nenhum outro módulo lê configurações diretamente.

```python
from rpa_core import Settings

settings = Settings.load()           # lê settings.ini na raiz do projeto
settings = Settings.load("caminho/settings.ini")  # caminho customizado
```

**`settings.ini`:**

```ini
[application]
environment = development

[automation]
timeout_seconds = 30

[logging]
level = INFO
directory = logs
```

---

### `LoggerFactory`

Logger com saída simultânea no console (colorida) e em arquivo.

```python
from rpa_core import LoggerFactory

logger = LoggerFactory()
logger.info("Mensagem")
logger.info("Com dados extras", total=150, status="ok")
logger.warning("Aviso")
logger.error("Erro")
logger.exception("Erro com traceback")
```

**Saída:**
```
[2024-01-15 10:30:00] [INFO] Mensagem
[2024-01-15 10:30:00] [INFO] Com dados extras | {'total': 150, 'status': 'ok'}
```

Logs em arquivo são gravados em `logs/YYYYMMDD_HHMMSS.txt`.

---

### `MaestroLogService`

Envia logs estruturados ao BotCity Maestro Orchestrator. Falha silenciosamente se o Maestro não estiver disponível.

```python
from rpa_core import MaestroLogService
from botcity.maestro import BotMaestroSDK

maestro = BotMaestroSDK.from_sys_args()
maestro_logger = MaestroLogService(maestro=maestro, process_name="meu_processo")

maestro_logger.info("Etapa concluída", step="EXTRACAO")
maestro_logger.error("Falha na etapa", step="PROCESSAMENTO")
```

---

### `ProcessRunner`

Orquestra o ciclo de vida da execução: loga início, chama `workflow.execute()`, loga sucesso ou erro (local e no Maestro), e propaga exceções.

```python
from rpa_core import ProcessRunner

runner = ProcessRunner(logger=logger, maestro_logger=maestro_logger)
runner.run(workflow)
```

---

### Services

Services gerenciam o ciclo de vida da ferramenta de automação escolhida. Cada um requer o extra correspondente instalado.

#### BotCity Web

```python
from rpa_core.services.botcity_web_service import BotCityWebService

bot_service = BotCityWebService(
    timeout_seconds=settings.timeout_seconds,
    logger=logger,
    headless=False,
)
bot_service.start()
bot_service.bot.navigate_to("https://exemplo.com")
bot_service.stop()
```

#### BotCity Core (desktop)

```python
from rpa_core.services.botcity_core_service import BotCityCoreService

bot_service = BotCityCoreService(logger=logger)
bot_service.start()
bot_service.bot.find("elemento", matching=0.97)
bot_service.stop()
```

#### Selenium

```python
from rpa_core.services.selenium_service import SeleniumService

selenium = SeleniumService(
    timeout_seconds=settings.timeout_seconds,
    logger=logger,
    headless=False,
)
selenium.start()
selenium.driver.get("https://exemplo.com")
selenium.stop()
```

#### Playwright

```python
from rpa_core.services.playwright_service import PlaywrightService

playwright = PlaywrightService(
    timeout_seconds=settings.timeout_seconds,
    logger=logger,
    headless=False,
)
playwright.start()
playwright.page.goto("https://exemplo.com")
playwright.stop()
```

---

## Estrutura de um Projeto de Automação

```
minha-automacao/
├── bot.py                      # Entry point do BotCity Runner (Maestro)
├── main.py                     # Entry point local e Docker
├── settings.ini                # Configurações do projeto
├── requirements.txt            # rpa-core + extras necessários
├── services/                   # Serviços reutilizáveis entre workflows
│   └── portal_xyz_login.py     # Ex: login compartilhado entre workflows
├── workflows/
│   └── meu_workflow/
│       ├── meu_workflow.py     # Orquestrador: sequencia as tasks
│       └── tasks/
│           ├── task_01_abrir_site.py
│           ├── task_02_extrair_dados.py
│           └── task_03_finalizar.py
└── tests/
    ├── conftest.py
    └── test_meu_workflow.py
```

### `bot.py` — Entry point do BotCity Runner

```python
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

from botcity.maestro import AutomationTaskFinishStatus, BotMaestroSDK
from main import main

WORKFLOW_NAME = "meu_workflow"

def bot_main() -> None:
    maestro = BotMaestroSDK.from_sys_args()
    try:
        execution = maestro.get_execution()
    except Exception:
        execution = None

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
```

### `main.py` — Entry point local e Docker

```python
import argparse
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

from botcity.maestro import BotMaestroSDK
from rpa_core import Settings, LoggerFactory, MaestroLogService, ProcessRunner
from rpa_core.services.botcity_web_service import BotCityWebService
from workflows.meu_workflow.meu_workflow import MeuWorkflow

WORKFLOWS = {
    "meu_workflow": MeuWorkflow,
}

def main(workflow_name: str | None = None, maestro: BotMaestroSDK | None = None) -> None:
    if workflow_name is None:
        parser = argparse.ArgumentParser()
        parser.add_argument("workflow", choices=list(WORKFLOWS.keys()))
        workflow_name = parser.parse_args().workflow

    settings = Settings.load()
    logger = LoggerFactory(log_directory=settings.log_directory)

    if maestro is None:
        BotMaestroSDK.RAISE_NOT_CONNECTED = False
        maestro = BotMaestroSDK.from_sys_args()

    maestro_logger = MaestroLogService(maestro=maestro, process_name=workflow_name)
    bot_service = BotCityWebService(timeout_seconds=settings.timeout_seconds, logger=logger)

    workflow = WORKFLOWS[workflow_name](
        logger=logger,
        settings=settings,
        bot_service=bot_service,
    )

    ProcessRunner(logger=logger, maestro_logger=maestro_logger).run(workflow)

if __name__ == "__main__":
    main()
```

### Workflow — Orquestrador

```python
# workflows/meu_workflow/meu_workflow.py
from rpa_core import Settings, LoggerFactory
from rpa_core.services.botcity_web_service import BotCityWebService
from workflows.meu_workflow.tasks import task_01_abrir_site, task_02_extrair_dados, task_03_finalizar


class MeuWorkflow:
    def __init__(self, logger: LoggerFactory, settings: Settings, bot_service: BotCityWebService):
        self._logger = logger
        self._settings = settings
        self._bot_service = bot_service

    def execute(self) -> None:
        self._bot_service.start()

        task_01_abrir_site.executar(self._logger, self._bot_service)

        dados = task_02_extrair_dados.executar(self._logger, self._bot_service)
        if not dados:
            return

        task_03_finalizar.executar(self._logger, self._bot_service, dados)
```

### Tasks — Funções atômicas

```python
# workflows/meu_workflow/tasks/task_01_abrir_site.py
from rpa_core import LoggerFactory
from rpa_core.services.botcity_web_service import BotCityWebService

URL = "https://exemplo.com"

def executar(logger: LoggerFactory, bot_service: BotCityWebService) -> None:
    logger.info("Abrindo site", url=URL)
    bot_service.bot.navigate_to(URL)
```

```python
# workflows/meu_workflow/tasks/task_02_extrair_dados.py
from rpa_core import LoggerFactory
from rpa_core.services.botcity_web_service import BotCityWebService

def executar(logger: LoggerFactory, bot_service: BotCityWebService) -> list[dict]:
    try:
        # lógica de extração
        return dados
    except Exception as e:
        logger.exception(f"Erro ao extrair dados: {e}")
        return []  # retorno vazio sinaliza falha ao workflow
```

### Services compartilhados

Quando dois ou mais workflows acessam a mesma plataforma, o script de login vai em `services/`:

```python
# services/portal_xyz_login.py
from rpa_core import LoggerFactory
from rpa_core.services.botcity_web_service import BotCityWebService

def fazer_login(logger: LoggerFactory, bot_service: BotCityWebService, usuario: str, senha: str) -> bool:
    try:
        bot_service.bot.navigate_to("https://portal-xyz.com/login")
        # preenche campos...
        logger.info("Login realizado com sucesso")
        return True
    except Exception as e:
        logger.exception(f"Falha no login: {e}")
        return False
```

---

## Variáveis do `settings.ini`

| Chave | Seção | Descrição | Padrão |
|---|---|---|---|
| `environment` | `[application]` | `development` ou `production` | `development` |
| `timeout_seconds` | `[automation]` | Timeout das ações de automação em segundos | `30` |
| `level` | `[logging]` | Nível de log (`DEBUG`, `INFO`, `WARNING`, `ERROR`) | `INFO` |
| `directory` | `[logging]` | Pasta de saída dos logs | `logs` |

---

## Extras disponíveis

| Extra | Instala | Uso |
|---|---|---|
| `botcity-web` | `botcity-framework-web` | Automação de browser via BotCity WebBot |
| `botcity-core` | `botcity-framework-core` | Automação desktop via BotCity DesktopBot |
| `selenium` | `selenium` | Automação de browser via Selenium WebDriver |
| `playwright` | `playwright` | Automação de browser via Playwright |
