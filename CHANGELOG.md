# Changelog for httpkom

## Unreleased

### Added

- Nothing yet.

### Changed

- Fix version handling. It wasn't possible to install httpkom due to
  the way we tried to single source the package version.


## 0.13 (2020-02-06)

### Added

- Run with python3 -m httpkom (instead of httpkom.main)
- Now uses asyncio version of pylyskom
- Converted from using Flask to Quart (and Hypercorn)


## 0.12 (2020-01-24)

### Added

- Should now run as a standalone process, not an WSGI app
- Python 3 support
- Internal counters (stats / metrics)
- Stats reporting to Graphite
- Published on PyPI


## 0.11 (2016-05-29)

### Added

- Setting version on what has been working okay for several years now.
- Added changelog.

### Changed

- Lots of refactoring


## 0.10 (2013-02-11)

## 0.9 (2013-01-08)

## 0.8 (2012-12-07)

## 0.7 (2012-12-02)

## 0.6 (2012-10-21)
