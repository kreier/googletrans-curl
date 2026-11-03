"""Free Google Translate API for Python. Translates totally free of charge."""

__all__ = (
    "Translator",
    "SyncTranslator",
    "LANGUAGES",
    "LANGCODES",
    "TranslationError",
    "RateLimitError",
    "CurlOpt",
)
__version__ = "4.1.1"


from googletrans.client import SyncTranslator, Translator
from googletrans.constants import (
    LANGCODES,
    LANGUAGES,
    RateLimitError,
    TranslationError,
)

try:
    from curl_cffi import CurlOpt
except ImportError:  # pragma: no cover
    CurlOpt = None
