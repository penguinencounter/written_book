# written_book

# On hold

## Currently working on `pixelscribe`, the renderer powering this project, in a seperate repository.

[![GitHub Actions](https://github.com/penguinencounter/written_book/workflows/CI/badge.svg)](https://github.com/FIXME/FIXME/actions)
[![PyPI](https://img.shields.io/pypi/v/FIXME.svg)](https://pypi.org/project/FIXME/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/FIXME.svg)](https://pypi.org/project/FIXME/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

> Dynamic in-game datapack documentation for Minecraft.

## Introduction

fonts everywhere

## Installation

The package can be installed with `pip`.

```bash
$ pip install written_book
```

## Getting started

FIXME

## Contributing

Contributions are welcome. Make sure to first open an issue discussing the problem or the new feature before creating a pull request. The project uses [`poetry`](https://python-poetry.org).

```bash
$ poetry install
```

You can run the tests with `poetry run pytest`.

```bash
$ poetry run pytest
```

The project must type-check with [`pyright`](https://github.com/microsoft/pyright). If you're using VSCode the [`pylance`](https://marketplace.visualstudio.com/items?itemName=ms-python.vscode-pylance) extension should report diagnostics automatically. You can also install the type-checker locally with `npm install` and run it from the command-line.

```bash
$ npm run watch
$ npm run check
```

The code follows the [`black`](https://github.com/psf/black) code style. Import statements are sorted with [`isort`](https://pycqa.github.io/isort/).

```bash
$ poetry run isort written_book examples tests
$ poetry run black written_book examples tests
$ poetry run black --check written_book examples tests
```

---

License - [MIT](https://github.com/FIXME/FIXME/blob/main/LICENSE)
