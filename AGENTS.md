# AGENTS.md

## Project Overview

`googletrans-curl` is a maintained, drop-in replacement fork of `ssut/py-googletrans`.

The primary mission is to resolve Google Translate HTTP 429 rate-limiting issues by introducing a modern browser-impersonating HTTP transport based on `curl-cffi`, while keeping 100% backward compatibility with existing codebases using `googletrans`.

---

## Core Principles

1. **Preserve Public API Compatibility**: The public API of `googletrans` must never be broken unless a deliberate breaking change is documented, reviewed, and approved.
2. **Drop-in Namespace Guarantee**: The distribution package is `googletrans-curl`, but the Python import namespace remains `googletrans` (`from googletrans import Translator`). Never rename the Python package namespace.
3. **Small, Testable Changes**: Prefer incremental, test-backed improvements over large rewrites.
4. **Deterministic Unit Testing**: Tests for translation parsing, URL construction, and token generation must be deterministic and runnable offline without hitting live Google Translate endpoints.
5. **Separate Live Tests**: Tests requiring live internet calls to `translate.google.com` or `translate.googleapis.com` must be clearly marked with `@pytest.mark.live`.
6. **Robust Transport Abstraction**: The library supports both `curl-cffi` (default) and `httpx`. Changes to transport handling must support both and handle connection/timeout exceptions gracefully.
7. **Documented Rationale**: Every user-visible change, bug fix, or dependency update must be reflected in `CHANGELOG.md` and aligned with `ROADMAP.md`.
8. **Upstream Attribution & Sync**: Respect upstream `ssut/py-googletrans` MIT license and track upstream changes in `UPSTREAM.md`.

---

## Drop-in Compatibility Rules

The package must be installable as:

```bash
pip install googletrans-curl
```

Existing applications must continue working with zero source modifications:

```python
from googletrans import Translator

translator = Translator()
result = await translator.translate("Hello world", dest="ko")
```

Do not introduce changes that require users to import from `googletrans_curl`.

---

## Development Workflow

### Before Modifying Code:
- Read `ROADMAP.md` to see the current milestone and priorities.
- Review `CHANGELOG.md` to understand recent changes.
- Check relevant deterministic tests in `tests/`.
- Understand whether behavior originates upstream or from `googletrans-curl`.

### After Modifying Code:
- Add or update deterministic tests.
- Run the test suite: `.venv/bin/pytest`
- Format and lint code if applicable (`ruff check googletrans`).
- Update `CHANGELOG.md` when user-facing behavior or internals are modified.
- Update `ROADMAP.md` when milestone goals are completed.

---

## Quality Gates for Releases

A release cannot be cut merely because code "appears working". It requires:
- All deterministic tests passing in offline/sandboxed environments.
- Live integration tests passing against Google Translate.
- Clean wheel and sdist build (`uv build`).
- Documentation updated and verified.
