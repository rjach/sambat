# Governance

## Maintainers

| Maintainer | GitHub | Responsibilities |
|---|---|---|
| Rojan Acharya | [@rjach](https://github.com/rjach) | Lead maintainer, releases, calendar data |

The project intends to have at least two maintainers with release rights
before version 1.0. Contributors who have made sustained, high-quality
contributions (code, reviews or calendar verification) may be invited to
become maintainers by the existing maintainers.

## Decision making

Decisions are made by consensus among maintainers in public issues and pull
requests. If consensus cannot be reached, the lead maintainer decides.

## Rules that are not negotiable

- **Exact or nothing.** sambat only ships functionality whose results are
  exactly right by construction. Approximate models, projections of
  unpublished calendar years, and policy-dependent data (such as public
  holidays) are out of scope.
- **Calendar data needs a cited source.** A row may become `verified` only
  with a published panchang cited in `data/sources.toml`, including a
  checksum of the document that was checked.
- **Conversion results change only in minor or major releases**, never in a
  patch release, and always with a `calendar` changelog entry.
- **The `main` branch is protected.** Every change lands through a pull
  request with a passing CI run and an approving review.

## Releases

Releases follow [Semantic Versioning](https://semver.org/). The public API is
everything exported in the `__all__` of `sambat` and its public submodules.
Deprecated APIs emit `DeprecationWarning` for at least two minor releases (or
six months, whichever is longer) before removal in a major release.
