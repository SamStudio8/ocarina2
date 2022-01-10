# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 0.47.2 2022-01-10
### Changed
* `.ocarina` file automatically created if it does not exist instead of suggesting the user creates it themselves
* Configuration and token files are created with better default permissions by setting `umask`
* Emits a warning if non-user read or write permissions are detected on the Ocarina configuration or token cache

## 0.47.1 2021-12-08
### Changed
* `empty biosample` command now supports `--metadata` when uploading single empty biosamples
    * Note that using `--metadata` with `--ids` is not supported and will emit a client side warning
* `api.put_force_linked_biosample` supports optional `metadata` parameter
### Fixed
* Corrected wrong version number in last CHANGELOG entry (46.1 was labelled as 46.0)

## 0.46.1 2021-12-02
### Changed
* `get pag` supports `--published-before`

## 0.46.0 2021-10-15
### Added
* New experimental (unsupported) functions added to importable API client
    * `put_force_linked_biosample`
    * `put_library`
    * `put_sequencing`
* `--print-config` option will dump out the Ocarina configuration (including secrets) for inspection
### Changed
* `MAJORA_TOKENS_FILE` config option (supported both by `--env` and `~/.ocarina` JSON) allows the tokens cache to be placed in a user-determined location (otherwise defaults to existing `~/.ocarina-tokens`)
### Fixed
* `library_primers` and `library_protocol` are now correctly sent to Majora when using the singular `--biosample` option for `put library`

## 0.44.2 2021-10-15
### Added
* `oauth authorise` will authorise an OAuth token for a particular endpoint for later use
### Changed
* `empty` subcommand supports `--sudo-as` command line option

## 0.44.0 2021-08-14
### Changed
* Util function `_wait_for_task` now controls all task result fetching for commands to remove significant code duplication
* `get sequencing` and `get sequencing --faster` have a configuration stanza to correctly support OAuth with `majora2.view_biosampleartifact` scope
* `api.majora.task.get` has a configuration stanza to correctly support scopeless OAuth
* `get pag`, `get dataview` and `get sequencing` will correctly support using `--task-id` (with or without `--task-wait`) to pick up a wait loop that was interrupted without issuing another task request
* Improved sysexit error codes for task waiting failure modes

## 0.43.0 2021-08-11
### Changed
* `pag suppress` has a configuration stanza to correctly support OAuth with `can_suppress_pags_via_api` scope
* `get summary` and `get outbound-summary` have configuration stanzas to correctly support scopeless OAuth

## 0.42.1 2021-08-10
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
