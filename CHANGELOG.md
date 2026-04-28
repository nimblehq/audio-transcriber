# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Migrated from Gitflow to trunk-based development. `main` is now the single long-lived branch; `develop` has been retired. CI runs on `main` only and squash-merge is the sole allowed merge method. See `CLAUDE.md` for the full workflow.

## [1.1.0] - 2026-02-26

### Added

- Web UI for transcription and meeting analysis: upload, progress tracking, synced transcripts, speaker renaming, and LLM prompt generation from analysis templates.
- Browser desktop notifications when transcription completes.

### Changed

- Rewrote "Getting Started" in the README for non-technical users.

### Fixed

- Notification permission request not triggering on first use.

## [1.0.0] - 2026-02-26

### Added

- Initial release: command-line transcription with WhisperX and PyAnnote speaker diarization.
- `.env` file support for persistent `HF_TOKEN` configuration via `python-dotenv`.
- Skip alignment for languages without wav2vec2 support.
- README with virtual environment setup instructions.
