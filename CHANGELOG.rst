.. _changelog:

=========
Changelog
=========

Versions follow `Semantic Versioning <https://semver.org>`_ (`<major>.<minor>.<patch>`).

Backward incompatible (breaking) changes will only be introduced in major versions with advance notice in the
**Deprecations** section of releases.

.. towncrier-draft-entries::

.. towncrier release notes start

1.0.2 (2022-02-16)
==================

Bug Fixes
---------

- Fixed issue with ``sdist`` recompression for reproducible packages not iterating though subdirectories contents. (`#1 <https://github.com/saltstack/pytest-system-statistics/issues/1>`_)


1.0.1 (2022-01-26)
==================

Trivial/Internal Changes
------------------------

- Reproducible builds
-  ``towncrier`` now uses ``issue_format``


system-statistics 1.0.0 (2022-01-05)
====================================

First Release.
