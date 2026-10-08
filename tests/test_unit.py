import json
from unittest.mock import AsyncMock, patch

import pytest

from googletrans import Translator
from googletrans.cli import _run_cli


@pytest.mark.asyncio
async def test_translator_init_transport_default():
    translator = Translator()
    assert translator.transport == "curl"
    assert translator.impersonate == "chrome"
    await translator.aclose()


@pytest.mark.asyncio
async def test_translator_init_transport_curl():
    translator = Translator(transport="curl", impersonate="safari")
    assert translator.transport == "curl"
    assert translator.impersonate == "safari"
    await translator.aclose()


@pytest.mark.asyncio
async def test_translator_init_transport_httpx():
    translator = Translator(transport="httpx")
    assert translator.transport == "httpx"
    await translator.aclose()


def test_translator_init_invalid_transport():
    with pytest.raises(ValueError, match="Invalid transport"):
        Translator(transport="invalid")


@pytest.mark.asyncio
async def test_mocked_translate_response():
    translator = Translator(transport="httpx")

    mock_body = json.dumps([
        [["안녕하세요", "hello", None, None, 1]],
        None,
        "en",
    ])

    class MockResponse:
        status_code = 200
        text = mock_body

    with patch.object(translator.client, "get", new=AsyncMock(return_value=MockResponse())):
        result = await translator.translate("hello", dest="ko", src="en")
        assert result.text == "안녕하세요"
        assert result.src == "en"
        assert result.dest == "ko"
        assert result.origin == "hello"

    await translator.aclose()


@pytest.mark.asyncio
async def test_mocked_detect_response():
    translator = Translator(transport="httpx")

    detect_data = [None] * 9
    detect_data[8] = [["ko"], None, None, None, None, None, [0.98], None]
    mock_body = json.dumps(detect_data)

    class MockResponse:
        status_code = 200
        text = mock_body

    with patch.object(translator.client, "get", new=AsyncMock(return_value=MockResponse())):
        result = await translator.detect("안녕하세요")
        assert result.lang == "ko"
        assert result.confidence == 0.98

    await translator.aclose()


@pytest.mark.asyncio
async def test_cli_execution_translate(capsys):
    import argparse

    args = argparse.Namespace(
        text="hello",
        dest="ko",
        src="en",
        detect=False,
    )

    mock_body = json.dumps([
        [["안녕하세요", "hello", None, None, 1]],
        None,
        "en",
    ])

    class MockResponse:
        status_code = 200
        text = mock_body

    with patch("googletrans.client.AsyncSession.get", new=AsyncMock(return_value=MockResponse())):
        await _run_cli(args)

    captured = capsys.readouterr()
    assert "안녕하세요" in captured.out
    assert "[en] hello" in captured.out
    assert "[ko] 안녕하세요" in captured.out


@pytest.mark.asyncio
async def test_cli_execution_detect(capsys):
    import argparse

    args = argparse.Namespace(
        text="안녕하세요",
        dest="en",
        src="auto",
        detect=True,
    )

    detect_data = [None] * 9
    detect_data[8] = [["ko"], None, None, None, None, None, [0.99], None]
    mock_body = json.dumps(detect_data)

    class MockResponse:
        status_code = 200
        text = mock_body

    with patch("googletrans.client.AsyncSession.get", new=AsyncMock(return_value=MockResponse())):
        await _run_cli(args)

    captured = capsys.readouterr()
    assert "[ko," in captured.out
    assert "안녕하세요" in captured.out


def test_language_codes_and_aliases():
    from googletrans.constants import LANGCODES, LANGUAGES

    # Modern ISO 639-1 additions
    assert LANGUAGES["ab"] == "abkhaz"
    assert LANGUAGES["aa"] == "afar"
    assert LANGUAGES["ba"] == "bashkir"
    assert LANGUAGES["br"] == "breton"
    assert LANGUAGES["ee"] == "ewe"
    assert LANGUAGES["et"] == "estonian"
    assert LANGCODES["ewe"] == "ee"
    assert LANGCODES["estonian"] == "et"

    # Backward-compatible legacy 3-letter aliases
    assert LANGUAGES["abk"] == "abkhaz"
    assert LANGUAGES["aar"] == "afar"
    assert LANGUAGES["bak"] == "bashkir"
    assert LANGUAGES["bre"] == "breton"
    assert LANGUAGES["fao"] == "faroese"
    assert LANGUAGES["fo"] == "faroese"

    # Regional / script variants
    assert LANGUAGES["zh-cn"] == "chinese (simplified)"
    assert LANGUAGES["zh-tw"] == "chinese (traditional)"
    assert LANGUAGES["crh-latn"] == "crimean tatar (latin)"
    assert LANGUAGES["sat-latn"] == "santali (latin)"


def test_language_normalization_in_client():
    from googletrans.client import _normalize_lang

    assert _normalize_lang("zh_cn") == "zh-cn"
    assert _normalize_lang("zh_tw") == "zh-tw"
    assert _normalize_lang("en_US") == "en"
    assert _normalize_lang("it_CH@euro") == "it"
    assert _normalize_lang("KO") == "ko"
    assert _normalize_lang("unknown_xyz") == "unknown_xyz"


