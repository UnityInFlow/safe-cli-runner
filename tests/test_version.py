"""Smoke test: the package imports and carries a PEP 440 version."""

import importlib.metadata
import re

import pytest

import safe_cli_runner

PEP440 = re.compile(r"^\d+\.\d+\.\d+(\.dev\d+)?$")


def test_version_is_pep440() -> None:
    assert PEP440.match(safe_cli_runner.__version__)


def test_version_matches_installed_metadata() -> None:
    assert importlib.metadata.version("safe-cli-runner") == safe_cli_runner.__version__


@pytest.mark.asyncio
async def test_asyncio_mode_is_wired() -> None:
    # Keeps pytest-asyncio configured before the first real coroutine test lands.
    assert safe_cli_runner.__doc__ is not None
    assert "RunnerConfig" in safe_cli_runner.__doc__
