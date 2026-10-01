# Security policy

## Supported versions

Security fixes are released for the latest minor version of sambat. Please
upgrade to the latest release before reporting an issue.

## Reporting a vulnerability

**Do not open a public issue for security problems.**

Report vulnerabilities privately through GitHub's
[private vulnerability reporting](https://github.com/rjach/sambat/security/advisories/new).
Include a description of the issue, the affected versions, and a minimal
reproduction if possible.

You can expect an acknowledgement within 7 days. Once the issue is confirmed,
a fix will be prepared privately, released, and announced in a GitHub
security advisory that credits you (unless you prefer otherwise).

## Scope

sambat is a pure-Python library with no runtime dependencies that performs no
network or file-system access at runtime. Relevant reports include, for
example, inputs that cause excessive CPU or memory use in parsing
(`strptime`, `fromisoformat`), or problems in the release and supply chain
(GitHub Actions workflows, published artifacts).

Incorrect calendar conversions are bugs, not vulnerabilities: please report
them with the calendar discrepancy issue form.

## Release integrity

Releases are built and published by GitHub Actions using PyPI Trusted
Publishing. Every distribution on PyPI carries a PEP 740 attestation, and
build provenance is attached to each GitHub release. You can verify a
download with:

```console
gh attestation verify sambat-<version>-py3-none-any.whl --repo rjach/sambat
```
