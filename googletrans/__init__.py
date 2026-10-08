"""Free Google Translate API for Python. Translates totally free of charge."""

__all__ = (
    "Translator",
    "SyncTranslator",
    "LANGUAGES",
    "LANGCODES",
    "TranslationError",
    "RateLimitError",
)
__version__ = "4.1.0"


from googletrans.client import SyncTranslator, Translator
from googletrans.constants import (
    LANGCODES,
    LANGUAGES,
    RateLimitError,
    TranslationError,
)
