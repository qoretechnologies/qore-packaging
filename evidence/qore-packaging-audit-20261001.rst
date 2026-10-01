Qore RPM packaging code audit
=============================

Copyright 2026 Qore Technologies, s.r.o.

Scope: uncommitted qore.spec-* and rpm/ changes on 2026-10-01.
Method: /home/david/.codex/skills/audit-changes/SKILL.md.
This is a code review record, not a release qualification or publication approval.

No C++, QPP, .qm/.qc modules, DataProviders or .qtest files are changed.
The Qore snippets in installed-package tests use %modern; their shell drivers
are executable and pass ShellCheck. SDK build fixes are separate commits.

Review correction: the spec now requires Python >= 3.11 for helpers using
BaseExceptionGroup. All three targets accept the corrected dependency.
The SDK package owns its installed language tag index. Runtime requirements
include glibc converters verified by the ISO-8859-2 minimal-install regression.

.. list-table:: Complete skill checklist
   :header-rows: 1
   :widths: 48 8 44

   * - Check
     - Status
     - Evidence

   * - Entry exists in doxygen/lang/120_modules.dox.tmpl (for modules in the Qore repo; N/A for external module repos)
     - N/A
     - No corresponding C++/Qore module, DataProvider, QPP or .qtest source changes in this packaging-only scope.

   * - Entry exists in doxygen/lang/900_release_notes.dox.tmpl (for modules in the Qore repo; external modules have release notes in their .qm)
     - N/A
     - No corresponding C++/Qore module, DataProvider, QPP or .qtest source changes in this packaging-only scope.

   * - qore_user_module() or qore_external_user_module() call in CMakeLists.txt
     - N/A
     - No corresponding C++/Qore module, DataProvider, QPP or .qtest source changes in this packaging-only scope.

   * - Module added to QMOD list in CMakeLists.txt
     - N/A
     - No corresponding C++/Qore module, DataProvider, QPP or .qtest source changes in this packaging-only scope.

   * - .qm file has @section <lowercasemodname>intro as first doc section — must be all lowercase (e.g., avrodataproviderintro, not AvroDataProviderintro)
     - N/A
     - No corresponding C++/Qore module, DataProvider, QPP or .qtest source changes in this packaging-only scope.

   * - %modern in .qm file — no redundant %new-style, %require-types, %strict-args, %enable-all-warnings
     - N/A
     - No corresponding C++/Qore module, DataProvider, QPP or .qtest source changes in this packaging-only scope.

   * - No parse directives (%requires, %modern, %new-style) in separated .qc files (check OUTSIDE of @code blocks only)
     - N/A
     - No corresponding C++/Qore module, DataProvider, QPP or .qtest source changes in this packaging-only scope.

   * - No %include usage (deprecated for modules)
     - N/A
     - No corresponding C++/Qore module, DataProvider, QPP or .qtest source changes in this packaging-only scope.

   * - Copyright 2026 on all new files
     - Pass
     - New helper, test and documentation copyright statements use 2026.

   * - Directory layout: .qm inside qlib/<ModuleName>/ directory (not at qlib/<ModuleName>.qm for multi-file modules)
     - N/A
     - No corresponding C++/Qore module, DataProvider, QPP or .qtest source changes in this packaging-only scope.

   * - No second .qm for the same module at qlib/<ModuleName>.qm
     - N/A
     - No corresponding C++/Qore module, DataProvider, QPP or .qtest source changes in this packaging-only scope.

   * - ns=Qore::XX matches the QoreNamespace constructor path
     - N/A
     - No corresponding C++/Qore module, DataProvider, QPP or .qtest source changes in this packaging-only scope.

   * - %modern directive present
     - N/A
     - No corresponding C++/Qore module, DataProvider, QPP or .qtest source changes in this packaging-only scope.

   * - Executable permission set (chmod +x)
     - N/A
     - No corresponding C++/Qore module, DataProvider, QPP or .qtest source changes in this packaging-only scope.

   * - Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus)
     - N/A
     - No corresponding C++/Qore module, DataProvider, QPP or .qtest source changes in this packaging-only scope.

   * - External module dependencies use %try-module — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard %requires
     - N/A
     - No corresponding C++/Qore module, DataProvider, QPP or .qtest source changes in this packaging-only scope.

   * - No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks
     - N/A
     - No corresponding C++/Qore module, DataProvider, QPP or .qtest source changes in this packaging-only scope.

   * - No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks
     - N/A
     - No corresponding C++/Qore module, DataProvider, QPP or .qtest source changes in this packaging-only scope.

   * - If filesystem/network ops exist, verify QoreSandboxManagerHelper usage
     - N/A
     - No corresponding C++/Qore module, DataProvider, QPP or .qtest source changes in this packaging-only scope.

   * - No File::, Dir::, Socket::, HTTPClient:: usage without justification
     - Pass
     - Embedded runtime tests intentionally read a copied ONNX model and metadata in temporary test directories.

   * - All for/while loops that could iterate >100 times have qore_check_cancel() checks
     - N/A
     - No corresponding C++/Qore module, DataProvider, QPP or .qtest source changes in this packaging-only scope.

   * - Uses qore_check_cancel() (NOT deprecated qore_check_io_interrupt())
     - N/A
     - No corresponding C++/Qore module, DataProvider, QPP or .qtest source changes in this packaging-only scope.

   * - Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations
     - N/A
     - No corresponding C++/Qore module, DataProvider, QPP or .qtest source changes in this packaging-only scope.

   * - No blocking operations without cancellation support
     - N/A
     - No corresponding C++/Qore module, DataProvider, QPP or .qtest source changes in this packaging-only scope.

   * - Every action has display_name, short_desc (plain text, <80 chars), desc (markdown)
     - N/A
     - No corresponding C++/Qore module, DataProvider, QPP or .qtest source changes in this packaging-only scope.

   * - Every action has options populated via getActionOptionFromFields() — without this, the action shows an empty, unusable form
     - N/A
     - No corresponding C++/Qore module, DataProvider, QPP or .qtest source changes in this packaging-only scope.

   * - Every action has output_type set to a typed data type constant (e.g., MyResponseDataType) — not omitted
     - N/A
     - No corresponding C++/Qore module, DataProvider, QPP or .qtest source changes in this packaging-only scope.

   * - DPAT_API actions: provider has "supports_request": True and implements doRequestImpl()
     - N/A
     - No corresponding C++/Qore module, DataProvider, QPP or .qtest source changes in this packaging-only scope.

   * - DPAT_FIND actions: every option exists in SearchOptions, getRecordTypeImpl() returns *hash<string, AbstractDataField>
     - N/A
     - No corresponding C++/Qore module, DataProvider, QPP or .qtest source changes in this packaging-only scope.

   * - Scheme-based apps (with "scheme" in registerApp): actions use "path" and do NOT use "cls" — having both scheme and cls causes a runtime error
     - N/A
     - No corresponding C++/Qore module, DataProvider, QPP or .qtest source changes in this packaging-only scope.

   * - Single-key hash slices use trailing comma: Fields{"key",} (without trailing comma, Fields{"key"} returns the value, not a hash)
     - N/A
     - No corresponding C++/Qore module, DataProvider, QPP or .qtest source changes in this packaging-only scope.

   * - Typed data type classes exist for request and response types — inherit HashDataType, have const Fields hash, call addQoreFields(Fields) in constructor, export public constant at bottom (e.g., public const MyDataType = new MyDataType();)
     - N/A
     - No corresponding C++/Qore module, DataProvider, QPP or .qtest source changes in this packaging-only scope.

   * - Request/input types use public Fields (enables ClassName::Fields in action registration)
     - N/A
     - No corresponding C++/Qore module, DataProvider, QPP or .qtest source changes in this packaging-only scope.

   * - Response/output types use private Fields
     - N/A
     - No corresponding C++/Qore module, DataProvider, QPP or .qtest source changes in this packaging-only scope.

   * - Each field in data types has display_name, type, and desc (markdown-formatted)
     - N/A
     - No corresponding C++/Qore module, DataProvider, QPP or .qtest source changes in this packaging-only scope.

   * - Input fields have example_value where useful (string fields, endpoint URIs, SQL queries, etc.)
     - N/A
     - No corresponding C++/Qore module, DataProvider, QPP or .qtest source changes in this packaging-only scope.

   * - Fields with finite allowed values use allowed_values with AllowedValueInfo containing both value and display_name (Title Case, human-readable) — never bare values, never described only in text
     - N/A
     - No corresponding C++/Qore module, DataProvider, QPP or .qtest source changes in this packaging-only scope.

   * - Password/secret fields have "sensitive": True
     - N/A
     - No corresponding C++/Qore module, DataProvider, QPP or .qtest source changes in this packaging-only scope.

   * - groups uses AppGroup enum values from qlib/DataProvider/AppGroup.qc
     - N/A
     - No corresponding C++/Qore module, DataProvider, QPP or .qtest source changes in this packaging-only scope.

   * - App logo stored as separate file, loaded at module level in Priv namespace
     - N/A
     - No corresponding C++/Qore module, DataProvider, QPP or .qtest source changes in this packaging-only scope.

   * - App desc uses markdown: bullet list of capabilities, links to project website, business-language explanation of value
     - N/A
     - No corresponding C++/Qore module, DataProvider, QPP or .qtest source changes in this packaging-only scope.

   * - display_name is user-friendly ("Apache Avro" not "avro")
     - N/A
     - No corresponding C++/Qore module, DataProvider, QPP or .qtest source changes in this packaging-only scope.

   * - short_desc is plain text, under 80 chars, single sentence — no markdown
     - N/A
     - No corresponding C++/Qore module, DataProvider, QPP or .qtest source changes in this packaging-only scope.

   * - desc uses markdown: backticks for code/field refs ( field_name ,  True ,  pdf ), \n\n for paragraphs, -  bullet lists for enumerations, bold for caveats
     - N/A
     - No corresponding C++/Qore module, DataProvider, QPP or .qtest source changes in this packaging-only scope.

   * - Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use"
     - N/A
     - No corresponding C++/Qore module, DataProvider, QPP or .qtest source changes in this packaging-only scope.

   * - No bare True/False/NOTHING — must be backtick-wrapped in desc
     - N/A
     - No corresponding C++/Qore module, DataProvider, QPP or .qtest source changes in this packaging-only scope.

   * - No bare field/option names in prose — must use backticks
     - N/A
     - No corresponding C++/Qore module, DataProvider, QPP or .qtest source changes in this packaging-only scope.

   * - Long descriptions (>500 chars) use bold section headers and bullet lists
     - N/A
     - No corresponding C++/Qore module, DataProvider, QPP or .qtest source changes in this packaging-only scope.

   * - Factory registration in Qore repo: every factory name registered in qlib/DataProvider/DataProvider.qc → FactoryMap (without this, module loads but doesn't appear in Qorus apps)
     - N/A
     - No corresponding C++/Qore module, DataProvider, QPP or .qtest source changes in this packaging-only scope.

   * - getRecordTypeImpl() signature: must be private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options) — NOT returning *AbstractDataProviderType
     - N/A
     - No corresponding C++/Qore module, DataProvider, QPP or .qtest source changes in this packaging-only scope.

   * - Dependency JARs committed (for JNI modules): JAR files in qlib/*/jar/ may be gitignored — use git add -f to ensure they're tracked, otherwise CI compilation fails
     - N/A
     - No corresponding C++/Qore module, DataProvider, QPP or .qtest source changes in this packaging-only scope.

   * - JAR install rules in CMakeLists.txt for all dependency JARs
     - N/A
     - No corresponding C++/Qore module, DataProvider, QPP or .qtest source changes in this packaging-only scope.

   * - No workarounds: No TODOs, FIXMEs, stubs, or partially-implemented features
     - Pass
     - No TODOs, stubs or silent feature omissions. ONNX is mandatory; AOT metadata handling follows the actual QAMD/QPCM/QAOM format.

   * - Exception safety: C++ uses ReferenceHolder for Qore allocations, std::unique_ptr for C++ allocations, *xsink checked after every fallible operation
     - Pass
     - Python helpers validate inputs first. Source files are replaced atomically; trailer restoration continues after an individual error and propagates all failures.

   * - Thread safety: All mutable shared state protected by std::lock_guard<std::mutex> or documented as immutable-after-construction
     - N/A
     - Helpers are single-process packaging utilities with no shared mutable runtime state.

   * - Type safety: Strongly-typed code<return(args)> instead of untyped code; static_cast instead of C casts; typed hashdecls for results; enums where appropriate
     - Pass
     - Binary footers use explicit little-endian struct layout; SDK EVR, ISA and API are validated. Embedded Qore test programs use modern syntax and typed values.

   * - Performance: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply
     - Pass
     - Helpers enumerate selected files once; metadata inspection starts at EOF and reads only the trailer chain.

   * - Error handling: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable
     - Pass
     - Negative tests cover malformed trailers, failed post-processing, symlink escapes, failed atomic replacement, invalid prefix maps and ambiguous SDK requirements.

   * - Documentation: Doxygen @param, @return, @throw on all public methods; @par Example with realistic business scenarios; @note for important caveats
     - Pass
     - rpm/README.rst documents prerequisites, package split, macros and validation commands. The spec changelog records the packaging change. No new public language methods.

   * - QPP flags: [flags=CONSTANT] on methods that never throw; [flags=RET_VALUE_ONLY] on methods that throw but have no side effects
     - N/A
     - No QPP changes.

   * - Security: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code
     - Pass
     - Subprocess arguments are passed as arrays; prefix-map shell arguments are quoted. Paths are checked against build/source roots. No credentials are present.

   * - Correctness: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features)
     - Pass
     - 25 helper tests and real RPM file-attribute/AOT/debug-source integration passed on Fedora, EL and Leap; real qcc RPM checks passed on Fedora. Installed-package qualification is recorded separately and remains required.

Qualification evidence: evidence/pilot-status-20261001.json.
The current working spec has additional dependency metadata and validation
changes beyond candidate 7; do not describe candidate 7 as an exact build of
the final committed packaging revision.