def test_sync_translator_translate_and_detect():
    from googletrans import SyncTranslator

    mock_trans_body = json.dumps([
        [["Bonjour", "Hello", None, None, 1]],
        None,
        "en",
    ])
    detect_data = [None] * 9
    detect_data[8] = [["fr"], None, None, None, None, None, [0.95], None]
    mock_detect_body = json.dumps(detect_data)

    class MockResponse:
        def __init__(self, text):
            self.status_code = 200
            self.text = text

    with SyncTranslator(transport="httpx") as translator:
        with patch.object(
            translator._async_translator.client,
            "get",
            new=AsyncMock(return_value=MockResponse(mock_trans_body)),
        ):
            res = translator.translate("Hello", dest="fr", src="en")
            assert res.text == "Bonjour"
            assert res.src == "en"
            assert res.dest == "fr"

        with patch.object(
            translator._async_translator.client,
            "get",
            new=AsyncMock(return_value=MockResponse(mock_detect_body)),
        ):
            det = translator.detect("Bonjour")
            assert det.lang == "fr"
            assert det.confidence == 0.95


@pytest.mark.asyncio
async def test_translator_sync_convenience_methods():
    translator = Translator(transport="curl")

    mock_trans_body = json.dumps([
        [["Bonjour", "Hello", None, None, 1]],
        None,
        "en",
    ])

    class MockResponse:
        status_code = 200
        text = mock_trans_body

    with patch("googletrans.client.AsyncSession.get", new=AsyncMock(return_value=MockResponse())):
        res = translator.translate_sync("Hello", dest="fr", src="en")
        assert res.text == "Bonjour"

    await translator.aclose()


@pytest.mark.asyncio
async def test_error_diagnostics_rate_limit_429():
    from googletrans.constants import RateLimitError

    translator = Translator(transport="httpx", raise_exception=True)

    class MockResponse429:
        status_code = 429
        text = "Too Many Requests"

    with patch.object(translator.client, "get", new=AsyncMock(return_value=MockResponse429())):
        with pytest.raises(RateLimitError) as exc_info:
            await translator.translate("Hello", dest="ko")
        assert exc_info.value.status_code == 429
        assert "rate limit reached (HTTP 429)" in str(exc_info.value)

    await translator.aclose()


@pytest.mark.asyncio
async def test_error_diagnostics_general_non_200():
    from googletrans.constants import TranslationError

    translator = Translator(transport="httpx", raise_exception=True)

    class MockResponse403:
        status_code = 403
        text = "Forbidden access"

    with patch.object(translator.client, "get", new=AsyncMock(return_value=MockResponse403())):
        with pytest.raises(TranslationError) as exc_info:
            await translator.translate("Hello", dest="ko")
        assert exc_info.value.status_code == 403
        assert 'Unexpected status code "403"' in str(exc_info.value)

    await translator.aclose()


@pytest.mark.asyncio
async def test_error_silent_fallback_when_raise_exception_false(caplog):
    import logging

    translator = Translator(transport="httpx", raise_exception=False)

    class MockResponse500:
        status_code = 500
        text = "Server error"

    with patch.object(translator.client, "get", new=AsyncMock(return_value=MockResponse500())):
        with caplog.at_level(logging.WARNING, logger="googletrans"):
            res = await translator.translate("fallback text", dest="ko")
            assert res.text == "fallback text"
            assert "Google Translate returned HTTP 500" in caplog.text

    await translator.aclose()


@pytest.mark.asyncio
async def test_fallback_detection_from_neural_model():
    """Verify fallback detection when data[2] echoes dest or is ambiguous but neural model has source."""
    translator = Translator(transport="httpx")

    raw_data = [
        [[
            "I want to check if it is working properly.",
            "我想檢查一下它是否正常運作。",
            None,
            None,
            11,
            None,
            None,
            [[]],
            [[["af64405095a399ceb1e05c7abb7cda66", "zh_en_2023q1.md"]]],
        ]],
        None,
        "en",  # data[2] erroneously echoes dest ('en')
        None,
        None,
        None,
        1,
        [],
        [["en"], None, [1], ["en"]],  # data[8] also echoed 'en'
    ]

    class MockResponse:
        status_code = 200
        text = json.dumps(raw_data)

    with patch.object(translator.client, "get", new=AsyncMock(return_value=MockResponse())):
        res = await translator.translate("我想檢查一下它是否正常運作。", dest="en", src="auto")
        assert res.src == "zh"
        assert res.text == "I want to check if it is working properly."

        det = await translator.detect("我想檢查一下它是否正常運作。")
        assert det.lang == "zh"

    await translator.aclose()


@pytest.mark.asyncio
async def test_backticks_text_translation():
    """Verify text containing backticks formats without error (Issue #448)."""
    translator = Translator(transport="httpx")

    text_input = "How `this` works in JavaScript"
    mock_body = json.dumps([
        [["JavaScript 中的“this”是如何工作的", text_input, None, None, 1]],
        None,
        "en",
    ])

    class MockResponse:
        status_code = 200
        text = mock_body

    with patch.object(translator.client, "get", new=AsyncMock(return_value=MockResponse())):
        res = await translator.translate(text_input, dest="zh-cn", src="en")
        assert res.text == "JavaScript 中的“this”是如何工作的"
        assert res.src == "en"

    await translator.aclose()
