import pytest
from unittest.mock import MagicMock
from rpa_core.logger import LoggerFactory


def test_botcity_web_service_sem_dependencia(monkeypatch):
    import rpa_core.services.botcity_web_service as m
    monkeypatch.setattr(m, "_DISPONIVEL", False)
    from rpa_core.services.botcity_web_service import BotCityWebService
    with pytest.raises(ImportError, match="rpa-core\\[botcity-web\\]"):
        BotCityWebService(timeout_seconds=30, logger=MagicMock(spec=LoggerFactory))


def test_botcity_core_service_sem_dependencia(monkeypatch):
    import rpa_core.services.botcity_core_service as m
    monkeypatch.setattr(m, "_DISPONIVEL", False)
    from rpa_core.services.botcity_core_service import BotCityCoreService
    with pytest.raises(ImportError, match="rpa-core\\[botcity-core\\]"):
        BotCityCoreService(logger=MagicMock(spec=LoggerFactory))


def test_selenium_service_sem_dependencia(monkeypatch):
    import rpa_core.services.selenium_service as m
    monkeypatch.setattr(m, "_DISPONIVEL", False)
    from rpa_core.services.selenium_service import SeleniumService
    with pytest.raises(ImportError, match="rpa-core\\[selenium\\]"):
        SeleniumService(timeout_seconds=30, logger=MagicMock(spec=LoggerFactory))


def test_playwright_service_sem_dependencia(monkeypatch):
    import rpa_core.services.playwright_service as m
    monkeypatch.setattr(m, "_DISPONIVEL", False)
    from rpa_core.services.playwright_service import PlaywrightService
    with pytest.raises(ImportError, match="rpa-core\\[playwright\\]"):
        PlaywrightService(timeout_seconds=30, logger=MagicMock(spec=LoggerFactory))


def test_maestro_log_service_sem_dependencia(monkeypatch):
    import rpa_core.maestro_log_service as m
    monkeypatch.setattr(m, "_DISPONIVEL", False)
    from rpa_core.maestro_log_service import MaestroLogService
    with pytest.raises(ImportError, match="rpa-core\\[maestro\\]"):
        MaestroLogService(maestro=MagicMock(), process_name="test")
