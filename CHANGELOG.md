# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [4.1.0] - 2026-10-08

### Added
- **Synchronous Translator Wrapper (`SyncTranslator`)**: Added `SyncTranslator` and convenience methods `Translator.translate_sync()` / `Translator.detect_sync()` to seamlessly support blocking codebases and scripts without requiring manual `asyncio.run()` loops (resolves upstream Issue #451).
- **Modern ISO 639-1 Language Code Support**: Integrated updated ISO 639-1 two-letter and BCP-47 language codes from community PR #450 (e.g. `ab`, `aa`, `ba`, `br`, `ce`, `ch`, `cv`, `dz`, `fo`, `fj`, `ff`, `kl`, `kr`, `kg`, `kv`, `li`, `gv`, `mh`, `nr`, `oc`, `os`, `rn`, `se`, `sg`, `ss`, `ty`, `bo`, `to`, `tn`, `tyv`, `ve`, `wo`, `lua`, `sat-Latn`, `crh-Latn`, etc.).
- **100% Backward-Compatible Language Aliasing**: Retained legacy 3-letter codes (`abk`, `aar`, `bak`, etc.) as aliases in `LANGUAGES` to prevent breaking existing codebases.
- **Informative Error Types & Diagnostics**:
  - Added `TranslationError` base exception and `RateLimitError` (HTTP 429) subclass with clear status codes, error snippets, and actionable resolution suggestions.
  - Added informative logging warnings when `raise_exception=False` encounters non-200 responses.
- **Fallback Language Detection**:
  - Implemented neural model tag inspection fallback (`data[0][0][8]`) when Google's `gtx` endpoint fails to detect CJK/Traditional Chinese and returns the target language (resolves upstream Issue #446).
- **Dialect & Script Normalization**: Enhanced language code sanitizer to preserve dialect scripts and region subtags (`zh-cn`, `zh-tw`, `zh_cn`, `zh_tw`, etc.).

### Fixed
- Fixed upstream Issue #446: Corrected detection of Traditional Chinese text (`我想檢查一下它是否正常運作。`) which previously was misclassified as `en`.
- Fixed upstream Issue #457: Clear error diagnostics when HTTP 429/403 errors occur instead of silent fallback returning original text without explanation.
- Fixed upstream PR #450: Corrected `SPECIAL_CASES` mapping `ee` (Ewe) to `et` (Estonian); `ee` is now properly mapped to Ewe and `et` to Estonian.
- Regression-tested upstream Issue #448: Verified text with backticks and markdown symbols formats without extraneous prefix symbols.
- Regression-tested upstream Issue #447: CLI `translate` verified working deterministically.

---

## [4.0.3] - 2026-10-08

### Added
- **`curl-cffi` Transport Support**: Added `curl_cffi` as a primary dependency with browser TLS/HTTP fingerprint impersonation (`impersonate="chrome"`), effectively mitigating HTTP 429 rate-limiting from Google Translate.
- **Pluggable Transport Configuration**: Added `transport` (`"auto"`, `"curl"`, `"httpx"`) and `impersonate` options to `Translator.__init__`. Default `transport="auto"` prefers `curl_cffi` for anti-blocking benefits while preserving fallback to `httpx`.
- **Async Command-Line Interface**: Added `googletrans.cli` with `asyncio.run()` support, enabling the CLI tool (`translate`) to work seamlessly with the v4 async API.
- **Project Governance & Agent Documentation**:
  - `AGENTS.md`: Guidelines and principles for AI coding agents.
  - `ROADMAP.md`: Phased progression from 4.0.3 through 5.0.0.
  - `UPSTREAM.md`: Documentation of fork lineage from `ssut/py-googletrans`.
- **Session Lifecycle Support**: Added `aclose()` method to `Translator` for closing client sessions explicitly or via `async with Translator()`.

### Changed
- **Package Identity**: Renamed PyPI distribution package to `googletrans-curl`. The Python import namespace remains unchanged as `googletrans` for drop-in compatibility.
- **Build Configuration**: Configured `hatchling` in `pyproject.toml` to package the `googletrans` namespace directory under the `googletrans-curl` package distribution.
- **Exception Mapping**: Mapped `curl_cffi` timeout and connection exceptions to `httpx` exceptions (`ConnectTimeout`, `ConnectError`) for backward compatibility with existing exception handlers.
- **Documentation Overhaul**: Replaced `README.rst` with modern `README.md` including drop-in guide, architecture diagram, and transport customization.

### Fixed
- Fixed CLI `translate` crashing with `AttributeError: 'coroutine' object has no attribute 'src'` when invoked from the command line.
- Fixed pytest configuration warning (`omit = tests/*` moved out of `[pytest]`).

---

## [4.0.2] - Upstream Baseline

- Upstream release from `ssut/py-googletrans` (commit `db0567f89d3201b787074cc1c53418763d5e6bcc`).
