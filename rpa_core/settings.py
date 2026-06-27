from __future__ import annotations

from configparser import ConfigParser, Error as ConfigParserError
from dataclasses import dataclass
from pathlib import Path

DEFAULT_SETTINGS_PATH = Path("settings.ini")


@dataclass(frozen=True)
class Settings:
    """Configurações tipadas carregadas exclusivamente de settings.ini."""

    environment: str
    timeout_seconds: int
    log_level: str
    log_directory: Path

    @classmethod
    def load(cls, path: str | Path | None = None) -> Settings:
        settings_path = Path(path) if path else DEFAULT_SETTINGS_PATH
        if not settings_path.is_file():
            raise FileNotFoundError(f"Arquivo de configuração não encontrado: {settings_path}")

        parser = ConfigParser()
        if not parser.read(settings_path, encoding="utf-8"):
            raise ValueError(f"Não foi possível ler o arquivo: {settings_path}")

        try:
            return cls(
                environment=parser.get("application", "environment"),
                timeout_seconds=parser.getint("automation", "timeout_seconds"),
                log_level=parser.get("logging", "level").upper(),
                log_directory=Path(parser.get("logging", "directory")),
            )
        except (ConfigParserError, KeyError, ValueError) as exc:
            raise ValueError(f"Configuração inválida em {settings_path}: {exc}") from exc
