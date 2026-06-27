from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class OrchestratorLogger(Protocol):
    def info(self, message: str, step: str = "-") -> None: ...
    def warning(self, message: str, step: str = "-") -> None: ...
    def error(self, message: str, step: str = "-") -> None: ...
