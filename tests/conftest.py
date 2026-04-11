"""Test configuration and fixtures."""

import pytest
import tempfile
import shutil
from pathlib import Path


@pytest.fixture
def temp_dir():
    """Create a temporary directory for each test."""
    dir_path = tempfile.mkdtemp()
    yield Path(dir_path)
    shutil.rmtree(dir_path)


@pytest.fixture
def temp_project(temp_dir):
    """Create a temporary project structure."""
    from runtime.adapters.filesystem_adapter import FilesystemAdapter

    fs = FilesystemAdapter()
    fs.ensure_dir(temp_dir)
    fs.ensure_dir(temp_dir / "execution-packs")
    fs.ensure_dir(temp_dir / "execution-results")
    fs.ensure_dir(temp_dir / "reviews")
    fs.ensure_dir(temp_dir / "features")

    yield temp_dir