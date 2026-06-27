from __future__ import annotations

from botcity.maestro import BotMaestroSDK


class MaestroLogService:
    """Envia logs estruturados ao BotCity Maestro Orchestrator."""

    def __init__(self, maestro: BotMaestroSDK, process_name: str) -> None:
        self._maestro = maestro
        self._process_name = process_name
        self._log_created = False

    def info(self, message: str, step: str = "-") -> None:
        self._write("INFO", message, step)

    def warning(self, message: str, step: str = "-") -> None:
        self._write("WARNING", message, step)

    def error(self, message: str, step: str = "-") -> None:
        self._write("ERROR", message, step)

    def _write(self, level: str, message: str, step: str) -> None:
        try:
            self._ensure_log_exists()
            self._maestro.new_log_entry(
                activity_label=self._process_name,
                values={"Level": level, "Message": message, "Step": step},
            )
        except Exception as exc:
            print(f"[WARN] Falha ao enviar log ao Maestro: {exc}")

    def _ensure_log_exists(self) -> None:
        if self._log_created:
            return
        from botcity.maestro import Column
        try:
            self._maestro.get_log(self._process_name)
        except Exception:
            try:
                self._maestro.new_log(
                    activity_label=self._process_name,
                    columns=[
                        Column(name="Level", label="Level", width=50),
                        Column(name="Message", label="Message", width=2000),
                        Column(name="Step", label="Step", width=200),
                    ],
                )
            except Exception as exc:
                print(f"[WARN] Falha ao criar log no Maestro: {exc}")
        self._log_created = True
