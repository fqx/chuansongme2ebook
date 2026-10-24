# Pillow 13 security compatibility validation

Validated entirely in an isolated Linux cloud container on 2026-10-24, based on
`15f9332d8aa91415e4f0bbf59c546f58eb75cc95` (master). No user Mac resources,
production requests, deployment, or high-resource exploit reproduction were used.

## Change and official sources

- Pin Pillow 13.0.0, the fixed release for
  [GHSA-65qm-jvmh-6pqg / CVE-2026-112400](https://github.com/advisories/GHSA-65qm-jvmh-6pqg).
  The advisory is **High**, and describes continued use after a rejected GIF
  frame seek. The repository does not contain that specific caught-error/retry
  path; this is not evidence that other vulnerabilities are inapplicable.
- [PyPI metadata](https://pypi.org/pypi/Pillow/13.0.0/json) requires Python >=3.11.
  Update the prior Python >=3.10 documentation accordingly.
- Pillow 13 rejects direct `I`-mode PNG saving. Explicitly convert integer images
  to `I;16`, retaining the previous clipping of negative and >65535 values.
  Regression input is a tiny four-pixel TIFF, not a resource-exhaustion payload.

## Completed checks

Two separate clean virtual environments installed the complete requirements
with dependency resolution from https://pypi.org/simple; no `--no-deps` was used.

| Interpreter | Existing + added tests | Dependency check | Import |
| --- | --- | --- | --- |
| CPython 3.12.14 | 8 passed | `pip check`: no broken requirements | `main`, Pillow 13.0.0 |
| CPython 3.11.17 | 8 passed | `uv pip check`: all packages compatible | `main`, Pillow 13.0.0 |

Commands (substitute the environment's interpreter):

```sh
python -m pip install --index-url https://pypi.org/simple -r requirements.txt
python -m pip check
python -m unittest discover -s tests -v
python -c 'import main; import PIL; print(PIL.__version__)'
```

The eight tests cover article parsing, ebook files, chunked Deflate responses,
redirects, HTTP failures, date filtering, selector boundaries, tiny PNG/JPEG/GIF
conversion to PNG, invalid-image skipping, and integer-image PNG compatibility.
HTTP fixtures use loopback only and reject external destinations. Image-only
fixtures mock the response bytes. Resolved versions are in
`pillow13-versions.json`; detailed run logs are retained in the cloud workspace
under `/workspace/pillow-security/evidence/`.

## Limits

Kindle/Calibre packaging, live third-party pages, animated multi-frame export,
and Python versions beyond the two listed above were not exercised.
Dependabot alerts #98 and #89 could not be read: the GitHub connector rejects the
Dependabot alert endpoint as unsupported. Their reported Critical identities
remain unverified and are not conflated with this High GIF advisory.
No claim is made that unrelated alerts are resolved. No deployment was performed.
