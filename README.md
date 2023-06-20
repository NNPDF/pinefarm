# Pinefarm

<p align="center">
  <a href="https://github.com/NNPDF/pinefarm/actions/workflows/unittests.yml"><img alt="Tests" src="https://github.com/NNPDF/pinefarm/actions/workflows/unittests.yml/badge.svg" /></a>
  <a href="https://pinefarm.readthedocs.io/en/latest/?badge=latest"><img alt="Docs" src="https://readthedocs.org/projects/pinefarm/badge/?version=latest"></a>
</p>

Generate [PineAPPL grids](https://github.com/NNPDF/pineappl) from [pinecards](https://github.com/NNPDF/pinecards).

## Installation

pinefarm is available via
- PyPI: <a href="https://pypi.org/project/pinefarm/"><img alt="PyPI" src="https://img.shields.io/pypi/v/pinefarm"/></a>
```bash
pip install pinefarm
```

### Dev

For development you need the following tools:

- `poetry`, follow [installation
  instructions](https://python-poetry.org/docs/#installation)
- `poetry-dynamic-versioning`, used to manage the version (see
  [repo](https://github.com/mtkennerly/poetry-dynamic-versioning))
- `pre-commit`, to run maintenance hooks before commits (see
  [instructions](https://pre-commit.com/#install))

See [below](.github/CONTRIBUTING.md#non-python-dependencies) for a few more
dependencies (already available on most systems).

## Documentation
- The documentation is available here: <a href="https://pinefarm.readthedocs.io/en/latest/?badge=latest"><img alt="Docs" src="https://readthedocs.org/projects/pinefarm/badge/?version=latest"></a>
- To build the documentation from source run these commands

```sh
poetry shell
cd docs
make html
make view
```
