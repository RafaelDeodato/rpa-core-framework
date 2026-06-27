from __future__ import annotations

from rpa_core.logger import LoggerFactory

try:
    from botcity.core import DesktopBot
    _DISPONIVEL = True
except ImportError:
    _DISPONIVEL = False


class BotCityCoreService:
    """Ciclo de vida do DesktopBot do BotCity Framework (automação desktop).

    Requer: pip install 'rpa-core[botcity-core]'
    """

    def __init__(self, logger: LoggerFactory) -> None:
        if not _DISPONIVEL:
            raise ImportError(
                "botcity-framework-core não instalado. "
                "Execute: pip install 'rpa-core[botcity-core]'"
            )
        self._logger = logger
        self._bot = None

    @property
    def bot(self) -> DesktopBot:
        return self._bot

    def start(self) -> None:
        self._bot = DesktopBot()
        self._logger.info("DesktopBot iniciado")

    def stop(self) -> None:
        if self._bot:
            self._bot = None
            self._logger.info("DesktopBot encerrado")
