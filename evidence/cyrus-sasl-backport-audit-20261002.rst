Cyrus SASL DIGEST-MD5 backport review
===================================

Copyright 2026 Qore Technologies, s.r.o.

Scope: dependencies/cyrus-sasl-digestmd5.*, both patches, test, and source pin.
The complete audit-changes checklist is applied below. This is a C dependency
backport, not a new Qore runtime API. Evidence: cyrus-sasl-backport-20261002.json.
Canonical source and native aarch64 results remain separate publication gates.

.. list-table:: Complete checklist
   :header-rows: 1
   :widths: 48 8 44

   * - Check
     - Status
     - Evidence

   * - Entry exists in doxygen/lang/120_modules.dox.tmpl (for modules in the Qore repo; N/A for external module repos)
     - N/A
     - No Qore module, QPP class, Qore test, DataProvider or Java code is changed. The external C cipher backport adds no filesystem/network operations or Qore cancellation boundary.

   * - Entry exists in doxygen/lang/900_release_notes.dox.tmpl (for modules in the Qore repo; external modules have release notes in their .qm)
     - N/A
     - No Qore module, QPP class, Qore test, DataProvider or Java code is changed. The external C cipher backport adds no filesystem/network operations or Qore cancellation boundary.

   * - qore_user_module() or qore_external_user_module() call in CMakeLists.txt
     - N/A
     - No Qore module, QPP class, Qore test, DataProvider or Java code is changed. The external C cipher backport adds no filesystem/network operations or Qore cancellation boundary.

   * - Module added to QMOD list in CMakeLists.txt
     - N/A
     - No Qore module, QPP class, Qore test, DataProvider or Java code is changed. The external C cipher backport adds no filesystem/network operations or Qore cancellation boundary.

   * - .qm file has @section <lowercasemodname>intro as first doc section — must be all lowercase (e.g., avrodataproviderintro, not AvroDataProviderintro)
     - N/A
     - No Qore module, QPP class, Qore test, DataProvider or Java code is changed. The external C cipher backport adds no filesystem/network operations or Qore cancellation boundary.

   * - %modern in .qm file — no redundant %new-style, %require-types, %strict-args, %enable-all-warnings
     - N/A
     - No Qore module, QPP class, Qore test, DataProvider or Java code is changed. The external C cipher backport adds no filesystem/network operations or Qore cancellation boundary.

   * - No parse directives (%requires, %modern, %new-style) in separated .qc files (check OUTSIDE of @code blocks only)
     - N/A
     - No Qore module, QPP class, Qore test, DataProvider or Java code is changed. The external C cipher backport adds no filesystem/network operations or Qore cancellation boundary.

   * - No %include usage (deprecated for modules)
     - N/A
     - No Qore module, QPP class, Qore test, DataProvider or Java code is changed. The external C cipher backport adds no filesystem/network operations or Qore cancellation boundary.

   * - Copyright 2026 on all new files
     - Pass
     - New patch attribution, test, recipe, notes and audit have 2026 copyright notices; original upstream attribution is retained.

   * - Directory layout: .qm inside qlib/<ModuleName>/ directory (not at qlib/<ModuleName>.qm for multi-file modules)
     - N/A
     - No Qore module, QPP class, Qore test, DataProvider or Java code is changed. The external C cipher backport adds no filesystem/network operations or Qore cancellation boundary.

   * - No second .qm for the same module at qlib/<ModuleName>.qm
     - N/A
     - No Qore module, QPP class, Qore test, DataProvider or Java code is changed. The external C cipher backport adds no filesystem/network operations or Qore cancellation boundary.

   * - ns=Qore::XX matches the QoreNamespace constructor path
     - N/A
     - No Qore module, QPP class, Qore test, DataProvider or Java code is changed. The external C cipher backport adds no filesystem/network operations or Qore cancellation boundary.

   * - %modern directive present
     - N/A
     - No Qore module, QPP class, Qore test, DataProvider or Java code is changed. The external C cipher backport adds no filesystem/network operations or Qore cancellation boundary.

   * - Executable permission set (chmod +x)
     - N/A
     - No Qore module, QPP class, Qore test, DataProvider or Java code is changed. The external C cipher backport adds no filesystem/network operations or Qore cancellation boundary.

   * - Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus)
     - N/A
     - No Qore module, QPP class, Qore test, DataProvider or Java code is changed. The external C cipher backport adds no filesystem/network operations or Qore cancellation boundary.

   * - External module dependencies use %try-module — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard %requires
     - N/A
     - No Qore module, QPP class, Qore test, DataProvider or Java code is changed. The external C cipher backport adds no filesystem/network operations or Qore cancellation boundary.

   * - No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks
     - N/A
     - No Qore module, QPP class, Qore test, DataProvider or Java code is changed. The external C cipher backport adds no filesystem/network operations or Qore cancellation boundary.

   * - No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks
     - N/A
     - No Qore module, QPP class, Qore test, DataProvider or Java code is changed. The external C cipher backport adds no filesystem/network operations or Qore cancellation boundary.

   * - If filesystem/network ops exist, verify QoreSandboxManagerHelper usage
     - N/A
     - No Qore module, QPP class, Qore test, DataProvider or Java code is changed. The external C cipher backport adds no filesystem/network operations or Qore cancellation boundary.

   * - No File::, Dir::, Socket::, HTTPClient:: usage without justification
     - N/A
     - No Qore module, QPP class, Qore test, DataProvider or Java code is changed. The external C cipher backport adds no filesystem/network operations or Qore cancellation boundary.

   * - All for/while loops that could iterate >100 times have qore_check_cancel() checks
     - N/A
     - No Qore module, QPP class, Qore test, DataProvider or Java code is changed. The external C cipher backport adds no filesystem/network operations or Qore cancellation boundary.

   * - Uses qore_check_cancel() (NOT deprecated qore_check_io_interrupt())
     - N/A
     - No Qore module, QPP class, Qore test, DataProvider or Java code is changed. The external C cipher backport adds no filesystem/network operations or Qore cancellation boundary.

   * - Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations
     - N/A
     - No Qore module, QPP class, Qore test, DataProvider or Java code is changed. The external C cipher backport adds no filesystem/network operations or Qore cancellation boundary.

   * - No blocking operations without cancellation support
     - N/A
     - No Qore module, QPP class, Qore test, DataProvider or Java code is changed. The external C cipher backport adds no filesystem/network operations or Qore cancellation boundary.

   * - Every action has display_name, short_desc (plain text, <80 chars), desc (markdown)
     - N/A
     - No Qore module, QPP class, Qore test, DataProvider or Java code is changed. The external C cipher backport adds no filesystem/network operations or Qore cancellation boundary.

   * - Every action has options populated via getActionOptionFromFields() — without this, the action shows an empty, unusable form
     - N/A
     - No Qore module, QPP class, Qore test, DataProvider or Java code is changed. The external C cipher backport adds no filesystem/network operations or Qore cancellation boundary.

   * - Every action has output_type set to a typed data type constant (e.g., MyResponseDataType) — not omitted
     - N/A
     - No Qore module, QPP class, Qore test, DataProvider or Java code is changed. The external C cipher backport adds no filesystem/network operations or Qore cancellation boundary.

   * - DPAT_API actions: provider has "supports_request": True and implements doRequestImpl()
     - N/A
     - No Qore module, QPP class, Qore test, DataProvider or Java code is changed. The external C cipher backport adds no filesystem/network operations or Qore cancellation boundary.

   * - DPAT_FIND actions: every option exists in SearchOptions, getRecordTypeImpl() returns *hash<string, AbstractDataField>
     - N/A
     - No Qore module, QPP class, Qore test, DataProvider or Java code is changed. The external C cipher backport adds no filesystem/network operations or Qore cancellation boundary.

   * - Scheme-based apps (with "scheme" in registerApp): actions use "path" and do NOT use "cls" — having both scheme and cls causes a runtime error
     - N/A
     - No Qore module, QPP class, Qore test, DataProvider or Java code is changed. The external C cipher backport adds no filesystem/network operations or Qore cancellation boundary.

   * - Single-key hash slices use trailing comma: Fields{"key",} (without trailing comma, Fields{"key"} returns the value, not a hash)
     - N/A
     - No Qore module, QPP class, Qore test, DataProvider or Java code is changed. The external C cipher backport adds no filesystem/network operations or Qore cancellation boundary.

   * - Typed data type classes exist for request and response types — inherit HashDataType, have const Fields hash, call addQoreFields(Fields) in constructor, export public constant at bottom (e.g., public const MyDataType = new MyDataType();)
     - N/A
     - No Qore module, QPP class, Qore test, DataProvider or Java code is changed. The external C cipher backport adds no filesystem/network operations or Qore cancellation boundary.

   * - Request/input types use public Fields (enables ClassName::Fields in action registration)
     - N/A
     - No Qore module, QPP class, Qore test, DataProvider or Java code is changed. The external C cipher backport adds no filesystem/network operations or Qore cancellation boundary.

   * - Response/output types use private Fields
     - N/A
     - No Qore module, QPP class, Qore test, DataProvider or Java code is changed. The external C cipher backport adds no filesystem/network operations or Qore cancellation boundary.

   * - Each field in data types has display_name, type, and desc (markdown-formatted)
     - N/A
     - No Qore module, QPP class, Qore test, DataProvider or Java code is changed. The external C cipher backport adds no filesystem/network operations or Qore cancellation boundary.

   * - Input fields have example_value where useful (string fields, endpoint URIs, SQL queries, etc.)
     - N/A
     - No Qore module, QPP class, Qore test, DataProvider or Java code is changed. The external C cipher backport adds no filesystem/network operations or Qore cancellation boundary.

   * - Fields with finite allowed values use allowed_values with AllowedValueInfo containing both value and display_name (Title Case, human-readable) — never bare values, never described only in text
     - N/A
     - No Qore module, QPP class, Qore test, DataProvider or Java code is changed. The external C cipher backport adds no filesystem/network operations or Qore cancellation boundary.

   * - Password/secret fields have "sensitive": True
     - N/A
     - No Qore module, QPP class, Qore test, DataProvider or Java code is changed. The external C cipher backport adds no filesystem/network operations or Qore cancellation boundary.

   * - groups uses AppGroup enum values from qlib/DataProvider/AppGroup.qc
     - N/A
     - No Qore module, QPP class, Qore test, DataProvider or Java code is changed. The external C cipher backport adds no filesystem/network operations or Qore cancellation boundary.

   * - App logo stored as separate file, loaded at module level in Priv namespace
     - N/A
     - No Qore module, QPP class, Qore test, DataProvider or Java code is changed. The external C cipher backport adds no filesystem/network operations or Qore cancellation boundary.

   * - App desc uses markdown: bullet list of capabilities, links to project website, business-language explanation of value
     - N/A
     - No Qore module, QPP class, Qore test, DataProvider or Java code is changed. The external C cipher backport adds no filesystem/network operations or Qore cancellation boundary.

   * - display_name is user-friendly ("Apache Avro" not "avro")
     - N/A
     - No Qore module, QPP class, Qore test, DataProvider or Java code is changed. The external C cipher backport adds no filesystem/network operations or Qore cancellation boundary.

   * - short_desc is plain text, under 80 chars, single sentence — no markdown
     - N/A
     - No Qore module, QPP class, Qore test, DataProvider or Java code is changed. The external C cipher backport adds no filesystem/network operations or Qore cancellation boundary.

   * - desc uses markdown: backticks for code/field refs ( field_name ,  True ,  pdf ), \n\n for paragraphs, -  bullet lists for enumerations, bold for caveats
     - N/A
     - No Qore module, QPP class, Qore test, DataProvider or Java code is changed. The external C cipher backport adds no filesystem/network operations or Qore cancellation boundary.

   * - Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use"
     - N/A
     - No Qore module, QPP class, Qore test, DataProvider or Java code is changed. The external C cipher backport adds no filesystem/network operations or Qore cancellation boundary.

   * - No bare True/False/NOTHING — must be backtick-wrapped in desc
     - N/A
     - No Qore module, QPP class, Qore test, DataProvider or Java code is changed. The external C cipher backport adds no filesystem/network operations or Qore cancellation boundary.

   * - No bare field/option names in prose — must use backticks
     - N/A
     - No Qore module, QPP class, Qore test, DataProvider or Java code is changed. The external C cipher backport adds no filesystem/network operations or Qore cancellation boundary.

   * - Long descriptions (>500 chars) use bold section headers and bullet lists
     - N/A
     - No Qore module, QPP class, Qore test, DataProvider or Java code is changed. The external C cipher backport adds no filesystem/network operations or Qore cancellation boundary.

   * - Factory registration in Qore repo: every factory name registered in qlib/DataProvider/DataProvider.qc → FactoryMap (without this, module loads but doesn't appear in Qorus apps)
     - N/A
     - No Qore module, QPP class, Qore test, DataProvider or Java code is changed. The external C cipher backport adds no filesystem/network operations or Qore cancellation boundary.

   * - getRecordTypeImpl() signature: must be private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options) — NOT returning *AbstractDataProviderType
     - N/A
     - No Qore module, QPP class, Qore test, DataProvider or Java code is changed. The external C cipher backport adds no filesystem/network operations or Qore cancellation boundary.

   * - Dependency JARs committed (for JNI modules): JAR files in qlib/*/jar/ may be gitignored — use git add -f to ensure they're tracked, otherwise CI compilation fails
     - N/A
     - No Qore module, QPP class, Qore test, DataProvider or Java code is changed. The external C cipher backport adds no filesystem/network operations or Qore cancellation boundary.

   * - JAR install rules in CMakeLists.txt for all dependency JARs
     - N/A
     - No Qore module, QPP class, Qore test, DataProvider or Java code is changed. The external C cipher backport adds no filesystem/network operations or Qore cancellation boundary.

   * - No workarounds: No TODOs, FIXMEs, stubs, or partially-implemented features
     - Pass
     - Root cause is missing OpenSSL 3 RC4 initialization and unchecked failure. Backport uses upstream error propagation and a per-connection provider context; no disabled tests or global provider changes. Generated configure/Makefiles are patched alongside their sources, then dependency timestamp ordering is restored.

   * - Exception safety: C++ uses ReferenceHolder for Qore allocations, std::unique_ptr for C++ allocations, *xsink checked after every fallible operation
     - Pass
     - C plugin owns each EVP context before fallible initialization, frees fetched cipher references on every path and unwinds partially initialized state. Nine injected failure points and repeated cleanup pass Valgrind with no errors or lost allocations.

   * - Thread safety: All mutable shared state protected by std::lock_guard<std::mutex> or documented as immutable-after-construction
     - Pass
     - Provider/cipher contexts belong to each SASL connection. Global OpenSSL context stays unchanged; failure-injection counters are confined to the single-threaded test executable.

   * - Type safety: Strongly-typed code<return(args)> instead of untyped code; static_cast instead of C casts; typed hashdecls for results; enums where appropriate
     - Pass
     - C uses the upstream typed OpenSSL and SASL interfaces; return codes and null pointers are checked. No C++ or Qore types are introduced.

   * - Performance: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply
     - Pass
     - Provider initialization occurs once per cipher connection; test failure loop has nine iterations. No unbounded or blocking loops added.

   * - Error handling: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable
     - Pass
     - Missing allocations, private contexts, providers, fetched ciphers and both initialization stages are exercised. Client and server propagate cipher-init failure to their existing cleanup paths.

   * - Documentation: Doxygen @param, @return, @throw on all public methods; @par Example with realistic business scenarios; @note for important caveats
     - Pass
     - Compatibility notes describe the crash, upstream sources, installation scope, full test coverage and the exact user-approved deprecation exception. Spec changelog records the backport.

   * - QPP flags: [flags=CONSTANT] on methods that never throw; [flags=RET_VALUE_ONLY] on methods that throw but have no side effects
     - N/A
     - No Qore module, QPP class, Qore test, DataProvider or Java code is changed. The external C cipher backport adds no filesystem/network operations or Qore cancellation boundary.

   * - Security: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code
     - Pass
     - Pinned upstream SHA256 is verified. Legacy provider is private; system crypto configuration stays unchanged. Test-only keys and buffers are fixed and sized; global RC4 availability is asserted unchanged.

   * - Correctness: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features)
     - Pass
     - Leap candidate 3 RPM completes; encrypted round trip, nine failure points and repeat cleanup pass Valgrind with zero errors/losses/suppressions. Installed RPM passes all 86 LDAP cases/501 assertions plus CLI and verified StartTLS checks. Only ten unchanged DES deprecation call sites are allowed, each emitted twice.
