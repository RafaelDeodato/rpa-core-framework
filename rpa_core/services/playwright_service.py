from __future__ import annotations

from rpa_core.logger import LoggerFactory

try:
    from playwright.sync_api import sync_playwright
    _DISPONIVEL = True
except ImportError:
    _DISPONIVEL = False


class PlaywrightService:
    """Ciclo de vida do Playwright (automação web).

    Requer: pip install 'rpa-core[playwright]'
    """

    def __init__(self, timeout_seconds: int, logger: LoggerFactory, headless: bool = False) -> None:
        if not _DISPONIVEL:
            raise ImportError(
                "playwright não instalado. "
                "Execute: pip install 'rpa-core[playwright]'"
            )
        self._timeout_seconds = timeout_seconds
        self._headless = headless
        self._logger = logger
        self._playwright = None
        self._browser = None
        self._page = None

    @property
    def page(self):
        return self._page

    def start(self) -> None:
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=self._headless)
        self._page = self._browser.new_page()
        self._page.set_default_timeout(self._timeout_seconds * 1000)
        self._logger.info("Browser iniciado", headless=self._headless)

    def stop(self) -> None:
        if self._browser:
            self._browser.close()
            self._playwright.stop()
            self._browser = None
            self._page = None
            self._playwright = None
            self._logger.info("Browser encerrado")
