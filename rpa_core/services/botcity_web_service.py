from __future__ import annotations

from rpa_core.logger import LoggerFactory

try:
    from botcity.web import WebBot, Browser
    _DISPONIVEL = True
except ImportError:
    _DISPONIVEL = False


class BotCityWebService:
    """Ciclo de vida do WebBot do BotCity Framework (automação web).

    Requer: pip install 'rpa-core[botcity-web]'
    """

    def __init__(self, timeout_seconds: int, logger: LoggerFactory, headless: bool = False) -> None:
        if not _DISPONIVEL:
            raise ImportError(
                "botcity-framework-web não instalado. "
                "Execute: pip install 'rpa-core[botcity-web]'"
            )
        self._timeout_seconds = timeout_seconds
        self._headless = headless
        self._logger = logger
        self._bot = None

    @property
    def bot(self) -> WebBot:
        return self._bot

    def start(self) -> None:
        self._bot = WebBot()
        self._bot.headless = self._headless
        self._bot.browser = Browser.CHROME
        self._bot.wait_timeout = self._timeout_seconds * 1000
        self._logger.info("Browser iniciado", headless=self._headless)

    def stop(self) -> None:
        if self._bot:
            self._bot.stop_browser()
            self._bot = None
            self._logger.info("Browser encerrado")
