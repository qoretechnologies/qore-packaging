Installed module wave review
============================

Copyright 2026 Qore Technologies, s.r.o.

Scope: AMQP 4707320, ODBC 07724a8, ZeroMQ 567790b, ImageMagick 2f37f77,
PostgreSQL ba456f6, twenty-one Fedora OBS package build flags, Fedora installed
module evidence and Leap installed core, ODBC and ImageMagick evidence.
The in-progress Fedora BRP and Leap ZIP/PROJ fixes are excluded from this review.
All 62 checks in the audit-changes skill were considered below.

Validation: 71 orchestration tests pass; twenty-one modules pass the Fedora
installed SDK build and installed-runtime checks. ODBC and ImageMagick also
pass committed Leap builds and installed checks. ZeroMQ passes 113 cases;
ImageMagick passes 114 cases, CLI checks and 124380 translation checks on both
targets. PostgreSQL passes 32 cases with 382 assertions and required pgvector,
three public HTML checks, three uninstall checks and five fixture unit tests.
No C++ runtime implementation changed in these module updates. QPP comment
changes fix generated API links; CMake fixes restore documented public pages.
All twenty-one Fedora OBS module builds are enabled; publication stays disabled.
Fedora core OBS post-processing failures currently block their dependency closure.

The private PostgreSQL fixture validates inputs, isolates inherited connection
settings, uses a private Unix socket and always attempts shutdown after startup.
A failed shutdown preserves the cluster and fails the test. Native ODBC runtime
code is unchanged. Documentation tests verify actual generated API pages.

The combined module run emits the existing ProviderIndexUtil AOT source-selection
diagnostic when msgpack is installed. The user explicitly approved this expected
diagnostic on 2026-10-01. Functionality is preserved and no warning is suppressed.

