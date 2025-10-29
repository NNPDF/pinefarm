# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased](https://github.com/NNPDF/pinefarm/compare/v0.4.0...HEAD)

## [0.4.0](https://github.com/NNPDF/pinefarm/compare/v0.3.3...v0.4.0) - 2025-10-29

### Added

- Added `NNLOJET` install helper and pinecard generation
- Added `--finalize` and `--dry` CLI flags
- Added tutorials on `PineAPPL` conversion using Nix

### Changed

- Updated `PineAPPL` to version v1
- Updated MG5 interface to version 3.6.5
- Updated `Yadism` to version 0.13.7
- Updated multiple pre-commit configurations
- Reworked MG5 cut configuration using JSON and dictionary-based defaults
- Updated linting and CI setup

### Fixed

- Fixed CKM running
- Fixed MG5 cut definitions and variable naming errors
- Fixed repository URL in `pyproject.toml`

### Internal / Maintenance

- Added `integrability v1` and updated positivity tests
- Changed behavior to fail when no pinecard is found
- Whitelisted `PineAPPL` for pylint and re-enabled checks
- General cleanup and minor stylistic fixes

---
