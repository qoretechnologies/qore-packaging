Core revision 15 and module qualification review
================================================

Copyright 2026 Qore Technologies, s.r.o.

Scope: README, catalog, testing project configuration, 24 module metadata files
and core15-ssh-mysql-treesitter-20261002.json. Native fixes and Cyrus SASL
backports have separate audits. Native ARM and release gates remain open.

.. list-table:: Complete audit-changes checklist
   :header-rows: 1
   :widths: 48 8 44

   * - Check
     - Status
     - Evidence

   * - Entry exists in doxygen/lang/120_modules.dox.tmpl (for modules in the Qore repo; N/A for external module repos)
     - N/A
     - This change set contains packaging metadata and qualification records, with no Qore modules, C++/QPP implementation, DataProviders or executable test changes.

   * - Entry exists in doxygen/lang/900_release_notes.dox.tmpl (for modules in the Qore repo; external modules have release notes in their .qm)
     - N/A
     - This change set contains packaging metadata and qualification records, with no Qore modules, C++/QPP implementation, DataProviders or executable test changes.

   * - qore_user_module() or qore_external_user_module() call in CMakeLists.txt
     - N/A
     - This change set contains packaging metadata and qualification records, with no Qore modules, C++/QPP implementation, DataProviders or executable test changes.

   * - Module added to QMOD list in CMakeLists.txt
     - N/A
     - This change set contains packaging metadata and qualification records, with no Qore modules, C++/QPP implementation, DataProviders or executable test changes.

   * - .qm file has @section <lowercasemodname>intro as first doc section — must be all lowercase (e.g., avrodataproviderintro, not AvroDataProviderintro)
     - N/A
     - This change set contains packaging metadata and qualification records, with no Qore modules, C++/QPP implementation, DataProviders or executable test changes.

   * - %modern in .qm file — no redundant %new-style, %require-types, %strict-args, %enable-all-warnings
     - N/A
     - This change set contains packaging metadata and qualification records, with no Qore modules, C++/QPP implementation, DataProviders or executable test changes.

   * - No parse directives (%requires, %modern, %new-style) in separated .qc files (check OUTSIDE of @code blocks only)
     - N/A
     - This change set contains packaging metadata and qualification records, with no Qore modules, C++/QPP implementation, DataProviders or executable test changes.

   * - No %include usage (deprecated for modules)
     - N/A
     - This change set contains packaging metadata and qualification records, with no Qore modules, C++/QPP implementation, DataProviders or executable test changes.

   * - Copyright 2026 on all new files
     - Pass
     - The new configuration, metadata, evidence and this audit carry 2026 notices.

   * - Directory layout: .qm inside qlib/<ModuleName>/ directory (not at qlib/<ModuleName>.qm for multi-file modules)
     - N/A
     - This change set contains packaging metadata and qualification records, with no Qore modules, C++/QPP implementation, DataProviders or executable test changes.

   * - No second .qm for the same module at qlib/<ModuleName>.qm
     - N/A
     - This change set contains packaging metadata and qualification records, with no Qore modules, C++/QPP implementation, DataProviders or executable test changes.

   * - ns=Qore::XX matches the QoreNamespace constructor path
     - N/A
     - This change set contains packaging metadata and qualification records, with no Qore modules, C++/QPP implementation, DataProviders or executable test changes.

   * - %modern directive present
     - N/A
     - This change set contains packaging metadata and qualification records, with no Qore modules, C++/QPP implementation, DataProviders or executable test changes.

   * - Executable permission set (chmod +x)
     - N/A
     - This change set contains packaging metadata and qualification records, with no Qore modules, C++/QPP implementation, DataProviders or executable test changes.

   * - Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus)
     - N/A
     - This change set contains packaging metadata and qualification records, with no Qore modules, C++/QPP implementation, DataProviders or executable test changes.

   * - External module dependencies use %try-module — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard %requires
     - N/A
     - This change set contains packaging metadata and qualification records, with no Qore modules, C++/QPP implementation, DataProviders or executable test changes.

   * - No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks
     - N/A
     - This change set contains packaging metadata and qualification records, with no Qore modules, C++/QPP implementation, DataProviders or executable test changes.

   * - No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks
     - N/A
     - This change set contains packaging metadata and qualification records, with no Qore modules, C++/QPP implementation, DataProviders or executable test changes.

   * - If filesystem/network ops exist, verify QoreSandboxManagerHelper usage
     - N/A
     - This change set contains packaging metadata and qualification records, with no Qore modules, C++/QPP implementation, DataProviders or executable test changes.

   * - No File::, Dir::, Socket::, HTTPClient:: usage without justification
     - N/A
     - This change set contains packaging metadata and qualification records, with no Qore modules, C++/QPP implementation, DataProviders or executable test changes.

   * - All for/while loops that could iterate >100 times have qore_check_cancel() checks
     - N/A
     - This change set contains packaging metadata and qualification records, with no Qore modules, C++/QPP implementation, DataProviders or executable test changes.

   * - Uses qore_check_cancel() (NOT deprecated qore_check_io_interrupt())
     - N/A
     - This change set contains packaging metadata and qualification records, with no Qore modules, C++/QPP implementation, DataProviders or executable test changes.

   * - Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations
     - N/A
     - This change set contains packaging metadata and qualification records, with no Qore modules, C++/QPP implementation, DataProviders or executable test changes.

   * - No blocking operations without cancellation support
     - N/A
     - This change set contains packaging metadata and qualification records, with no Qore modules, C++/QPP implementation, DataProviders or executable test changes.

   * - Every action has display_name, short_desc (plain text, <80 chars), desc (markdown)
     - N/A
     - This change set contains packaging metadata and qualification records, with no Qore modules, C++/QPP implementation, DataProviders or executable test changes.

   * - Every action has options populated via getActionOptionFromFields() — without this, the action shows an empty, unusable form
     - N/A
     - This change set contains packaging metadata and qualification records, with no Qore modules, C++/QPP implementation, DataProviders or executable test changes.

   * - Every action has output_type set to a typed data type constant (e.g., MyResponseDataType) — not omitted
     - N/A
     - This change set contains packaging metadata and qualification records, with no Qore modules, C++/QPP implementation, DataProviders or executable test changes.

   * - DPAT_API actions: provider has "supports_request": True and implements doRequestImpl()
     - N/A
     - This change set contains packaging metadata and qualification records, with no Qore modules, C++/QPP implementation, DataProviders or executable test changes.

   * - DPAT_FIND actions: every option exists in SearchOptions, getRecordTypeImpl() returns *hash<string, AbstractDataField>
     - N/A
     - This change set contains packaging metadata and qualification records, with no Qore modules, C++/QPP implementation, DataProviders or executable test changes.

   * - Scheme-based apps (with "scheme" in registerApp): actions use "path" and do NOT use "cls" — having both scheme and cls causes a runtime error
     - N/A
     - This change set contains packaging metadata and qualification records, with no Qore modules, C++/QPP implementation, DataProviders or executable test changes.

   * - Single-key hash slices use trailing comma: Fields{"key",} (without trailing comma, Fields{"key"} returns the value, not a hash)
     - N/A
     - This change set contains packaging metadata and qualification records, with no Qore modules, C++/QPP implementation, DataProviders or executable test changes.

   * - Typed data type classes exist for request and response types — inherit HashDataType, have const Fields hash, call addQoreFields(Fields) in constructor, export public constant at bottom (e.g., public const MyDataType = new MyDataType();)
     - N/A
     - This change set contains packaging metadata and qualification records, with no Qore modules, C++/QPP implementation, DataProviders or executable test changes.

   * - Request/input types use public Fields (enables ClassName::Fields in action registration)
     - N/A
     - This change set contains packaging metadata and qualification records, with no Qore modules, C++/QPP implementation, DataProviders or executable test changes.

   * - Response/output types use private Fields
     - N/A
     - This change set contains packaging metadata and qualification records, with no Qore modules, C++/QPP implementation, DataProviders or executable test changes.

   * - Each field in data types has display_name, type, and desc (markdown-formatted)
     - N/A
     - This change set contains packaging metadata and qualification records, with no Qore modules, C++/QPP implementation, DataProviders or executable test changes.

   * - Input fields have example_value where useful (string fields, endpoint URIs, SQL queries, etc.)
     - N/A
     - This change set contains packaging metadata and qualification records, with no Qore modules, C++/QPP implementation, DataProviders or executable test changes.

   * - Fields with finite allowed values use allowed_values with AllowedValueInfo containing both value and display_name (Title Case, human-readable) — never bare values, never described only in text
     - N/A
     - This change set contains packaging metadata and qualification records, with no Qore modules, C++/QPP implementation, DataProviders or executable test changes.

   * - Password/secret fields have "sensitive": True
     - N/A
     - This change set contains packaging metadata and qualification records, with no Qore modules, C++/QPP implementation, DataProviders or executable test changes.

   * - groups uses AppGroup enum values from qlib/DataProvider/AppGroup.qc
     - N/A
     - This change set contains packaging metadata and qualification records, with no Qore modules, C++/QPP implementation, DataProviders or executable test changes.

   * - App logo stored as separate file, loaded at module level in Priv namespace
     - N/A
     - This change set contains packaging metadata and qualification records, with no Qore modules, C++/QPP implementation, DataProviders or executable test changes.

   * - App desc uses markdown: bullet list of capabilities, links to project website, business-language explanation of value
     - N/A
     - This change set contains packaging metadata and qualification records, with no Qore modules, C++/QPP implementation, DataProviders or executable test changes.

   * - display_name is user-friendly ("Apache Avro" not "avro")
     - N/A
     - This change set contains packaging metadata and qualification records, with no Qore modules, C++/QPP implementation, DataProviders or executable test changes.

   * - short_desc is plain text, under 80 chars, single sentence — no markdown
     - N/A
     - This change set contains packaging metadata and qualification records, with no Qore modules, C++/QPP implementation, DataProviders or executable test changes.

   * - desc uses markdown: backticks for code/field refs ( field_name ,  True ,  pdf ), \n\n for paragraphs, -  bullet lists for enumerations, bold for caveats
     - N/A
     - This change set contains packaging metadata and qualification records, with no Qore modules, C++/QPP implementation, DataProviders or executable test changes.

   * - Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use"
     - N/A
     - This change set contains packaging metadata and qualification records, with no Qore modules, C++/QPP implementation, DataProviders or executable test changes.

   * - No bare True/False/NOTHING — must be backtick-wrapped in desc
     - N/A
     - This change set contains packaging metadata and qualification records, with no Qore modules, C++/QPP implementation, DataProviders or executable test changes.

   * - No bare field/option names in prose — must use backticks
     - N/A
     - This change set contains packaging metadata and qualification records, with no Qore modules, C++/QPP implementation, DataProviders or executable test changes.

   * - Long descriptions (>500 chars) use bold section headers and bullet lists
     - N/A
     - This change set contains packaging metadata and qualification records, with no Qore modules, C++/QPP implementation, DataProviders or executable test changes.

   * - Factory registration in Qore repo: every factory name registered in qlib/DataProvider/DataProvider.qc → FactoryMap (without this, module loads but doesn't appear in Qorus apps)
     - N/A
     - This change set contains packaging metadata and qualification records, with no Qore modules, C++/QPP implementation, DataProviders or executable test changes.

   * - getRecordTypeImpl() signature: must be private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options) — NOT returning *AbstractDataProviderType
     - N/A
     - This change set contains packaging metadata and qualification records, with no Qore modules, C++/QPP implementation, DataProviders or executable test changes.

   * - Dependency JARs committed (for JNI modules): JAR files in qlib/*/jar/ may be gitignored — use git add -f to ensure they're tracked, otherwise CI compilation fails
     - N/A
     - This change set contains packaging metadata and qualification records, with no Qore modules, C++/QPP implementation, DataProviders or executable test changes.

   * - JAR install rules in CMakeLists.txt for all dependency JARs
     - N/A
     - This change set contains packaging metadata and qualification records, with no Qore modules, C++/QPP implementation, DataProviders or executable test changes.

   * - No workarounds: No TODOs, FIXMEs, stubs, or partially-implemented features
     - Pass
     - Build flags retain disabled publication; CPU ONNX preference resolves an actual ambiguous provider without weakening tests.

   * - Exception safety: C++ uses ReferenceHolder for Qore allocations, std::unique_ptr for C++ allocations, *xsink checked after every fallible operation
     - N/A
     - This change set contains packaging metadata and qualification records, with no Qore modules, C++/QPP implementation, DataProviders or executable test changes.

   * - Thread safety: All mutable shared state protected by std::lock_guard<std::mutex> or documented as immutable-after-construction
     - Pass
     - No shared runtime state; metadata is applied with an exact-current-state guard and read back.

   * - Type safety: Strongly-typed code<return(args)> instead of untyped code; static_cast instead of C casts; typed hashdecls for results; enums where appropriate
     - Pass
     - JSON schemas and XML attributes are checked by orchestration tests and explicit target-set assertions.

   * - Performance: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply
     - Pass
     - Only documentation, metadata and recorded results change.

   * - Error handling: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable
     - Pass
     - All result exit codes and source/artifact digests are checked before qualification is recorded.

   * - Documentation: Doxygen @param, @return, @throw on all public methods; @par Example with realistic business scenarios; @note for important caveats
     - Pass
     - README describes current qualification, diagnostic exceptions and unresolved architecture gates.

   * - QPP flags: [flags=CONSTANT] on methods that never throw; [flags=RET_VALUE_ONLY] on methods that throw but have no side effects
     - N/A
     - This change set contains packaging metadata and qualification records, with no Qore modules, C++/QPP implementation, DataProviders or executable test changes.

   * - Security: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code
     - Pass
     - Source commits and artifact hashes are pinned; no credentials recorded; testing publication remains disabled.

   * - Correctness: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features)
     - Pass
     - 71 orchestration tests pass; all three distributions pass canonical core, SSH, MySQL and tree-sitter qualification; OBS provider/build flags were read back.

Additional packaging-only scope reviewed on 2026-10-02
-----------------------------------------------------

The same complete checklist covers the LDAP/SSH2 canonical evidence, their two
new package metadata files, Leap-only Cyrus SASL metadata and the OBS resolver
configuration. All new metadata preserves disabled publication. LDAP final
RPM, runtime and SDK checks pass on all targets; SSH2 final RPM and runtime
steps pass independently of the still-running XML worker. OBS buildinfo verifies
the interpreter and the same libgit2 provider families used locally. Canonical
Cyrus SASL is built and exercised by Leap's installed LDAP suite. Its native
backport audit is separate. The original three module uploads and Cyrus upload
are verified against every remote source MD5, including the pinned manifests.
