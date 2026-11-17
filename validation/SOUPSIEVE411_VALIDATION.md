# SoupSieve 4.1.1 compatibility verification

Date: 2026-11-17. Base: remote master
`99d924b542173695c30e8baaa99a0f23bbabb67e`.

## Change

- SoupSieve 2.9 -> 4.1.1; BeautifulSoup remains pinned to 4.7.1.
- Document Python >=3.11.5, matching the new wheel's Requires-Python metadata.
- All other dependency pins and application source remain unchanged.
- Add three tests for selector API/cache behavior, bounded descendant matching,
  and the interactive CLI entry point.

The original workspace checkout was stale and contained uncommitted changes.
It was left untouched; this update uses a separate clone of current master,
including its existing certifi 2026.10.23 and Pillow 13.0.0 updates.
No AGENTS.md or CI configuration was present in the current checkout.

## Results

| Runtime | SoupSieve | Tests | pip check |
| --- | --- | --- | --- |
| Python 3.12.14 baseline | 2.9 | Existing 8/8 pass | No broken requirements |
| Python 3.11.5 (exact new minimum) | 4.1.1 | 11/11 pass | No broken requirements |
| Python 3.12.14 (upgraded baseline environment) | 4.1.1 | 11/11 pass | No broken requirements |
| Python 3.13.5 (clean environment) | 4.1.1 | 11/11 pass | No broken requirements |

Python 3.11.5 used a clean uv-managed interpreter/virtualenv. Python 3.12 used
`python -m venv .venv312`; Python 3.13 used `/usr/bin/python3.13`.
Installed versions, including transitive dependencies and tooling, are recorded
in `soupsieve411-versions.json`.

For each final environment (replace ENV with .venv311, .venv312 or .venv313):

```sh
ENV/bin/python -m pip install --index-url https://pypi.org/simple -r requirements.txt
ENV/bin/python -m unittest discover -s tests -v
ENV/bin/python -m pip check
```

All tests use tiny fixtures and loopback HTTP. Coverage includes article/account
parsing, chunked Deflate, redirects, date filtering, missing articles,
PNG/JPEG/GIF decoding, integer image conversion, invalid-image handling, and
HTML/OPF/NCX generation. The CLI test executes main.py with runpy as __main__,
supplies the normal account URL prompt, and redirects only the production host
to the guarded loopback fixture server. It checks saved article text and images.
Only input, delays, output capture and transport destination are adapted.

Selector checks exercise BeautifulSoup select/select_one/limit, compiled
SoupSieve select/match, invalid syntax, nth-child boundaries, and repeated
selection after moving/removing nodes. The descendant fixture is 12 levels deep.

## Security and limits

4.1.1 exceeds the reported four advisories' highest 4.0 repair threshold.
It also includes the later nested nth-selector fix GHSA-98qm-p6jx-5wj2, for
which upstream specifically requires 4.1.1. The project currently uses find,
find_all and tag lookup rather than CSS selectors in production code.

No production site traffic, exploit stress tests, TLS/proxy verification,
Kindle/Calibre conversion or formal EPUB/OPF conformance checks were performed.
Existing main.py `is ''` SyntaxWarning and BeautifulSoup/lxml strip_cdata
DeprecationWarning remain; neither caused a test failure. This is a dependency
compatibility verification, not a complete security audit.

Sources:
- https://pypi.org/pypi/soupsieve/4.1.1/json
- https://facelessuser.github.io/soupsieve/about/changelog/
- https://github.com/facelessuser/soupsieve/security/advisories/GHSA-mmhr-3c5m-f64f
- https://github.com/facelessuser/soupsieve/security/advisories/GHSA-98qm-p6jx-5wj2
