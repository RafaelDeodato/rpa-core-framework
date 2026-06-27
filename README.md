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
pip install "rpa-core @ git+https://github.com/RafaelDeodato/rpa-core-framework.git"

# Com BotCity Web (automação de browser)
pip install "rpa-core[botcity-web] @ git+https://github.com/RafaelDeodato/rpa-core-framework.git"

# Com Selenium
pip install "rpa-core[selenium] @ git+https://github.com/RafaelDeodato/rpa-core-framework.git"

# Com Playwright
pip install "rpa-core[playwright] @ git+https://github.com/RafaelDeodato/rpa-core-framework.git"

# Com BotCity Core (automação desktop)
pip install "rpa-core[botcity-core] @ git+https://github.com/RafaelDeodato/rpa-core-framework.git"
```

No `requirements.txt` do projeto:

```
rpa-core[botcity-web] @ git+https://github.com/RafaelDeodato/rpa-core-framework.git
```

---

## CLI — Criando um projeto

### 1. Inicializar estrutura base

Crie a pasta do projeto, instale o `rpa-core` e rode:

```bash
mkdir minha-automacao
cd minha-automacao
pip install "rpa-core @ git+https://github.com/RafaelDeodato/rpa-core-framework.git"
rpa-core init
```

Cria no diretório atual:

```
minha-automacao/
├── bot.py        # Entry point do BotCity Maestro
├── main.py       # Entry point local e Docker
├── settings.py   # Dataclass Settings do projeto (editável)
├── settings.ini  # Configurações base
├── services/
│   └── __init__.py
└── workflows/
    └── __init__.py
```

### 2. Criar um workflow

```bash
rpa-core new-workflow extrator_nfe
```

Cria a estrutura do workflow, registra automaticamente no `main.py` e define o `WORKFLOW_NAME` no `bot.py` (apenas no primeiro workflow criado):

```
workflows/
└── extrator_nfe/
    ├── __init__.py
    ├── extrator_nfe.py   # classe ExtratorNfe com execute()
    └── tasks/
        └── __init__.py
```

Para adicionar mais workflows, basta rodar o comando novamente — os registros acumulam no `main.py` e o `bot.py` não é alterado.

### 3. Adicionar uma configuração

```bash
rpa-core add-setting <secao> <chave> <tipo> <valor_padrao>
```

Adiciona o campo em `settings.ini` **e** no dataclass `Settings` em `settings.py`, mantendo os dois em sincronia:

```bash
rpa-core add-setting automation max_retries int 3
rpa-core add-setting application base_url str https://api.exemplo.com
rpa-core add-setting automation headless bool false
```

Tipos disponíveis: `str`, `int`, `float`, `bool`, `path`

### 4. Trocar o workflow do bot

```bash
rpa-core set-bot-workflow orquestrador
```

Atualiza o `WORKFLOW_NAME` no `bot.py`. Útil quando o projeto cresce e um workflow passa a orquestrar os demais.

---

## Executando

### Via Maestro (produção)

O BotCity Runner executa o `bot.py` diretamente. O `WORKFLOW_NAME` define qual workflow será chamado:

```python
# bot.py
WORKFLOW_NAME = "extrator_nfe"
```

### Localmente (desenvolvimento)

O `bot.py` não é usado localmente. Use o `main.py` passando o nome do workflow como argumento:

```bash
python main.py extrator_nfe
python main.py validador
python main.py orquestrador
```

O argumento precisa estar registrado no dict `WORKFLOWS` do `main.py`.

---

## Estrutura de um Projeto

```
minha-automacao/
├── bot.py
├── main.py
├── settings.py
├── settings.ini
├── requirements.txt
├── services/
│   └── portal_xyz_login.py   # login compartilhado entre workflows
├── workflows/
│   ├── extrator_nfe/
│   │   ├── extrator_nfe.py   # orquestra as tasks
│   │   └── tasks/
│   │       ├── task_01_abrir_site.py
│   │       ├── task_02_extrair_dados.py
│   │       └── task_03_salvar.py
│   └── orquestrador/
│       └── orquestrador.py   # chama outros workflows se necessário
└── tests/
```

### Workflow

```python
# workflows/extrator_nfe/extrator_nfe.py
from rpa_core import Settings, LoggerFactory
from rpa_core.services.botcity_web_service import BotCityWebService
from workflows.extrator_nfe.tasks import task_01_abrir_site, task_02_extrair_dados, task_03_salvar