.. list-table:: Complete audit checklist
   :header-rows: 1
   :widths: 48 8 44

   * - Check
     - Status
     - Evidence

   * - Entry exists in doxygen/lang/120_modules.dox.tmpl (for modules in the Qore repo; N/A for external module repos)
     - N/A
     - No new Qore modules, QPP classes, provider registrations or runtime implementation changes in this scope.

   * - Entry exists in doxygen/lang/900_release_notes.dox.tmpl (for modules in the Qore repo; external modules have release notes in their .qm)
     - Pass
     - AMQP, ODBC, ZeroMQ, ImageMagick and PostgreSQL mainpage release notes describe corrected public API documentation.

   * - qore_user_module() or qore_external_user_module() call in CMakeLists.txt
     - N/A
     - No new Qore modules, QPP classes, provider registrations or runtime implementation changes in this scope.

   * - Module added to QMOD list in CMakeLists.txt
     - N/A
     - No new Qore modules, QPP classes, provider registrations or runtime implementation changes in this scope.

   * - .qm file has @section <lowercasemodname>intro as first doc section — must be all lowercase (e.g., avrodataproviderintro, not AvroDataProviderintro)
     - N/A
     - No new Qore modules, QPP classes, provider registrations or runtime implementation changes in this scope.

   * - %modern in .qm file — no redundant %new-style, %require-types, %strict-args, %enable-all-warnings
     - N/A
     - No new Qore modules, QPP classes, provider registrations or runtime implementation changes in this scope.

   * - No parse directives (%requires, %modern, %new-style) in separated .qc files (check OUTSIDE of @code blocks only)
     - N/A
     - No new Qore modules, QPP classes, provider registrations or runtime implementation changes in this scope.

   * - No %include usage (deprecated for modules)
     - N/A
     - No new Qore modules, QPP classes, provider registrations or runtime implementation changes in this scope.

   * - Copyright 2026 on all new files
     - Pass
     - All new packaging, Python and shell files carry 2026 copyright notices.

   * - Directory layout: .qm inside qlib/<ModuleName>/ directory (not at qlib/<ModuleName>.qm for multi-file modules)
     - N/A
     - No new Qore modules, QPP classes, provider registrations or runtime implementation changes in this scope.

   * - No second .qm for the same module at qlib/<ModuleName>.qm
     - N/A
     - No new Qore modules, QPP classes, provider registrations or runtime implementation changes in this scope.

   * - ns=Qore::XX matches the QoreNamespace constructor path
     - N/A
     - No new Qore modules, QPP classes, provider registrations or runtime implementation changes in this scope.

   * - %modern directive present
     - N/A
     - No new Qore modules, QPP classes, provider registrations or runtime implementation changes in this scope.

   * - Executable permission set (chmod +x)
     - N/A
     - No new Qore modules, QPP classes, provider registrations or runtime implementation changes in this scope.

   * - Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus)
     - N/A
     - No new Qore modules, QPP classes, provider registrations or runtime implementation changes in this scope.

   * - External module dependencies use %try-module — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard %requires
     - N/A
     - No new Qore modules, QPP classes, provider registrations or runtime implementation changes in this scope.

   * - No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks
     - N/A
     - No new Qore modules, QPP classes, provider registrations or runtime implementation changes in this scope.

   * - No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks
     - N/A
     - No new Qore modules, QPP classes, provider registrations or runtime implementation changes in this scope.

   * - If filesystem/network ops exist, verify QoreSandboxManagerHelper usage
     - N/A
     - No new Qore modules, QPP classes, provider registrations or runtime implementation changes in this scope.

   * - No File::, Dir::, Socket::, HTTPClient:: usage without justification
     - N/A
     - No new Qore modules, QPP classes, provider registrations or runtime implementation changes in this scope.

   * - All for/while loops that could iterate >100 times have qore_check_cancel() checks
     - N/A
     - No new Qore modules, QPP classes, provider registrations or runtime implementation changes in this scope.

   * - Uses qore_check_cancel() (NOT deprecated qore_check_io_interrupt())
     - N/A
     - No new Qore modules, QPP classes, provider registrations or runtime implementation changes in this scope.

   * - Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations
     - N/A
     - No new Qore modules, QPP classes, provider registrations or runtime implementation changes in this scope.

   * - No blocking operations without cancellation support
     - N/A
     - No new Qore modules, QPP classes, provider registrations or runtime implementation changes in this scope.

   * - Every action has display_name, short_desc (plain text, <80 chars), desc (markdown)
     - N/A
     - No new Qore modules, QPP classes, provider registrations or runtime implementation changes in this scope.

   * - Every action has options populated via getActionOptionFromFields() — without this, the action shows an empty, unusable form
     - N/A
     - No new Qore modules, QPP classes, provider registrations or runtime implementation changes in this scope.

   * - Every action has output_type set to a typed data type constant (e.g., MyResponseDataType) — not omitted
     - N/A
     - No new Qore modules, QPP classes, provider registrations or runtime implementation changes in this scope.

   * - DPAT_API actions: provider has "supports_request": True and implements doRequestImpl()
     - N/A
     - No new Qore modules, QPP classes, provider registrations or runtime implementation changes in this scope.

   * - DPAT_FIND actions: every option exists in SearchOptions, getRecordTypeImpl() returns *hash<string, AbstractDataField>
     - N/A
     - No new Qore modules, QPP classes, provider registrations or runtime implementation changes in this scope.

   * - Scheme-based apps (with "scheme" in registerApp): actions use "path" and do NOT use "cls" — having both scheme and cls causes a runtime error
     - N/A
     - No new Qore modules, QPP classes, provider registrations or runtime implementation changes in this scope.

   * - Single-key hash slices use trailing comma: Fields{"key",} (without trailing comma, Fields{"key"} returns the value, not a hash)
     - N/A
     - No new Qore modules, QPP classes, provider registrations or runtime implementation changes in this scope.

   * - Typed data type classes exist for request and response types — inherit HashDataType, have const Fields hash, call addQoreFields(Fields) in constructor, export public constant at bottom (e.g., public const MyDataType = new MyDataType();)
     - N/A
     - No new Qore modules, QPP classes, provider registrations or runtime implementation changes in this scope.

   * - Request/input types use public Fields (enables ClassName::Fields in action registration)
     - N/A
     - No new Qore modules, QPP classes, provider registrations or runtime implementation changes in this scope.

   * - Response/output types use private Fields
     - N/A
     - No new Qore modules, QPP classes, provider registrations or runtime implementation changes in this scope.

   * - Each field in data types has display_name, type, and desc (markdown-formatted)
     - N/A
     - No new Qore modules, QPP classes, provider registrations or runtime implementation changes in this scope.

   * - Input fields have example_value where useful (string fields, endpoint URIs, SQL queries, etc.)
     - N/A
     - No new Qore modules, QPP classes, provider registrations or runtime implementation changes in this scope.

   * - Fields with finite allowed values use allowed_values with AllowedValueInfo containing both value and display_name (Title Case, human-readable) — never bare values, never described only in text
     - N/A
     - No new Qore modules, QPP classes, provider registrations or runtime implementation changes in this scope.

   * - Password/secret fields have "sensitive": True
     - N/A
     - No new Qore modules, QPP classes, provider registrations or runtime implementation changes in this scope.

   * - groups uses AppGroup enum values from qlib/DataProvider/AppGroup.qc
     - N/A
     - No new Qore modules, QPP classes, provider registrations or runtime implementation changes in this scope.

   * - App logo stored as separate file, loaded at module level in Priv namespace
     - N/A
     - No new Qore modules, QPP classes, provider registrations or runtime implementation changes in this scope.

   * - App desc uses markdown: bullet list of capabilities, links to project website, business-language explanation of value
     - N/A
     - No new Qore modules, QPP classes, provider registrations or runtime implementation changes in this scope.

   * - display_name is user-friendly ("Apache Avro" not "avro")
     - N/A
     - No new Qore modules, QPP classes, provider registrations or runtime implementation changes in this scope.

   * - short_desc is plain text, under 80 chars, single sentence — no markdown
     - N/A
     - No new Qore modules, QPP classes, provider registrations or runtime implementation changes in this scope.

   * - desc uses markdown: backticks for code/field refs ( field_name ,  True ,  pdf ), \n\n for paragraphs, -  bullet lists for enumerations, bold for caveats
     - N/A
     - No new Qore modules, QPP classes, provider registrations or runtime implementation changes in this scope.

   * - Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use"
     - N/A
     - No new Qore modules, QPP classes, provider registrations or runtime implementation changes in this scope.

   * - No bare True/False/NOTHING — must be backtick-wrapped in desc
     - N/A
     - No new Qore modules, QPP classes, provider registrations or runtime implementation changes in this scope.

   * - No bare field/option names in prose — must use backticks
     - N/A
     - No new Qore modules, QPP classes, provider registrations or runtime implementation changes in this scope.

   * - Long descriptions (>500 chars) use bold section headers and bullet lists
     - N/A
     - No new Qore modules, QPP classes, provider registrations or runtime implementation changes in this scope.

   * - Factory registration in Qore repo: every factory name registered in qlib/DataProvider/DataProvider.qc → FactoryMap (without this, module loads but doesn't appear in Qorus apps)
     - N/A
     - No new Qore modules, QPP classes, provider registrations or runtime implementation changes in this scope.

   * - getRecordTypeImpl() signature: must be private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options) — NOT returning *AbstractDataProviderType
     - N/A
     - No new Qore modules, QPP classes, provider registrations or runtime implementation changes in this scope.

   * - Dependency JARs committed (for JNI modules): JAR files in qlib/*/jar/ may be gitignored — use git add -f to ensure they're tracked, otherwise CI compilation fails
     - N/A
     - No new Qore modules, QPP classes, provider registrations or runtime implementation changes in this scope.

   * - JAR install rules in CMakeLists.txt for all dependency JARs
     - N/A
     - No new Qore modules, QPP classes, provider registrations or runtime implementation changes in this scope.

   * - No workarounds: No TODOs, FIXMEs, stubs, or partially-implemented features
     - Pass
     - Missing docs inputs and incorrect references are corrected at their source; real offline database tests run without skips.

   * - Exception safety: C++ uses ReferenceHolder for Qore allocations, std::unique_ptr for C++ allocations, *xsink checked after every fallible operation
     - Pass
     - Five fixture tests cover rejected inputs, nonzero command status, launch/start errors and failed shutdown preservation.

   * - Thread safety: All mutable shared state protected by std::lock_guard<std::mutex> or documented as immutable-after-construction
     - Pass
     - Each fixture owns a unique private temporary cluster; no shared database configuration is changed.

   * - Type safety: Strongly-typed code<return(args)> instead of untyped code; static_cast instead of C casts; typed hashdecls for results; enums where appropriate
     - Pass
     - Python subprocess argument arrays and pathlib paths avoid shell interpolation; no public API types change.

   * - Performance: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply
     - Pass
     - Tests process manifests and package paths linearly; no runtime algorithm changes.

   * - Error handling: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable
     - Pass
     - Five fixture tests cover rejected inputs, nonzero command status, launch/start errors and failed shutdown preservation.

   * - Documentation: Doxygen @param, @return, @throw on all public methods; @par Example with realistic business scenarios; @note for important caveats
     - Pass
     - RPM READMEs include source preparation, installed test commands and vendor coverage limits; generated HTML has regression checks.

   * - QPP flags: [flags=CONSTANT] on methods that never throw; [flags=RET_VALUE_ONLY] on methods that throw but have no side effects
     - N/A
     - No new Qore modules, QPP classes, provider registrations or runtime implementation changes in this scope.

   * - Security: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code
     - Pass
     - The unprivileged test cluster is accessible only through its private Unix socket; connection environment and driver paths are validated.

   * - Correctness: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features)
     - Pass
     - Pinned RPMs pass real installed suites; hashes, source revisions, images and explicitly deferred live AMQP coverage are recorded.
