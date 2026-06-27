import pytest
from unittest.mock import MagicMock
from rpa_core.process_runner import ProcessRunner
from rpa_core.logger import LoggerFactory


def test_run_chama_workflow_execute(logger):
    workflow = MagicMock()
    runner = ProcessRunner(logger=logger)
    runner.run(workflow)
    workflow.execute.assert_called_once()


def test_run_loga_inicio_e_sucesso(logger):
    workflow = MagicMock()
    runner = ProcessRunner(logger=logger)
    runner.run(workflow)
    assert logger.info.call_count >= 2


def test_run_propaga_excecao(logger):
    workflow = MagicMock()
    workflow.execute.side_effect = RuntimeError("falha")
    runner = ProcessRunner(logger=logger)
    with pytest.raises(RuntimeError, match="falha"):
        runner.run(workflow)


def test_run_loga_erro_no_maestro(logger):
    maestro_logger = MagicMock()
    workflow = MagicMock()
    workflow.execute.side_effect = RuntimeError("falha")
    runner = ProcessRunner(logger=logger, maestro_logger=maestro_logger)
    with pytest.raises(RuntimeError):
        runner.run(workflow)
    maestro_logger.error.assert_called_once()
