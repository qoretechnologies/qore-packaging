Offline source bundle completeness
==================================

Copyright 2026 Qore Technologies, s.r.o.

Both module and dependency preparation validate every Source and Patch declared
by the recipe before exposing the completed directory. The build and OBS upload
tools repeat this validation after verifying all manifest checksums. This catches
omitted vendor archives even when every file present has a valid checksum.

Recipes may use literal filenames, URL basenames, URL fragment renames such as
``archive/1.0#/%{name}-%{version}.tar.gz``, and the pinned ``%{name}`` and
``%{version}`` macros. Other macros and escaped URLs are rejected rather than
executed. Sources in conditional recipe branches must all be included so one
bundle supports every target. Source declarations in comments are ignored.

For a module with a vendor manifest, pass ``--vendor-manifest
rpm/vendor-sources.json --cache cache`` to ``tools/packaging.py prepare``.
The manifest is read from the same committed revision as the module; each
upstream archive is verified, normalized and checked for retained licenses.
A missing Source or Patch fails preparation without leaving a result or temporary
directory. It also fails an existing bundle before container startup, driver
launch, or any OBS request.
