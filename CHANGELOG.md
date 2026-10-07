# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

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
