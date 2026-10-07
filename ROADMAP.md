# Roadmap

This roadmap outlines the path from initial fork foundation to the stable **5.0.0** release.

---

## 4.0.3 — Initial Working Release (Current)

**Goal:** Establish `googletrans-curl` as a working, drop-in replacement on PyPI for community testing.

- [x] Fork `ssut/py-googletrans` at 4.0.2 baseline (`db0567f89d3201b787074cc1c53418763d5e6bcc`).
- [x] Set PyPI distribution package name to `googletrans-curl` with import namespace `googletrans`.
- [x] Implement `curl-cffi` HTTP transport with Chrome browser impersonation as default to avoid HTTP 429 rate limits.
- [x] Add transport selection flags (`transport="auto"|"curl"|"httpx"`, `impersonate="chrome"`).
- [x] Fix async command-line tool `translate` (`googletrans.cli`).
- [x] Create core documentation: `AGENTS.md`, `CHANGELOG.md`, `ROADMAP.md`, `UPSTREAM.md`, and modernized `README.md`.
- [x] Separate deterministic unit tests from live integration tests.
- [ ] Publish 4.0.3 to PyPI for public testing and feedback.

---

## 4.1.0 — Upstream Issue & PR Triage

**Goal:** Tackle pending upstream bugs and evaluate community pull requests.

- [ ] **Triage 5 pending upstream issues:**
  - Investigate open issues in `ssut/py-googletrans` (e.g. edge-case character encoding, language detection anomalies).
  - Add regression tests for confirmed bugs.
  - Fix validated issues in `googletrans-curl`.
- [ ] **Review 6 open pull requests:**
  - Audit open pull requests in `ssut/py-googletrans` for still-viable enhancements and bugfixes.
  - Cherry-pick or re-implement clean PRs with proper tests and credit.
- [ ] Improve error reporting and timeout diagnostics across both transports.

---

## 4.2.0 — Fork Ecosystem Mining

**Goal:** Investigate improvements and patches across the 740 forks of `py-googletrans`.

- [ ] Analyze most starred and active forks of `ssut/py-googletrans`.
- [ ] Identify recurring patterns and community fixes:
  - Alternative endpoint routing (`translate.googleapis.com` vs webapp).
  - Bulk translation optimizations and concurrency improvements.
  - Proxy and network resiliency enhancements.
- [ ] Incorporate verified improvements into `googletrans-curl` with regression tests.

---

## 4.3.0 — Transport Architecture Refinement

**Goal:** Formalize the modular transport architecture.

- [ ] Extract transport implementations into dedicated submodules:
  - `googletrans/transport/base.py`
  - `googletrans/transport/curl.py`
  - `googletrans/transport/httpx.py`
- [ ] Benchmark performance and memory usage between `curl-cffi` and `httpx`.
- [ ] Add support for custom sessions and connection pooling configuration.

---

## 5.0.0 — Stable Milestone Release

**Goal:** First major stable release of `googletrans-curl`.

- [ ] Complete test suite passing across all supported Python versions (3.8 - 3.13).
- [ ] Full compatibility test matrix across Linux, macOS, and Windows.
- [ ] Comprehensive documentation with architecture diagrams, usage guides, and known web API limitations.
- [ ] API freeze: backwards compatibility guaranteed.
- [ ] Automated GitHub Actions CI/CD with PyPI Trusted Publishing (OIDC).
