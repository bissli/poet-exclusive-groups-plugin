"""End-to-end checks of the group filter through the Poetry CLI.

Each test runs the Poetry installed beside the plugin against a project
whose dev and prod groups give one package two path sources.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

PACKAGE_PYPROJECT = """\
[project]
name = "{name}"
version = "1.0.0"
requires-python = ">=3.10"

[build-system]
requires = ["poetry-core>=2.0"]
build-backend = "poetry.core.masonry.api"
"""

APP_PYPROJECT = """\
[project]
name = "app"
version = "0.1.0"
requires-python = ">=3.10,<4.0"

[tool.poetry]
package-mode = false

[tool.poetry.group.dev.dependencies]
foo = { path = "../lib_dev", develop = true }

[tool.poetry.group.prod.dependencies]
foo = { path = "../lib_prod" }

[tool.poetry.group.tools.dependencies]
bar = { path = "../lib_tools" }
"""


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """The app directory, beside lib_dev, lib_prod and lib_tools.
    """
    libraries = [('lib_dev', 'foo'), ('lib_prod', 'foo'), ('lib_tools', 'bar')]
    for folder, name in libraries:
        (tmp_path / folder / name).mkdir(parents=True)
        (tmp_path / folder / name / '__init__.py').touch()
        pyproject = PACKAGE_PYPROJECT.format(name=name)
        (tmp_path / folder / 'pyproject.toml').write_text(pyproject)
    (tmp_path / 'app').mkdir()
    (tmp_path / 'app' / 'pyproject.toml').write_text(APP_PYPROJECT)
    return tmp_path / 'app'


def run_update(project: Path, *options: str) -> str:
    """Combined output of a dry-run 'poetry update' in project.
    """
    env = {
        **os.environ,
        'POETRY_VIRTUALENVS_PATH': str(project.parent / 'venvs'),
        'POETRY_VIRTUALENVS_IN_PROJECT': 'false',
        }
    command = [sys.executable, '-m', 'poetry', 'update', '--dry-run', '--no-ansi']
    result = subprocess.run(
        [*command, *options],
        cwd=project,
        env=env,
        capture_output=True,
        text=True)
    return result.stdout + result.stderr


def test_only_prod_installs_prod_source(project):
    """Verify --only prod resolves foo from the prod group's path alone.

    Mutation: the --only branch skipped, so both foo sources reach the
      solver and it reports incompatible constraints.
    Oracle: the lib_prod and lib_dev directory names the fixture writes.
    """
    output = run_update(project, '--only', 'prod')
    assert 'lib_prod' in output
    assert 'lib_dev' not in output


def test_without_prod_installs_dev_path(project):
    """Verify --without prod resolves foo from the dev group's path alone.

    Mutation: the --without branch skipped, so both foo sources reach the
      solver and it reports incompatible constraints.
    Oracle: the lib_prod and lib_dev directory names the fixture writes.
    """
    output = run_update(project, '--without', 'prod')
    assert 'lib_dev' in output
    assert 'lib_prod' not in output


def test_only_comma_list_names_two_groups(project):
    """Verify --only prod,tools keeps both groups, as Poetry's split does.

    Mutation: the option value passed through unsplit, so 'prod,tools'
      matches no group and nothing installs.
    Oracle: the lib_prod and lib_tools directory names the fixture writes.
    """
    output = run_update(project, '--only', 'prod,tools')
    assert 'lib_prod' in output
    assert 'lib_tools' in output
    assert 'lib_dev' not in output
