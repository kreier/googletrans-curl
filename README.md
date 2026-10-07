# googletrans-curl

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![GitHub Repo](https://img.shields.io/badge/github-kreier%2Fgoogletrans--curl-blue.svg)](https://github.com/kreier/googletrans-curl)

**googletrans-curl** is a fast, drop-in replacement fork of [`googletrans`](https://github.com/ssut/py-googletrans) that integrates [`curl-cffi`](https://github.com/lexiforest/curl_cffi) to eliminate Google Translate **HTTP 429 Too Many Requests** and rate-limiting blocks via browser TLS fingerprint impersonation.

---

## Drop-in Replacement for googletrans

The PyPI distribution package is named `googletrans-curl`, but the Python import namespace remains **`googletrans`**:

```bash
# Uninstall old package if present
pip uninstall googletrans

# Install drop-in replacement
pip install googletrans-curl
```

Existing applications continue importing `googletrans` with **zero code modifications**:

```python
from googletrans import Translator
```

---

## Why googletrans-curl?

The upstream `googletrans` uses `httpx` for HTTP requests. Google Translate's web endpoints actively monitor client TLS handshakes and HTTP/2 settings, frequently rejecting automated Python HTTP clients with `HTTP 429 Too Many Requests` or `HTTP 403 Forbidden`.

`googletrans-curl` solves this by introducing a flexible HTTP layer backed by `curl-cffi`. By impersonating real browser fingerprints (default: Chrome), requests match legitimate browser traffic and bypass fingerprint-based rate limiting.

### Architecture

```text
                  Existing Application
                          │
                          │ from googletrans import Translator
                          ▼
                  ┌───────────────┐
                  │  Translator   │
                  │  Python API   │
                  └───────┬───────┘
                          │
                  ┌───────▼───────┐
                  │ HTTP Session  │
                  │  Abstraction  │
                  └───┬───────┬───┘
                      │       │
      transport="curl"│       │ transport="httpx"
                      │       │
                      ▼       ▼
                  curl-cffi httpx
                      │
           (Chrome impersonation)
                      │
                      ▼
            Google Translate Service
```

---

## Features

- **Drop-in Compatible**: 100% compatible with existing `googletrans` code.
- **Anti-429 Protection**: Uses `curl-cffi` with Chrome TLS/HTTP2 impersonation.
- **Pluggable Transports**: Switch between `curl` (anti-blocking) and standard `httpx`.
- **Async First**: Native `async`/`await` support with async context manager.
- **Bulk Translation**: Efficiently translate batches of text in a single request.
- **Auto Language Detection**: Automatically detect language and confidence scores.
- **CLI Tool Included**: Includes the command-line utility `translate`.
- **Complete Type Annotations**: Fully typed for modern Python environments.

---

## Installation

```bash
pip install googletrans-curl
```

Requirements: Python 3.8 or newer.

---

## Quickstart

### Basic Usage (Async)

```python
import asyncio
from googletrans import Translator

async def main():
    async with Translator() as translator:
        # Detect and translate to English (default)
        result = await translator.translate("안녕하세요.")
        print(result.text)  # "Hello."
        print(result.src)   # "ko"

        # Translate to Japanese
        result = await translator.translate("안녕하세요.", dest="ja")
        print(result.text)  # "こんにちは。"

        # Specify source language
        result = await translator.translate("veritas lux mea", src="la", dest="en")
        print(result.text)  # "truth is my light"

asyncio.run(main())
```

---

## Transport Configuration

By default, `Translator()` automatically uses `curl-cffi` with Chrome impersonation. You can customize the transport and browser fingerprint as needed:

```python
from googletrans import Translator

# Default: automatic browser impersonation via curl-cffi
translator = Translator()

# Explicit curl transport with Safari impersonation
translator = Translator(
    transport="curl",
    impersonate="safari",
)

# Standard httpx transport
translator = Translator(
    transport="httpx",
)
```

Available impersonation presets for `curl-cffi` include: `"chrome"`, `"chrome110"`, `"chrome120"`, `"safari"`, `"safari15_3"`, `"safari15_5"`, `"edge99"`, `"edge101"`, etc.

---

## Advanced Usage

### Bulk Translation

Translate multiple strings in a single call:

```python
import asyncio
from googletrans import Translator

async def main():
    async with Translator() as translator:
        phrases = ["The quick brown fox", "jumps over", "the lazy dog"]
        translations = await translator.translate(phrases, dest="ko")
        for item in translations:
            print(f"{item.origin} -> {item.text}")

asyncio.run(main())
```

### Language Detection

Detect the language of text with confidence scores:

```python
import asyncio
from googletrans import Translator

async def main():
    async with Translator() as translator:
        detection = await translator.detect("이 문장은 한글로 쓰여졌습니다.")
        print(detection.lang)        # "ko"
        print(detection.confidence)  # 0.27...

asyncio.run(main())
```

### Custom Service URLs

Use alternate Google Translate service endpoints:

```python
# Rotate across multiple domains
translator = Translator(service_urls=[
    "translate.google.com",
    "translate.google.co.kr",
])

# Direct client API (no token acquirer needed)
translator = Translator(service_urls=[
    "translate.googleapis.com",
])
```

---

## Command-Line Tool

`googletrans-curl` includes the `translate` CLI command:

```bash
# Translate text to English (default)
translate "veritas lux mea" -s la -d en

# Translate text to Korean
translate "Hello world" -d ko

# Detect language
translate -c "안녕하세요."
```

---

## Unofficial API Disclaimer

> [!WARNING]
> This library uses Google Translate's unofficial web endpoints (`translate.google.com`).
> - While `curl-cffi` impersonation drastically reduces 429 blocks, Google may modify web endpoints at any time.
> - Maximum character limit per single request is approximately 15,000 characters.
> - For mission-critical production environments requiring guaranteed SLAs, please use [Google Cloud Translation API](https://cloud.google.com/translate/docs).

---

## License

This project is licensed under the [MIT License](LICENSE).
Upstream copyright (c) 2015 SuHun Han. Modifications copyright (c) 2026 Klaus Kreier and contributors.
