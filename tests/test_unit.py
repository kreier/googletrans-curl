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
