# Poet Plugin
A Poetry plugin to enable exclusivity between groups.  
Poet stands for **Po**etry **E**xclusivity **T**oggle (or some other excuse, I did not want a verbose package name and
`poet` seemed short and sweet since this plugin changes the internal poetry package during runtime).

## Installation
### Per project
Poetry 2 installs the plugins a project declares:
```toml
[tool.poetry.requires-plugins]
poet-plugin = "*"
```
The first `poetry install` after the declaration fetches the plugin into `.poetry/plugins` but resolves without it, so in a
project whose groups conflict that run fails. Every later command loads the plugin.

### For every project
```shell
poetry self add poet-plugin
```
This installs into Poetry's own environment, so a project's conflicting groups never block it.

## Usage
`poetry update` reads `--only` and `--without` and drops the excluded groups before Poetry resolves the project. Two
groups can then define one package from different sources, such as a local path in `dev` and a git URL in `prod`. A
comma-separated value names several groups, as in Poetry itself: `--only prod,tools`.

The lock holds only the groups the last resolve kept. `poetry install` filters the same way when no lock exists, but
with a lock present it installs from the lock and never resolves, so a switch from `prod` to `dev` takes
`poetry update`. A bare `poetry update` sees both definitions of the package and fails. `poetry lock`, `poetry add`
and `poetry remove` take no group options, so they fail in such a project.

### Example
A mono-repository `pyproject.toml`:
```toml
[project]
name = "app"
version = "0.1.0"
requires-python = ">=3.10"

[tool.poetry]
package-mode = false

[tool.poetry.requires-plugins]
poet-plugin = "*"

[tool.poetry.group.prod.dependencies]
foo = { git = "https://github.com/bar/foo", subdirectory = "src/libs/foo" }

[tool.poetry.group.dev.dependencies]
foo = { path = "../../libs/foo", develop = true }
```

| Source of `foo` | Command                                                      |
| --------------- | ------------------------------------------------------------ |
| prod (git)      | `poetry update --only prod` or `poetry update --without dev` |
| dev (path)      | `poetry update --only dev` or `poetry update --without prod` |

## Tests
The tests run Poetry with the plugin against a toy project in a temporary directory:
```shell
poetry install
poetry run pytest
```
