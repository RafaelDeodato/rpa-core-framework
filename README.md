# rpa-core

Framework Python para projetos de automação RPA. Fornece a infraestrutura comum a qualquer automação — configuração, logging e ciclo de vida de execução — para que cada projeto foque só na lógica da automação em si.

A ferramenta de automação (BotCity, Selenium, Playwright) e o orquestrador (BotCity Maestro) são **opcionais**: cada projeto instala apenas o que precisa.

## Sumário

- [Requisitos](#requisitos)
- [Instalação](#instalação)
  - [Em um projeto real (requirements.txt)](#em-um-projeto-real-requirementstxt)
- [Quickstart](#quickstart)
- [Estrutura de um projeto gerado](#estrutura-de-um-projeto-gerado)
- [Comandos da CLI](#comandos-da-cli)
- [Executando](#executando)
- [Conceitos centrais](#conceitos-centrais)
  - [Settings](#settings)
  - [LoggerFactory](#loggerfactory)
  - [ProcessRunner](#processrunner)
- [Orquestrador (opcional)](#orquestrador-opcional)
- [Services de automação](#services-de-automação)
- [Testes](#testes)
- [Indo além: framework por cliente](#indo-além-framework-por-cliente)

---

## Requisitos

Python 3.10+

## Instalação

```bash
pip install "rpa-core[botcity-web] @ git+https://github.com/RafaelDeodato/rpa-core-framework.git"
```

Troque `botcity-web` pelo extra correspondente à ferramenta que o projeto usa, ou combine mais de um separando por vírgula (`rpa-core[botcity-web,maestro]`):

| Extra | Instala | Uso |
|---|---|---|
| `botcity-web` | `botcity-framework-web` | Automação de browser via BotCity WebBot |
| `botcity-core` | `botcity-framework-core` | Automação desktop via BotCity DesktopBot |
| `selenium` | `selenium` | Automação de browser via Selenium WebDriver |
| `playwright` | `playwright` | Automação de browser via Playwright |
| `maestro` | `botcity-maestro-sdk` | Integração com BotCity Maestro Orchestrator |

Sem nenhum extra, o `rpa-core` instala só a base (configuração, logging, ciclo de vida) — útil quando a automação não usa browser/desktop nem orquestrador.

### Em um projeto real (`requirements.txt`)

O `pip install` direto é prático para testar rapidamente, mas em qualquer projeto que vá pra produção ou rodar em Docker/CI, declare a dependência no `requirements.txt` junto com as demais bibliotecas que a automação precisar — pandas, openpyxl, SQLAlchemy, drivers de banco, etc.:

```
rpa-core[botcity-web] @ git+https://github.com/RafaelDeodato/rpa-core-framework.git
pandas
openpyxl
sqlalchemy
```

```bash
pip install -r requirements.txt
```

Isso garante que qualquer ambiente — sua máquina, um container Docker, um pipeline de CI — instala exatamente o mesmo conjunto de dependências, em vez de depender de comandos rodados manualmente.

Para travar numa versão específica do `rpa-core` (recomendado para produção), use a tag no lugar da branch padrão. A versão mais recente publicada é a `v0.1.0`:

```
rpa-core[botcity-web] @ git+https://github.com/RafaelDeodato/rpa-core-framework.git@v0.1.0
```

---

## Quickstart

```bash
mkdir minha-automacao && cd minha-automacao
python3 -m venv venv && source venv/bin/activate   # opcional, recomendado

echo 'rpa-core[botcity-web] @ git+https://github.com/RafaelDeodato/rpa-core-framework.git' > requirements.txt
pip install -r requirements.txt

rpa-core init
rpa-core new-workflow extrator_nfe
```

Isso gera a estrutura do projeto e o esqueleto do workflow em `workflows/extrator_nfe/extrator_nfe.py`. Implemente a automação no método `execute()`:

```python
from rpa_core import LoggerFactory
from rpa_core.services.botcity_web_service import BotCityWebService
from settings import Settings


class ExtratorNfe:
    def __init__(self, logger: LoggerFactory, settings: Settings) -> None:
        self._logger = logger
        self._settings = settings

    def execute(self) -> None:
        bot_service = BotCityWebService(timeout_seconds=self._settings.timeout_seconds, logger=self._logger)
        bot_service.start()

        bot_service.bot.navigate_to("https://exemplo.com")
        self._logger.info("Site aberto com sucesso")

        bot_service.stop()
```

Rode:

```bash
python main.py extrator_nfe
```

Precisa de uma configuração nova (URL, credencial, flag)? Adicione com:

```bash
rpa-core add-setting application base_url str https://api.exemplo.com
```

Isso atualiza `settings.ini` e o dataclass `Settings` em `settings.py` ao mesmo tempo — o campo já fica disponível em `self._settings.base_url`.

---

## Estrutura de um projeto gerado

```
minha-automacao/
├── bot.py            # só com --orchestrator maestro
├── main.py           # entry point
├── settings.py       # dataclass Settings (editável, atualizado por add-setting)
├── settings.ini      # valores de configuração
├── services/         # services compartilhados entre workflows (ex: login de um sistema)
└── workflows/
    └── extrator_nfe/
        ├── extrator_nfe.py   # classe com execute() — orquestra a automação
        └── tasks/            # passos da automação, um arquivo por etapa
```

`services/` e `tasks/` são convenções de organização, não geradas automaticamente com conteúdo — a CLI cria as pastas vazias e você estrutura o código conforme o workflow cresce. Um padrão comum é uma função/classe por etapa em `tasks/`, e tudo que é compartilhado entre dois ou mais workflows (como um login) em `services/`.

---

## Comandos da CLI

| Comando | Faz |
|---|---|
| `rpa-core init [--orchestrator none\|maestro]` | Cria a estrutura base do projeto no diretório atual. Default: `none` |
| `rpa-core new-workflow <nome>` | Cria um workflow e registra automaticamente em `main.py` (e em `bot.py`, se existir) |
| `rpa-core add-setting <secao> <chave> <tipo> <valor>` | Adiciona um campo a `settings.ini` e `settings.py`. Tipos: `str`, `int`, `float`, `bool`, `path` |
| `rpa-core set-bot-workflow <nome>` | Define qual workflow o `bot.py` executa. Só disponível em projetos com `--orchestrator maestro` |

Nomes de workflow e de chave de configuração devem estar em `snake_case`.

---

## Executando

Sem orquestrador (default), em desenvolvimento ou produção/Docker:

```bash
python main.py extrator_nfe
```

Com BotCity Maestro, o BotCity Runner executa `bot.py`, que por sua vez chama `main.py` internamente — o `WORKFLOW_NAME` definido em `bot.py` decide qual workflow roda. Localmente, `python main.py <workflow>` funciona da mesma forma, com ou sem Maestro.

---

## Conceitos centrais

### `Settings`

Dataclass gerado em `settings.py`, carregado de `settings.ini`.

```python
from settings import Settings

settings = Settings.load()                       # lê settings.ini na raiz do projeto
settings = Settings.load("caminho/settings.ini")  # caminho customizado
```

### `LoggerFactory`

Logger com saída simultânea no console (colorida) e em arquivo (`logs/YYYYMMDD_HHMMSS.txt`).

```python
from rpa_core import LoggerFactory

logger = LoggerFactory()
logger.info("Mensagem", total=150, status="ok")  # kwargs extras aparecem no log
logger.exception("Erro com traceback")
```

### `ProcessRunner`

Centraliza o ciclo de vida da execução de um workflow: loga início, chama `workflow.execute()`, loga sucesso ou erro, propaga a exceção. Usado internamente pelo `main.py` gerado — raramente é necessário instanciá-lo à mão.

```python
from rpa_core import ProcessRunner

ProcessRunner(logger=logger).run(workflow)
```

---

## Orquestrador (opcional)

Por padrão (`--orchestrator none`), o projeto não depende de nenhum orquestrador externo. Para integrar com BotCity Maestro:

```bash
rpa-core init --orchestrator maestro
pip install "rpa-core[maestro] @ git+https://github.com/RafaelDeodato/rpa-core-framework.git"
```

Isso gera `bot.py` (entry point do BotCity Runner) e conecta o `MaestroLogService` ao `ProcessRunner`, enviando logs estruturados ao Maestro a cada etapa. Se o Maestro estiver inacessível em tempo de execução, o envio de log falha silenciosamente — a automação não é interrompida por isso.

Para integrar com um orquestrador diferente, implemente o protocolo `OrchestratorLogger` (métodos `info`, `warning`, `error`) e passe sua própria classe ao `ProcessRunner` no lugar do `MaestroLogService` — o `rpa-core` não exige Maestro especificamente, só esse contrato.

---

## Services de automação

Cada service encapsula o ciclo de vida (`start()` / `stop()`) de uma ferramenta de automação e expõe o objeto nativo dela para uso direto — sem abstrair a API da ferramenta em si.

```python
from rpa_core.services.botcity_web_service import BotCityWebService

service = BotCityWebService(timeout_seconds=30, logger=logger, headless=False)
service.start()
service.bot.navigate_to("https://exemplo.com")  # objeto WebBot nativo do BotCity
service.stop()
```

| Service | Extra | Construtor | Objeto nativo |
|---|---|---|---|
| `BotCityWebService` | `botcity-web` | `timeout_seconds, logger, headless=False` | `.bot` (BotCity `WebBot`) |
| `BotCityCoreService` | `botcity-core` | `logger` | `.bot` (BotCity `DesktopBot`) |
| `SeleniumService` | `selenium` | `timeout_seconds, logger, headless=False` | `.driver` (Selenium `WebDriver`) |
| `PlaywrightService` | `playwright` | `timeout_seconds, logger, headless=False` | `.page` (Playwright `Page`) |

Instanciar um service sem o extra correspondente instalado levanta `ImportError` com a instrução de instalação.

---

## Testes

```bash
pip install -e ".[botcity-web,botcity-core,selenium,playwright,maestro]"
pip install pytest
pytest
```

---

## Indo além: framework por cliente

Quando uma automação cresce para múltiplos workflows de um mesmo cliente — com logins, clients de API internas ou regras de negócio compartilhadas entre eles — vale extrair esse código para um pacote próprio, em vez de adicionar lógica específica de cliente dentro do `rpa-core` (que deve continuar genérico). Esse pacote declara `rpa-core` como dependência, do mesmo jeito mostrado em [Em um projeto real](#em-um-projeto-real-requirementstxt):

```
rpa-core[botcity-web] @ git+https://github.com/RafaelDeodato/rpa-core-framework.git@v0.1.0
```

Cada cliente ganha seus próprios services compartilhados entre workflows, e continua se beneficiando de atualizações do `rpa-core` ao avançar a tag fixada.
