from __future__ import annotations

from rpa_core.logger import LoggerFactory

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    _DISPONIVEL = True
except ImportError:
    _DISPONIVEL = False


class SeleniumService:
    """Ciclo de vida do WebDriver Selenium (automação web).

    Requer: pip install 'rpa-core[selenium]'
    """

    def __init__(self, timeout_seconds: int, logger: LoggerFactory, headless: bool = False) -> None:
        if not _DISPONIVEL:
            raise ImportError(
                "selenium não instalado. "
                "Execute: pip install 'rpa-core[selenium]'"
            )
        self._timeout_seconds = timeout_seconds
        self._headless = headless
        self._logger = logger
        self._driver = None

    @property
    def driver(self):
        return self._driver

    def start(self) -> None:
        options = Options()
        if self._headless:
            options.add_argument("--headless")
        self._driver = webdriver.Chrome(options=options)
        self._driver.implicitly_wait(self._timeout_seconds)
        self._logger.info("Browser iniciado", headless=self._headless)

    def stop(self) -> None:
        if self._driver:
            self._driver.quit()
            self._driver = None
            self._logger.info("Browser encerrado")
