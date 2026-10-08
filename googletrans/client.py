"""
A Translation module.

You can translate text using this module.
"""

import asyncio
import logging
import random
import re
import threading
import typing

import httpx
from httpx import ConnectTimeout, Response, Timeout
from httpx._types import ProxyTypes

from googletrans import urls, utils
from googletrans.constants import (
    DEFAULT_CLIENT_SERVICE_URLS,
    DEFAULT_RAISE_EXCEPTION,
    DEFAULT_USER_AGENT,
    DUMMY_DATA,
    LANGCODES,
    LANGUAGES,
    SPECIAL_CASES,
    RateLimitError,
    TranslationError,
)
from googletrans.gtoken import TokenAcquirer
from googletrans.models import Detected, Translated

logger = logging.getLogger("googletrans")

EXCLUDES = ("en", "ca", "fr")


def _normalize_lang(code: str) -> str:
    """Normalize language code, preserving script/regional variants like zh-cn or zh-tw."""
    code = code.lower().strip()
    if "@" in code:
        code = code.split("@", 1)[0]
    if code in LANGUAGES:
        return code
    # Try replacing underscores with hyphens (e.g. zh_cn -> zh-cn)
    hyphenated = code.replace("_", "-")
    if hyphenated in LANGUAGES:
        return hyphenated
    # Fallback to base language code (e.g. en_us -> en, it_ch -> it)
    base = re.split(r"[-_]", code)[0]
    if base in LANGUAGES:
        return base
    return code


try:
    from curl_cffi.requests import AsyncSession
    from curl_cffi.requests.exceptions import RequestException as CurlRequestException
    from curl_cffi.requests.exceptions import Timeout as CurlTimeout
    CURL_AVAILABLE = True
except ImportError:  # pragma: no cover
    CURL_AVAILABLE = False
    CurlRequestException = Exception
    CurlTimeout = Exception


