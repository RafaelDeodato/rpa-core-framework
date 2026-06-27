from __future__ import annotations

from rpa_core.logger import LoggerFactory
from rpa_core.maestro_log_service import MaestroLogService


class ProcessRunner:
    """Orquestra o ciclo de vida da execução: início, sucesso e erro.

    Centraliza o tratamento de exceções e o registro de logs locais e no Maestro,
    liberando os workflows de se preocuparem com essa infraestrutura.
    """

    def __init__(
        self,
        logger: LoggerFactory,
        maestro_logger: MaestroLogService | None = None,
    ) -> None:
        self._logger = logger
        self._maestro_logger = maestro_logger

    def run(self, workflow) -> None:
        self._logger.info("Processo iniciado")
        if self._maestro_logger:
            self._maestro_logger.info("Processo iniciado", step="PROCESSO")

        try:
            workflow.execute()
        except Exception as exc:
            self._logger.exception(f"Processo finalizado com erro: {exc}")
            if self._maestro_logger:
                self._maestro_logger.error(f"Erro na execução: {exc}", step="PROCESSO")
            raise
        else:
            self._logger.info("Processo finalizado com sucesso")
            if self._maestro_logger:
                self._maestro_logger.info("Processo finalizado com sucesso", step="PROCESSO")
