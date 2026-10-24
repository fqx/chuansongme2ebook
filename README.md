# chuansongme to ebook
A python script to convert chuansongme.com (wechat official accounts mirror) to ebook.

Use kindlegen or calibre to pack package.opf to ebook.

## Runtime and installation

Use Python 3.11 or newer. Pillow 13.0.0 raises the minimum Python version
from 3.10 to 3.11 and fixes GHSA-65qm-jvmh-6pqg / CVE-2026-112400.

```sh
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python main.py
```

The separate `lxml_html_clean` package is required for `lxml.html.clean.Cleaner`.
Its pinned version 0.4.5 requires lxml 6.1.1 or newer. Cleaner is used to simplify
article HTML; it should not be treated as a security boundary for arbitrary
untrusted HTML.

## Offline compatibility tests

```sh
.venv/bin/python -m pip check
.venv/bin/python -m unittest discover -s tests -v
```

Tests use a loopback HTTP server and tiny in-memory HTML/PNG fixtures, with
external destinations rejected. They cover account/article parsing, ordinary
chunked Deflate responses, redirects, missing articles, date filtering, image
saving (PNG/JPEG/GIF), integer-image conversion to 16-bit PNG, invalid-image
skipping, ebook file generation, and SoupSieve selector boundaries. No external
article/image requests or resource-exhaustion payloads are used. Ebook file
creation is checked; Kindle/Calibre conversion and formal ebook validation are
not covered.
