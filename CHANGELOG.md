# Changelog for httpkom

## Unreleased


## 0.20 (2022-09-12)

### Added

- Added API for returning server info.
- Added API for setting presentation.
- Added API for setting password.

### Fixed

- Update required pylyskom version to 0.8 to fix issue with texts by
  anonymous users, and to add support for new functionality.


## 0.19 (2021-01-20)

### Fixed

- Fix dict serialization.


## 0.18 (2021-01-20)

### Changed

- Update to be compatible with next version of pylyskom.
- API changes: Changes "conf_name" to "name".


## 0.17 (2020-07-03)

### Fixed

- Update required pylyskom version to 0.5
- Fix use of AioKomSession methods that are now async.


## 0.16 (2020-07-01)

### Changed

- Update required pylyskom version to 0.4.


## 0.15 (2020-07-01)

### Changed

- Minor refactorings and changes.


## 0.14 (2020-02-07)

### Fixed

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