class ExtratorNfe:
    def __init__(self, logger: LoggerFactory, settings: Settings) -> None:
        self._logger = logger
        self._settings = settings

    def execute(self) -> None:
        bot_service = BotCityWebService(timeout_seconds=self._settings.timeout_seconds, logger=self._logger)
        bot_service.start()

        task_01_abrir_site.executar(self._logger, bot_service)

        dados = task_02_extrair_dados.executar(self._logger, bot_service)
        if not dados:
            return

        task_03_salvar.executar(self._logger, dados)
```

### Tasks

```python
# workflows/extrator_nfe/tasks/task_01_abrir_site.py
from rpa_core import LoggerFactory
from rpa_core.services.botcity_web_service import BotCityWebService

URL = "https://exemplo.com"

def executar(logger: LoggerFactory, bot_service: BotCityWebService) -> None:
    logger.info("Abrindo site", url=URL)
    bot_service.bot.navigate_to(URL)
```

```python
# workflows/extrator_nfe/tasks/task_02_extrair_dados.py
from rpa_core import LoggerFactory
from rpa_core.services.botcity_web_service import BotCityWebService

def executar(logger: LoggerFactory, bot_service: BotCityWebService) -> list[dict]:
    try:
        # lógica de extração
        return dados
    except Exception as e:
        logger.exception(f"Erro ao extrair dados: {e}")
        return []
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
        logger.info("Login realizado com sucesso")
        return True
    except Exception as e:
        logger.exception(f"Falha no login: {e}")
        return False
```

---

## Componentes

### `Settings`

Carrega configurações de um arquivo `settings.ini`. Nenhum outro módulo lê configurações diretamente.

```python
from rpa_core import Settings

settings = Settings.load()                        # lê settings.ini na raiz do projeto
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

Logger com saída simultânea no console e em arquivo.

```python
from rpa_core import LoggerFactory

logger = LoggerFactory()
logger.info("Mensagem")
logger.info("Com dados extras", total=150, status="ok")
logger.warning("Aviso")
logger.error("Erro")
logger.exception("Erro com traceback")
```

Logs em arquivo são gravados em `logs/YYYYMMDD_HHMMSS.txt`.

---

### `MaestroLogService`

Envia logs estruturados ao BotCity Maestro. Falha silenciosamente se o Maestro não estiver disponível.

```python
from rpa_core import MaestroLogService
from botcity.maestro import BotMaestroSDK

maestro = BotMaestroSDK.from_sys_args()
maestro_logger = MaestroLogService(maestro=maestro, process_name="extrator_nfe")

maestro_logger.info("Etapa concluída", step="EXTRACAO")
maestro_logger.error("Falha na etapa", step="PROCESSAMENTO")
```

---

### `ProcessRunner`

Orquestra o ciclo de vida da execução: loga início, chama `workflow.execute()`, loga sucesso ou erro e propaga exceções.

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

service = BotCityWebService(timeout_seconds=30, logger=logger, headless=False)
service.start()
service.bot.navigate_to("https://exemplo.com")
service.stop()
```

#### BotCity Core (desktop)

```python
from rpa_core.services.botcity_core_service import BotCityCoreService

service = BotCityCoreService(logger=logger)
service.start()
service.bot.find("elemento", matching=0.97)
service.stop()
```

#### Selenium

```python
from rpa_core.services.selenium_service import SeleniumService

service = SeleniumService(timeout_seconds=30, logger=logger, headless=False)
service.start()
service.driver.get("https://exemplo.com")
service.stop()
```

#### Playwright

```python
from rpa_core.services.playwright_service import PlaywrightService

service = PlaywrightService(timeout_seconds=30, logger=logger, headless=False)
service.start()
service.page.goto("https://exemplo.com")
service.stop()
```

---

## Variáveis do `settings.ini`

| Chave | Seção | Descrição |
|---|---|---|
| `environment` | `[application]` | `development` ou `production` |
| `timeout_seconds` | `[automation]` | Timeout das ações de automação em segundos |
| `level` | `[logging]` | Nível de log (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `directory` | `[logging]` | Pasta de saída dos logs |

---

## Extras disponíveis

| Extra | Instala | Uso |
|---|---|---|
| `botcity-web` | `botcity-framework-web` | Automação de browser via BotCity WebBot |
| `botcity-core` | `botcity-framework-core` | Automação desktop via BotCity DesktopBot |
| `selenium` | `selenium` | Automação de browser via Selenium WebDriver |
| `playwright` | `playwright` | Automação de browser via Playwright |
