===============================================================
Googletrans-curl: Free and Unlimited Google Translate API for Python
===============================================================

.. image:: https://img.shields.io/pypi/v/googletrans-curl.svg
   :target: https://pypi.org/project/googletrans-curl/
.. image:: https://img.shields.io/badge/License-MIT-yellow.svg
   :target: https://opensource.org/licenses/MIT
.. image:: https://img.shields.io/badge/python-3.8%2B-blue.svg
   :target: https://www.python.org/

Googletrans-curl is a fast, drop-in replacement fork of `googletrans <https://github.com/ssut/py-googletrans>`_
that integrates `curl-cffi <https://github.com/lexiforest/curl_cffi>`_ to eliminate Google Translate
**HTTP 429 Too Many Requests** and rate-limiting blocks via browser TLS fingerprint impersonation.

The package maintains full backward compatibility:
- Modern asynchronous API (compatible with googletrans v4.x).
- Synchronous drop-in wrapper (compatible with googletrans v3.x legacy scripts).

--------
Features
--------

- Fast and reliable - uses Google Translate endpoints with browser impersonation
- Auto language detection and confidence scoring
- Bulk translations (translate multiple strings in one call)
- Anti-429 protection using ``curl-cffi`` (default: Chrome TLS fingerprint)
- Pluggable transports: ``curl`` (default) and standard ``httpx``
- Async-first architecture with synchronous fallback (``SyncTranslator``)
- Customizable service URLs (e.g. ``translate.google.com``, ``translate.googleapis.com``)

~~~~~~~~~~~~~~~~~~~~~
Note on library usage
~~~~~~~~~~~~~~~~~~~~~

- The maximum character limit on a single text is ~15k characters.
- Due to limitations of the web version of google translate, this API does not guarantee that the library would work properly at all times.
- If you want to use a stable API with guaranteed SLAs, consider using `Google Cloud Translation API <https://cloud.google.com/translate/docs>`__.

----------
Quickstart
----------

Install the drop-in replacement from PyPI:

.. sourcecode:: bash

   $ pip install googletrans-curl

Existing code continues using the same import namespace: ``googletrans``.

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Drop-in Replacement for Legacy Synchronous Code (v3.x Migration)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Upstream ``googletrans`` v4 broke backwards compatibility by converting ``Translator.translate()``
into an ``async`` coroutine.

In ``googletrans-curl``, legacy synchronous codebases can continue running with **just a single change to the import line**:

.. code-block:: python

   # Replace: from googletrans import Translator
   from googletrans import SyncTranslator as Translator

   # Existing synchronous code works without any further changes:
   translator = Translator()
   result = translator.translate('안녕하세요.', dest='en')
   print(result.text)  # Good evening / Hello.

   detected = translator.detect('Bonjour tout le monde')
   print(detected.lang)  # fr

You can also use the synchronous context manager:

.. code-block:: python

   from googletrans import SyncTranslator

   with SyncTranslator() as translator:
       result = translator.translate('안녕하세요.', dest='en')
       print(result.text)

~~~~~~~~~~~~~~~~~~~~~~~~~
Asynchronous Usage (v4.x)
~~~~~~~~~~~~~~~~~~~~~~~~~

For modern async applications:

.. code-block:: python

   import asyncio
   from googletrans import Translator

   async def main():
       async with Translator() as translator:
           # Detect and translate to English (default)
           result = await translator.translate('안녕하세요.')
           print(result.text)

           # Translate to Japanese
           result = await translator.translate('안녕하세요.', dest='ja')
           print(result.text)

   asyncio.run(main())

~~~~~~~~~~~~~~~~~~~~~
Customize service URL
~~~~~~~~~~~~~~~~~~~~~

You can use another Google Translate domain for translation:

.. code-block:: python

   from googletrans import SyncTranslator as Translator

   translator = Translator(service_urls=[
       'translate.google.com',
       'translate.googleapis.com',
   ])

~~~~~~~~~~~~~~~~~~~~~
Advanced Usage (Bulk)
~~~~~~~~~~~~~~~~~~~~~

Translate a batch of strings in a single call:

.. code-block:: python

   from googletrans import SyncTranslator as Translator

   translator = Translator()
   translations = translator.translate(['The quick brown fox', 'jumps over', 'the lazy dog'], dest='ko')
   for translation in translations:
       print(translation.origin, ' -> ', translation.text)

~~~~~~~~~~~~~~~~~~
Language detection
~~~~~~~~~~~~~~~~~~

Detect the language of text with confidence scores:

.. code-block:: python

   from googletrans import SyncTranslator as Translator

   translator = Translator()
   detected = translator.detect('이 문장은 한글로 쓰여졌습니다.')
   print(detected.lang, detected.confidence)

---------
API Guide
---------

======================
googletrans.Translator
======================

.. autoclass:: googletrans.Translator
    :members:

==========================
googletrans.SyncTranslator
==========================

.. autoclass:: googletrans.SyncTranslator
    :members:

==================
googletrans.models
==================

.. automodule:: googletrans.models
    :members:

==================
googletrans.gtoken
==================

.. hint::

   This is for internal use only to generate a valid token to access
   translate.google.com ajax API.

.. automodule:: googletrans.gtoken
    :members:

=====================
googletrans.LANGUAGES
=====================

.. hint::

   iso639-1 language codes for
   `supported languages <https://developers.google.com/translate/v2/using_rest#language-params>`_
   for translation. Some language codes also include a country code, like zh-CN or zh-TW.

.. literalinclude:: ../googletrans/constants.py
   :language: python
   :lines: 70-182
   :linenos:

================================
googletrans.DEFAULT_SERVICE_URLS
================================

.. hint::

   `DEFAULT_SERVICE_URLS <https://github.com/ssut/py-googletrans/blob/master/googletrans/constants.py#L3:1>`_ is the list of current available Google Translation service urls.
   
   For using these service urls, please check `Customize service URL`_.