"""Smoke: workspace packages import after uv sync."""

from atlas_api import __version__ as api_version
from atlas_common import __version__ as common_version
from atlas_worker import __version__ as worker_version


def test_common_version() -> None:
    assert common_version == "0.1.0"


def test_api_and_worker_importable() -> None:
    assert api_version == "0.1.0"
    assert worker_version == "0.1.0"
