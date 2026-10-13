# Dependency update verification

Base: fqx/chuansongme2ebook master at
`36649a9f3add35ccf8a1466ba670c9e0fb286ba4`.

## Changes

- urllib3 2.7.0 → 2.8.0: fixes response-stream/chunk parsing and other security issues.
- SoupSieve 2.8.4 → 2.9: incorporates the dependency change in existing PR #38.
- Add lxml_html_clean 0.4.5 and update lxml 6.1.0 → 6.1.1: necessary compatibility
  repair, because the baseline imports `lxml.html.clean.Cleaner` without installing
  its now-separate package. Cleaner 0.4.5 requires lxml >=6.1.1 for its security fix.
- Document Python >=3.10, already required by baseline Pillow, requests and urllib3.
- Add five offline compatibility tests. No application source changes.

## Findings and commands

Baseline `python -m venv .venv` followed by
`.venv/bin/python -m pip install --index-url https://pypi.org/simple -r requirements.txt`
succeeded on Python 3.12.14. Baseline `.venv/bin/python -c 'import main'` failed with
`ImportError: lxml.html.clean module is now a separate project lxml_html_clean`.

An intermediate attempt to install lxml_html_clean 0.4.5 alongside lxml 6.1.0
correctly failed dependency resolution. Updating lxml to its minimum required
6.1.1 resolved this, without selecting the older cleaner release.

Final Python 3.12.14 verification:

```sh
.venv/bin/python -m pip install --index-url https://pypi.org/simple -r requirements.txt
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m pip check
```

All five tests pass; no broken requirements.

Final Python 3.13.5 verification, clean isolated environment:

```sh
UV_CACHE_DIR=$PWD/.uv-cache uv venv --python /usr/bin/python3.13 .venv313
UV_CACHE_DIR=$PWD/.uv-cache uv pip install --python .venv313/bin/python --index-url https://pypi.org/simple -r requirements.txt
.venv313/bin/python -m unittest discover -s tests -v
UV_CACHE_DIR=$PWD/.uv-cache uv pip check --python .venv313/bin/python
```

All five tests pass; all installed packages are compatible.

Final Python 3.10.22 minimum-runtime verification, clean isolated environment:

```sh
UV_CACHE_DIR=$PWD/.uv-cache UV_PYTHON_INSTALL_DIR=$PWD/.python uv python install 3.10
UV_CACHE_DIR=$PWD/.uv-cache UV_PYTHON_INSTALL_DIR=$PWD/.python uv venv --python 3.10 .venv310
UV_CACHE_DIR=$PWD/.uv-cache uv pip install --python .venv310/bin/python --index-url https://pypi.org/simple -r requirements.txt
.venv310/bin/python -m unittest discover -s tests -v
UV_CACHE_DIR=$PWD/.uv-cache uv pip check --python .venv310/bin/python
```

All five tests pass; all installed packages are compatible. uv installed the
interpreter into the repository-local .python directory. Its attempt to add a
convenience executable link under the read-only home failed; using the local
interpreter/venv worked normally.

The resolved transitive dependency was charset-normalizer 3.5.2 in all three
Python environments. All other final versions are pinned in requirements.txt.

## Scope and limitations

- Tests use actual requests.Session and urllib3 transport against a loopback-only
  server, including small chunked Deflate HTML and PNG decoding with Pillow.
- No production site access, external application requests, exploit stress tests,
  TLS/proxy handshake validation, or Kindle/Calibre conversion was performed.
- File creation/content assertions do not establish EPUB/OPF conformance. Existing
  packaging quirks and unrelated image-cache behavior were not changed.
- Existing `is ''` SyntaxWarning and BeautifulSoup lxml `strip_cdata` deprecation
  remain. No claim of complete application/security audit is made.
- No prior test suite or CI configuration was present. No remote writes were made.

## Sources

- https://github.com/fqx/chuansongme2ebook/pull/38
- https://urllib3.readthedocs.io/en/stable/changelog.html (2.8.0 section)
- https://facelessuser.github.io/soupsieve/about/changelog/
- https://lxml-html-clean.readthedocs.io/en/latest/changes.html
- PyPI wheel metadata for installed dependency/runtime requirements.
