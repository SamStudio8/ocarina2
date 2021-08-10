# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 0.42.0 2021-08-10
### Changed
* Changed exit codes to cover more cases using codes recommended by `sysexits`
### Fixed
* Error message and exit code returned in the case where the `.ocarina` or `.ocarina-tokens` JSON is malformed

## 0.41.4 2021-07-30
### Fixed
* Ocarina will reload OAuth2 tokens from disk before each request to reduce the likelihood of polling queries from failing
### Changed
* `get pag` has a configuration stanza to correctly support OAuth with `temp_can_read_pags_via_api` scope

## 0.41.2 2021-06-11
### Changed
* `get biosample` subcommand now supports OAuth using `majora2.view_biosampleartifact` scope

## 0.41.1 2021-06-05
### Added
* Spruced up `ocarina info` using the very fancy [`rich` library](https://github.com/willmcgugan/rich), you can disable this with `--boring`

## 0.40.2 2021-05-25
### Changed
* `ocarina empty biosample` now has two modes:
    * Existing `--ids hoot meow honk` mode allows one or more biosample artifacts named `central_sample_id` to be forced into existence, unchanged for backward compatability
    * `--central-sample-id hoot --sender-sample-id secret_hoot` allows one biosample named `central_sample_id` with its `sender_sample_id` to be forced into existence

## 0.39.2 2021-05-24
### Changed
* `get dataview --output-table` now handles dataviews with nested data, one level deeper

### Fixed
* Fixed incorrectly documented version number for last release in CHANGELOG, incorrectly referred to as 0.31.1 instead of 0.39.1

## 0.39.1 2021-05-23
### Added
* `OCARINA_QUIET` config option (supported both by `--env` and `~/.ocarina` JSON) can be set to non-zero (`0`) to suppress *all* non-output messages without `--quiet`
* `--no-banner` command line option suppresses the welcoming ocarina banner
* `OCARINA_NO_BANNER` config option (supported both by `--env` and `~/.ocarina` JSON) can be set to non-zero (`0`) to suppress the welcoming ocarina banner without `--no-banner`
    * You're welcome, @m-bull [#12]

### Changed
* `ocarina info` metadata lines are now printed in key sorted order

## 0.39.0 2021-04-27
### Added
* Experimental `info` command to grab basic metadata on any artifact in Majora

## 0.38.4 2021-04-26
### Changed
* `put tag` subcommand now supports OAuth using `majora2.add_majorametarecord majora2.change_majorametarecord` scopes

## 0.38.3 2021-04-22
### Added
* Better late than never, `CHANGELOG.md` will now document notable changes to Ocarina
### Changed
* `get biosample-validity` subcommand now supports OAuth using `majora2.view_biosampleartifact` scope