class Translator:
    """Google Translate ajax API implementation class

    You have to create an instance of Translator to use this API

    :param service_urls: google translate url list. URLs will be used randomly.
                         For example ``['translate.google.com', 'translate.google.co.kr']``
                         To preferably use the non webapp api, service url should be translate.googleapis.com
    :type service_urls: a sequence of strings

    :param user_agent: the User-Agent header to send when making requests.
    :type user_agent: :class:`str`

    :param transport: HTTP transport to use: 'auto' (default: uses curl-cffi if installed,
                      falling back to httpx), 'curl' (requires curl-cffi), or 'httpx'.
    :type transport: :class:`str`
    :param impersonate: Browser TLS/JA3/HTTP2 fingerprint to impersonate when using curl-cffi.
                        Defaults to 'chrome'.
    :type impersonate: :class:`str`
    :param proxy: proxy configuration.
    :param timeout: Definition of timeout.
    :param raise_exception: if `True` then raise exception if something goes wrong.
    :type raise_exception: boolean
    """

    def __init__(
        self,
        service_urls: typing.Sequence[str] = DEFAULT_CLIENT_SERVICE_URLS,
        user_agent: str = DEFAULT_USER_AGENT,
        raise_exception: bool = DEFAULT_RAISE_EXCEPTION,
        proxy: typing.Optional[ProxyTypes] = None,
        timeout: typing.Optional[Timeout] = None,
        http2: bool = True,
        list_operation_max_concurrency: int = 2,
        transport: typing.Literal["auto", "curl", "httpx"] = "auto",
        impersonate: str = "chrome",
    ):
        if transport not in ("auto", "curl", "httpx"):
            raise ValueError(
                f"Invalid transport: '{transport}'. Must be one of 'auto', 'curl', 'httpx'."
            )

        if transport == "curl":
            if not CURL_AVAILABLE:
                raise ImportError(
                    "curl_cffi is required when transport='curl'. "
                    "Install it via `pip install curl_cffi`."
                )
            use_curl = True
        elif transport == "httpx":
            use_curl = False
        else:  # transport == "auto"
            use_curl = CURL_AVAILABLE

        self.transport = "curl" if use_curl else "httpx"
        self.impersonate = impersonate

        if use_curl:
            timeout_sec = None
            if timeout is not None:
                if isinstance(timeout, httpx.Timeout):
                    timeout_sec = timeout.connect or timeout.read
                else:
                    timeout_sec = float(timeout)
                if timeout_sec is not None and 0 < timeout_sec < 0.001:
                    timeout_sec = 0.001

            session_kwargs: typing.Dict[str, typing.Any] = {
                "impersonate": impersonate,
                "headers": {
                    "User-Agent": user_agent,
                },
            }
            if timeout_sec is not None:
                session_kwargs["timeout"] = timeout_sec
            if isinstance(proxy, str):
                session_kwargs["proxy"] = proxy
            elif isinstance(proxy, dict):
                session_kwargs["proxies"] = proxy

            self.client = AsyncSession(**session_kwargs)
            self.client.aclose = self.client.close
        else:
            self.client = httpx.AsyncClient(
                http2=http2,
                proxy=proxy,
                headers={
                    "User-Agent": user_agent,
                },
            )
            if timeout is not None:
                self.client.timeout = timeout

        self.service_urls = ["translate.google.com"]
        self.client_type = "webapp"
        self.token_acquirer = TokenAcquirer(
            client=self.client, host=self.service_urls[0]
        )

        if service_urls:
            # default way of working: use the defined values from user app
            self.service_urls = service_urls
            self.client_type = "webapp"
            self.token_acquirer = TokenAcquirer(
                client=self.client, host=self.service_urls[0]
            )

            # if we have a service url pointing to client api we force the use of it as defaut client
            for t in enumerate(service_urls):
                api_type = re.search("googleapis", service_urls[0])
                if api_type:
                    self.service_urls = ["translate.googleapis.com"]
                    self.client_type = "gtx"
                    break

        self.raise_exception = raise_exception
        self.list_operation_max_concurrency = list_operation_max_concurrency

    def _pick_service_url(self) -> str:
        if len(self.service_urls) == 1:
            return self.service_urls[0]
        return random.choice(self.service_urls)

    async def __aenter__(self):
        return self

    async def aclose(self):
        """Close underlying HTTP client session."""
        if hasattr(self.client, "aclose"):
            await self.client.aclose()
        elif hasattr(self.client, "close"):
            await self.client.close()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.aclose()

    async def _translate(
        self, text: str, dest: str, src: str, override: typing.Dict[str, typing.Any]
    ) -> typing.Tuple[typing.List[typing.Any], typing.Any]:
        token = "xxxx"  # dummy default value here as it is not used by api client
        if self.client_type == "webapp":
            token = await self.token_acquirer.do(text)

        params = utils.build_params(
            client=self.client_type,
            query=text,
            src=src,
            dest=dest,
            token=token,
            override=override,
        )

        url = urls.TRANSLATE.format(host=self._pick_service_url())
        try:
            r = await self.client.get(url, params=params)
        except (CurlTimeout, httpx.TimeoutException) as exc:
            raise ConnectTimeout(str(exc)) from exc
        except CurlRequestException as exc:
            if "timeout" in str(exc).lower() or "timed out" in str(exc).lower():
                raise ConnectTimeout(str(exc)) from exc
            if self.raise_exception:
                raise TranslationError(
                    f"HTTP transport error during translation request: {exc}"
                ) from exc
            logger.warning("HTTP transport error: %s. Returning fallback dummy data.", exc)
            DUMMY_DATA[0][0][0] = text
            return DUMMY_DATA, None

        if r.status_code == 200:
            data = utils.format_json(r.text)
            if not isinstance(data, list):
                data = [data]  # Convert dict to list to match return type
            return data, r

        if self.raise_exception:
            if r.status_code == 429:
                raise RateLimitError(
                    f'Google Translate rate limit reached (HTTP 429) from {self.service_urls}. '
                    f'Consider using transport="curl" with browser impersonation, slowing requests, or rotating proxies.',
                    status_code=429,
                    response=r,
                )
            raise TranslationError(
                f'Unexpected status code "{r.status_code}" from {self.service_urls}. '
                f'Response: {r.text[:200]}',
                status_code=r.status_code,
                response=r,
            )

        logger.warning(
            "Google Translate returned HTTP %s from %s. Returning fallback dummy data because raise_exception=False.",
            r.status_code,
            self.service_urls,
        )
        DUMMY_DATA[0][0][0] = text
        return DUMMY_DATA, r

    async def build_request(
        self, text: str, dest: str, src: str, override: typing.Dict[str, typing.Any]
    ) -> httpx.Request:
        """Async helper for making the translation request"""
        token = "xxxx"  # dummy default value here as it is not used by api client
        if self.client_type == "webapp":
            token = await self.token_acquirer.do(text)

        params = utils.build_params(
            client=self.client_type,
            query=text,
            src=src,
            dest=dest,
            token=token,
            override=override,
        )

        url = urls.TRANSLATE.format(host=self._pick_service_url())

        return httpx.Request("GET", url, params=params)

    def _parse_extra_data(
        self, data: typing.List[typing.Any]
    ) -> typing.Dict[str, typing.Any]:
        response_parts_name_mapping = {
            0: "translation",
            1: "all-translations",
            2: "original-language",
            5: "possible-translations",
            6: "confidence",
            7: "possible-mistakes",
            8: "language",
            11: "synonyms",
            12: "definitions",
            13: "examples",
            14: "see-also",
        }

        extra = {}

        for index, category in response_parts_name_mapping.items():
            extra[category] = (
                data[index] if (index < len(data) and data[index]) else None
            )

        return extra

    @typing.overload
    async def translate(
        self, text: str, dest: str = ..., src: str = ..., **kwargs: typing.Any
    ) -> Translated: ...

    @typing.overload
    async def translate(
        self,
        text: typing.List[str],
        dest: str = ...,
        src: str = ...,
        **kwargs: typing.Any,
    ) -> typing.List[Translated]: ...

    async def translate(
        self,
        text: typing.Union[str, typing.List[str]],
        dest: str = "en",
        src: str = "auto",
        **kwargs: typing.Any,
    ) -> typing.Union[Translated, typing.List[Translated]]:
        """Translate text from source language to destination language

        :param text: The source text(s) to be translated. Batch translation is supported via sequence input.
        :type text: UTF-8 :class:`str`; :class:`unicode`; string sequence (list, tuple, iterator, generator)

        :param dest: The language to translate the source text into.
                     The value should be one of the language codes listed in :const:`googletrans.LANGUAGES`
                     or one of the language names listed in :const:`googletrans.LANGCODES`.
        :param dest: :class:`str`; :class:`unicode`

        :param src: The language of the source text.
                    The value should be one of the language codes listed in :const:`googletrans.LANGUAGES`
                    or one of the language names listed in :const:`googletrans.LANGCODES`.
                    If a language is not specified,
                    the system will attempt to identify the source language automatically.
        :param src: :class:`str`; :class:`unicode`

        :rtype: Translated
        :rtype: :class:`list` (when a list is passed)

        Basic usage:
            >>> from googletrans import Translator
            >>> translator = Translator()
            >>> translator.translate('안녕하세요.')
            <Translated src=ko dest=en text=Good evening. pronunciation=Good evening.>
            >>> translator.translate('안녕하세요.', dest='ja')
            <Translated src=ko dest=ja text=こんにちは。 pronunciation=Kon'nichiwa.>
            >>> translator.translate('veritas lux mea', src='la')
            <Translated src=la dest=en text=The truth is my light pronunciation=The truth is my light>

        Advanced usage:
            >>> translations = translator.translate(['The quick brown fox', 'jumps over', 'the lazy dog'], dest='ko')
            >>> for translation in translations:
            ...    print(translation.origin, ' -> ', translation.text)
            The quick brown fox  ->  빠른 갈색 여우
            jumps over  ->  이상 점프
            the lazy dog  ->  게으른 개
        """
        dest = _normalize_lang(dest)
        src = _normalize_lang(src)

        if src != "auto" and src not in LANGUAGES:
            if src in SPECIAL_CASES:
                src = SPECIAL_CASES[src]
            elif src in LANGCODES:
                src = LANGCODES[src]
            else:
                raise ValueError("invalid source language")

        if dest not in LANGUAGES:
            if dest in SPECIAL_CASES:
                dest = SPECIAL_CASES[dest]
            elif dest in LANGCODES:
                dest = LANGCODES[dest]
            else:
                raise ValueError("invalid destination language")

        if isinstance(text, list):
            concurrency_limit = kwargs.pop(
                "list_operation_max_concurrency", self.list_operation_max_concurrency
            )
            semaphore = asyncio.Semaphore(concurrency_limit)

            async def translate_with_semaphore(item):
                async with semaphore:
                    return await self.translate(item, dest=dest, src=src, **kwargs)

            tasks = [translate_with_semaphore(item) for item in text]
            result = await asyncio.gather(*tasks)
            return result

        origin = text
        data, response = await self._translate(text, dest, src, kwargs)

        # this code will be updated when the format is changed.
        translated = "".join([d[0] if d[0] else "" for d in data[0]])

        extra_data = self._parse_extra_data(data)

        # actual source language that will be recognized by Google Translator when the
        # src passed is equal to auto.
        detected_src = None
        try:
            detected_src = data[2]
        except Exception:  # pragma: nocover
            pass

        # Fallback for Traditional Chinese and ambiguous detections
        if (not detected_src or detected_src == dest) and len(data) > 0 and data[0] and len(data[0][0]) > 8:
            try:
                models = data[0][0][8]
                if models and isinstance(models, list):
                    first = models[0]
                    while isinstance(first, list) and len(first) > 0 and isinstance(first[0], list):
                        first = first[0]
                    if isinstance(first, list) and len(first) >= 2 and isinstance(first[1], str) and "_" in first[1]:
                        model_src = first[1].split("_")[0]
                        if model_src:
                            detected_src = model_src
            except Exception:  # pragma: nocover
                pass

        if detected_src:
            src = detected_src

        pron = origin
        try:
            pron = data[0][1][-2]
        except Exception:  # pragma: nocover
            pass

        if pron is None:
            try:
                pron = data[0][1][2]
            except:  # pragma: nocover  # noqa: E722
                pass

        if dest in EXCLUDES and pron == origin:
            pron = translated

        # put final values into a new Translated object
        result = Translated(
            src=src,
            dest=dest,
            origin=origin,
            text=translated,
            pronunciation=pron,
            extra_data=extra_data,
            response=response,
        )

        return result

    @typing.overload
    async def detect(self, text: str, **kwargs: typing.Any) -> Detected: ...

    @typing.overload
    async def detect(
        self, text: typing.List[str], **kwargs: typing.Any
    ) -> typing.List[Detected]: ...

    async def detect(
        self, text: typing.Union[str, typing.List[str]], **kwargs: typing.Any
    ) -> typing.Union[Detected, typing.List[Detected]]:
        """Detect language of the input text

        :param text: The source text(s) whose language you want to identify.
                     Batch detection is supported via sequence input.
        :type text: UTF-8 :class:`str`; :class:`unicode`; string sequence (list, tuple, iterator, generator)

        :rtype: Detected
        :rtype: :class:`list` (when a list is passed)

        Basic usage:
            >>> from googletrans import Translator
            >>> translator = Translator()
            >>> translator.detect('이 문장은 한글로 쓰여졌습니다.')
            <Detected lang=ko confidence=0.27041003>
            >>> translator.detect('この文章は日本語で書かれました。')
            <Detected lang=ja confidence=0.64889508>
            >>> translator.detect('This sentence is written in English.')
            <Detected lang=en confidence=0.22348526>
            >>> translator.detect('Tiu frazo estas skribita en Esperanto.')
            <Detected lang=eo confidence=0.10538048>

        Advanced usage:
            >>> langs = translator.detect(['한국어', '日本語', 'English', 'le français'])
            >>> for lang in langs:
            ...    print(lang.lang, lang.confidence)
            ko 1
            ja 0.92929292
            en 0.96954316
            fr 0.043500196
        """
        if isinstance(text, list):
            concurrency_limit = kwargs.pop(
                "list_operation_max_concurrency", self.list_operation_max_concurrency
            )
            semaphore = asyncio.Semaphore(concurrency_limit)

            async def detect_with_semaphore(item):
                async with semaphore:
                    return await self.detect(item, **kwargs)

            tasks = [detect_with_semaphore(item) for item in text]
            result = await asyncio.gather(*tasks)
            return result

        data, response = await self._translate(text, "en", "auto", kwargs)

        # actual source language that will be recognized by Google Translator when the
        # src passed is equal to auto.
        src = ""
        confidence = 0.0
        try:
            if len(data[8][0]) > 1:
                src = data[8][0]
                confidence = data[8][-2]
            else:
                src = "".join(data[8][0])
                confidence = data[8][-2][0]
        except Exception:  # pragma: nocover
            pass

        # Fallback if detect returned destination ('en') or empty for CJK/other characters
        if (not src or src == "en") and len(data) > 0 and data[0] and len(data[0][0]) > 8:
            try:
                models = data[0][0][8]
                if models and isinstance(models, list):
                    first = models[0]
                    while isinstance(first, list) and len(first) > 0 and isinstance(first[0], list):
                        first = first[0]
                    if isinstance(first, list) and len(first) >= 2 and isinstance(first[1], str) and "_" in first[1]:
                        model_src = first[1].split("_")[0]
                        if model_src and model_src != "en":
                            src = model_src
                            confidence = 1.0
            except Exception:  # pragma: nocover
                pass

        result = Detected(lang=src, confidence=confidence, response=response)

        return result

    def translate_sync(
        self,
        text: typing.Union[str, typing.List[str]],
        dest: str = "en",
        src: str = "auto",
        **kwargs: typing.Any,
    ) -> typing.Union[Translated, typing.List[Translated]]:
        """Synchronously translate text without manually creating an event loop."""
        with SyncTranslator(
            service_urls=self.service_urls,
            raise_exception=self.raise_exception,
            list_operation_max_concurrency=self.list_operation_max_concurrency,
            transport=self.transport,
            impersonate=self.impersonate,
        ) as sync_trans:
            return sync_trans.translate(text, dest=dest, src=src, **kwargs)

    def detect_sync(
        self,
        text: typing.Union[str, typing.List[str]],
        **kwargs: typing.Any,
    ) -> typing.Union[Detected, typing.List[Detected]]:
        """Synchronously detect text language without manually creating an event loop."""
        with SyncTranslator(
            service_urls=self.service_urls,
            raise_exception=self.raise_exception,
            list_operation_max_concurrency=self.list_operation_max_concurrency,
            transport=self.transport,
            impersonate=self.impersonate,
        ) as sync_trans:
            return sync_trans.detect(text, **kwargs)


