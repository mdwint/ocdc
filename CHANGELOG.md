# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## Unreleased

### Changed

- Upgraded to Pydantic v2.

### Removed

- Dropped Python 3.7 support.

### Fixed

- Use a single trailing newline when writing to stdout.


## 0.3.3 - 2022-08-10

### Fixed

- Don't introduce newlines when merging duplicate changes sections.


## 0.3.2 - 2022-08-05

### Fixed

- Strip whitespace between version numbers and dates.
- Skip newlines before changelog title.


## 0.3.1 - 2022-08-04

### Fixed

- Raise error on missing title before changes.
- Strip trailing whitespace from text.


## 0.3.0 - 2022-08-02

### Added

- Pass `--path -` to read the changelog from stdin and write the formatted result to
  stdout. This is useful for integrating with text editors.


## 0.2.3 - 2022-08-01

### Fixed

- Report column 1 in errors instead of 0.


## 0.2.2 - 2022-08-01

### Fixed

- Raise error on wrong title level before changes.
- Raise error on duplicate version sections.
- Merge duplicate changes sections.


## 0.2.1 - 2022-08-01

### Fixed

- Add `packaging` dependency.


## 0.2.0 - 2022-08-01

### Added

- Print message on success.

### Changed

- Sort version sections by version number.
- Sort changes sections by type.


## 0.1.1 - 2022-08-01

### Fixed

- Handle footers in the intro section.


## 0.1.0 - 2022-08-01

### Added

- Initial version.
