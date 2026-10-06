Tree-sitter installed qualification
===================================

Copyright 2026 Qore Technologies, s.r.o.

The ``treesitter-*-aarch64.json`` manifests install the signed native OBS
Tree-sitter RPM with the qualified Qore core. They pin the complete parser suite
and compiler smoke test to the same immutable module revision as the RPM source.

The runtime suite exercises all packaged grammars, parser errors, incremental
edits, node and cursor ownership, query files and query-directory overrides.
It runs with Qore debugging enabled and clears inherited
``QORE_TREESITTER_QUERY_DIR`` so default query checks use the installed payload.
The SDK phase repeats the suite, compiles a named-argument Python parser example,
and loads the packaged Python highlight query from the compiled executable.

Select these jobs with ``RPM_NATIVE_QUALIFICATION=treesitter``; optionally set
``RPM_NATIVE_TARGET`` to ``fedora``, ``leap`` or ``el10``. The manifests start with
the qualified core and this module so unrelated module suites do not need to
run again. Whole-repository lifecycle checks remain a separate publication gate.