class SyncTranslator:
    """Synchronous drop-in translator wrapper for blocking workflows."""

    def __init__(
        self,
        service_urls: typing.Sequence[str] = DEFAULT_CLIENT_SERVICE_URLS,
        user_agent: str = DEFAULT_USER_AGENT,
        raise_exception: bool = DEFAULT_RAISE_EXCEPTION,
        proxy: typing.Optional[ProxyTypes] = None,
        timeout: typing.Optional[Timeout] = None,
        http2: bool = True,
        list_operation_max_concurrency: int = 2,
        transport: typing.Literal["auto", "curl", "httpx"] = "auto",
        impersonate: str = "chrome",
    ):
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._loop.run_forever, daemon=True)
        self._thread.start()

        async def _init_client():
            return Translator(
                service_urls=service_urls,
                user_agent=user_agent,
                raise_exception=raise_exception,
                proxy=proxy,
                timeout=timeout,
                http2=http2,
                transport=transport,
                impersonate=impersonate,
                list_operation_max_concurrency=list_operation_max_concurrency,
            )

        future = asyncio.run_coroutine_threadsafe(_init_client(), self._loop)
        self._async_translator = future.result()

    def _run_coroutine(self, coro: typing.Coroutine) -> typing.Any:
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result()

    def translate(
        self,
        text: typing.Union[str, typing.List[str]],
        dest: str = "en",
        src: str = "auto",
        **kwargs: typing.Any,
    ) -> typing.Union[Translated, typing.List[Translated]]:
        """Synchronously translate text from source language to destination language."""
        return self._run_coroutine(
            self._async_translator.translate(text, dest=dest, src=src, **kwargs)
        )

    def detect(
        self,
        text: typing.Union[str, typing.List[str]],
        **kwargs: typing.Any,
    ) -> typing.Union[Detected, typing.List[Detected]]:
        """Synchronously detect language of the input text."""
        return self._run_coroutine(
            self._async_translator.detect(text, **kwargs)
        )

    def close(self):
        """Close the underlying client session and persistent event loop."""
        if hasattr(self, "_loop") and self._loop.is_running():
            try:
                future = asyncio.run_coroutine_threadsafe(
                    self._async_translator.aclose(), self._loop
                )
                future.result(timeout=2.0)
            except Exception:
                pass
            finally:
                self._loop.call_soon_threadsafe(self._loop.stop)
                if hasattr(self, "_thread") and self._thread.is_alive():
                    self._thread.join(timeout=2.0)
                try:
                    self._loop.close()
                except Exception:
                    pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass
