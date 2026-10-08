# Upstream Lineage & Tracking

`googletrans-curl` is a maintained fork of [ssut/py-googletrans](https://github.com/ssut/py-googletrans).

---

## Origin Baseline

- **Upstream Repository:** `https://github.com/ssut/py-googletrans`
- **Baseline Commit:** `db0567f89d3201b787074cc1c53418763d5e6bcc` (April 25, 2025)
- **Baseline Version:** `4.0.2`
- **Original Author:** SuHun Han (`suhunhankr@gmail.com`)
- **Fork Maintainer:** Matthias Kreier (`https://github.com/kreier`)

---

## Motivation for the Fork

Upstream `googletrans` uses `httpx` directly to communicate with Google Translate web service endpoints (`translate.google.com` / `translate.googleapis.com`). In recent years, Google deployed advanced bot detection and TLS fingerprinting mechanisms that frequently result in `HTTP 429 Too Many Requests` or `HTTP 403 Forbidden` responses for standard HTTP clients.

`googletrans-curl` solves this problem by integrating `curl-cffi`, allowing requests to impersonate modern browser TLS and HTTP/2 fingerprints (`impersonate="chrome"`), while keeping 100% backward compatibility as a drop-in replacement.

---

## License & Attribution

This project continues to be licensed under the **MIT License**, consistent with the upstream repository.

Original copyright belongs to SuHun Han (2015). Enhancements and modifications are copyright (c) 2026 Matthias Kreier and contributors.
