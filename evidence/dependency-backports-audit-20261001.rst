Dependency backport review
==========================

Copyright 2026 Qore Technologies, s.r.o.

Scope: dependency recipes, pinned sources, patches and installed ONNX SDK fixture.
Method: /home/david/.codex/skills/audit-changes/SKILL.md.
This is a code review, not repository or untested-architecture qualification.

Current spec hashes match completed binary builds and parse on all three targets.
ONNX Leap passes seven CTest groups, CMake/pkg-config consumers, inference and
negative cases, and Valgrind with zero errors or lost allocations. Its two policy
warnings concern the upstream private provider basename and duplicate licenses.
EL's clean ONNX rebuild remains pending; affected tests and the approved cpuinfo
startup-allocation baseline already have Valgrind evidence. Arrow's installed SDK
and policy checks pass; its recovered build lacks part of the test transcript,
which the evidence states explicitly. MongoDB mock/local tests and SDK consumers
pass. HTTP/parser evidence records the completed builds; nghttp2's Fedora crypto-
policy warnings are not represented as policy compliance.

.. list-table:: Complete skill checklist
   :header-rows: 1
   :widths: 48 8 44

   * - Check
     - Status
     - Evidence

   * - Entry exists in doxygen/lang/120_modules.dox.tmpl (for modules in the Qore repo; N/A for external module repos)
     - N/A
     - No Qore module registration, QPP API, DataProvider schema, Java dependency or .qtest change in this third-party backport scope.

   * - Entry exists in doxygen/lang/900_release_notes.dox.tmpl (for modules in the Qore repo; external modules have release notes in their .qm)
     - N/A
     - No Qore module registration, QPP API, DataProvider schema, Java dependency or .qtest change in this third-party backport scope.

   * - qore_user_module() or qore_external_user_module() call in CMakeLists.txt
     - N/A
     - No Qore module registration, QPP API, DataProvider schema, Java dependency or .qtest change in this third-party backport scope.

   * - Module added to QMOD list in CMakeLists.txt
     - N/A
     - No Qore module registration, QPP API, DataProvider schema, Java dependency or .qtest change in this third-party backport scope.

   * - .qm file has @section <lowercasemodname>intro as first doc section — must be all lowercase (e.g., avrodataproviderintro, not AvroDataProviderintro)
     - N/A
     - No Qore module registration, QPP API, DataProvider schema, Java dependency or .qtest change in this third-party backport scope.

   * - %modern in .qm file — no redundant %new-style, %require-types, %strict-args, %enable-all-warnings
     - N/A
     - No Qore module registration, QPP API, DataProvider schema, Java dependency or .qtest change in this third-party backport scope.

   * - No parse directives (%requires, %modern, %new-style) in separated .qc files (check OUTSIDE of @code blocks only)
     - N/A
     - No Qore module registration, QPP API, DataProvider schema, Java dependency or .qtest change in this third-party backport scope.

   * - No %include usage (deprecated for modules)
     - N/A
     - No Qore module registration, QPP API, DataProvider schema, Java dependency or .qtest change in this third-party backport scope.

   * - Copyright 2026 on all new files
     - Pass
     - New files use 2026; imported patches retain upstream authorship and license notices.

   * - Directory layout: .qm inside qlib/<ModuleName>/ directory (not at qlib/<ModuleName>.qm for multi-file modules)
     - N/A
     - No Qore module registration, QPP API, DataProvider schema, Java dependency or .qtest change in this third-party backport scope.

   * - No second .qm for the same module at qlib/<ModuleName>.qm
     - N/A
     - No Qore module registration, QPP API, DataProvider schema, Java dependency or .qtest change in this third-party backport scope.

   * - ns=Qore::XX matches the QoreNamespace constructor path
     - N/A
     - No Qore module registration, QPP API, DataProvider schema, Java dependency or .qtest change in this third-party backport scope.

   * - %modern directive present
     - N/A
     - No Qore module registration, QPP API, DataProvider schema, Java dependency or .qtest change in this third-party backport scope.

   * - Executable permission set (chmod +x)
     - N/A
     - No Qore module registration, QPP API, DataProvider schema, Java dependency or .qtest change in this third-party backport scope.

   * - Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus)
     - N/A
     - No Qore module registration, QPP API, DataProvider schema, Java dependency or .qtest change in this third-party backport scope.

   * - External module dependencies use %try-module — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard %requires
     - N/A
     - No Qore module registration, QPP API, DataProvider schema, Java dependency or .qtest change in this third-party backport scope.

   * - No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks
     - N/A
     - No Qore module registration, QPP API, DataProvider schema, Java dependency or .qtest change in this third-party backport scope.

   * - No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks
     - N/A
     - No Qore module registration, QPP API, DataProvider schema, Java dependency or .qtest change in this third-party backport scope.

   * - If filesystem/network ops exist, verify QoreSandboxManagerHelper usage
     - N/A
     - No Qore module registration, QPP API, DataProvider schema, Java dependency or .qtest change in this third-party backport scope.

   * - No File::, Dir::, Socket::, HTTPClient:: usage without justification
     - N/A
     - No Qore module registration, QPP API, DataProvider schema, Java dependency or .qtest change in this third-party backport scope.

   * - All for/while loops that could iterate >100 times have qore_check_cancel() checks
     - N/A
     - No Qore module registration, QPP API, DataProvider schema, Java dependency or .qtest change in this third-party backport scope.

   * - Uses qore_check_cancel() (NOT deprecated qore_check_io_interrupt())
     - N/A
     - No Qore module registration, QPP API, DataProvider schema, Java dependency or .qtest change in this third-party backport scope.

   * - Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations
     - N/A
     - No Qore module registration, QPP API, DataProvider schema, Java dependency or .qtest change in this third-party backport scope.

   * - No blocking operations without cancellation support
     - N/A
     - No Qore module registration, QPP API, DataProvider schema, Java dependency or .qtest change in this third-party backport scope.

   * - Every action has display_name, short_desc (plain text, <80 chars), desc (markdown)
     - N/A
     - No Qore module registration, QPP API, DataProvider schema, Java dependency or .qtest change in this third-party backport scope.

   * - Every action has options populated via getActionOptionFromFields() — without this, the action shows an empty, unusable form
     - N/A
     - No Qore module registration, QPP API, DataProvider schema, Java dependency or .qtest change in this third-party backport scope.

   * - Every action has output_type set to a typed data type constant (e.g., MyResponseDataType) — not omitted
     - N/A
     - No Qore module registration, QPP API, DataProvider schema, Java dependency or .qtest change in this third-party backport scope.

   * - DPAT_API actions: provider has "supports_request": True and implements doRequestImpl()
     - N/A
     - No Qore module registration, QPP API, DataProvider schema, Java dependency or .qtest change in this third-party backport scope.

   * - DPAT_FIND actions: every option exists in SearchOptions, getRecordTypeImpl() returns *hash<string, AbstractDataField>
     - N/A
     - No Qore module registration, QPP API, DataProvider schema, Java dependency or .qtest change in this third-party backport scope.

   * - Scheme-based apps (with "scheme" in registerApp): actions use "path" and do NOT use "cls" — having both scheme and cls causes a runtime error
     - N/A
     - No Qore module registration, QPP API, DataProvider schema, Java dependency or .qtest change in this third-party backport scope.

   * - Single-key hash slices use trailing comma: Fields{"key",} (without trailing comma, Fields{"key"} returns the value, not a hash)
     - N/A
     - No Qore module registration, QPP API, DataProvider schema, Java dependency or .qtest change in this third-party backport scope.

   * - Typed data type classes exist for request and response types — inherit HashDataType, have const Fields hash, call addQoreFields(Fields) in constructor, export public constant at bottom (e.g., public const MyDataType = new MyDataType();)
     - N/A
     - No Qore module registration, QPP API, DataProvider schema, Java dependency or .qtest change in this third-party backport scope.

   * - Request/input types use public Fields (enables ClassName::Fields in action registration)
     - N/A
     - No Qore module registration, QPP API, DataProvider schema, Java dependency or .qtest change in this third-party backport scope.

   * - Response/output types use private Fields
     - N/A
     - No Qore module registration, QPP API, DataProvider schema, Java dependency or .qtest change in this third-party backport scope.

   * - Each field in data types has display_name, type, and desc (markdown-formatted)
     - N/A
     - No Qore module registration, QPP API, DataProvider schema, Java dependency or .qtest change in this third-party backport scope.

   * - Input fields have example_value where useful (string fields, endpoint URIs, SQL queries, etc.)
     - N/A
     - No Qore module registration, QPP API, DataProvider schema, Java dependency or .qtest change in this third-party backport scope.

   * - Fields with finite allowed values use allowed_values with AllowedValueInfo containing both value and display_name (Title Case, human-readable) — never bare values, never described only in text
     - N/A
     - No Qore module registration, QPP API, DataProvider schema, Java dependency or .qtest change in this third-party backport scope.

   * - Password/secret fields have "sensitive": True
     - N/A
     - No Qore module registration, QPP API, DataProvider schema, Java dependency or .qtest change in this third-party backport scope.

   * - groups uses AppGroup enum values from qlib/DataProvider/AppGroup.qc
     - N/A
     - No Qore module registration, QPP API, DataProvider schema, Java dependency or .qtest change in this third-party backport scope.

   * - App logo stored as separate file, loaded at module level in Priv namespace
     - N/A
     - No Qore module registration, QPP API, DataProvider schema, Java dependency or .qtest change in this third-party backport scope.

   * - App desc uses markdown: bullet list of capabilities, links to project website, business-language explanation of value
     - N/A
     - No Qore module registration, QPP API, DataProvider schema, Java dependency or .qtest change in this third-party backport scope.

   * - display_name is user-friendly ("Apache Avro" not "avro")
     - N/A
     - No Qore module registration, QPP API, DataProvider schema, Java dependency or .qtest change in this third-party backport scope.

   * - short_desc is plain text, under 80 chars, single sentence — no markdown
     - N/A
     - No Qore module registration, QPP API, DataProvider schema, Java dependency or .qtest change in this third-party backport scope.

   * - desc uses markdown: backticks for code/field refs ( field_name ,  True ,  pdf ), \n\n for paragraphs, -  bullet lists for enumerations, bold for caveats
     - N/A
     - No Qore module registration, QPP API, DataProvider schema, Java dependency or .qtest change in this third-party backport scope.

   * - Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use"
     - N/A
     - No Qore module registration, QPP API, DataProvider schema, Java dependency or .qtest change in this third-party backport scope.

   * - No bare True/False/NOTHING — must be backtick-wrapped in desc
     - N/A
     - No Qore module registration, QPP API, DataProvider schema, Java dependency or .qtest change in this third-party backport scope.

   * - No bare field/option names in prose — must use backticks
     - N/A
     - No Qore module registration, QPP API, DataProvider schema, Java dependency or .qtest change in this third-party backport scope.

   * - Long descriptions (>500 chars) use bold section headers and bullet lists
     - N/A
     - No Qore module registration, QPP API, DataProvider schema, Java dependency or .qtest change in this third-party backport scope.

   * - Factory registration in Qore repo: every factory name registered in qlib/DataProvider/DataProvider.qc → FactoryMap (without this, module loads but doesn't appear in Qorus apps)
     - N/A
     - No Qore module registration, QPP API, DataProvider schema, Java dependency or .qtest change in this third-party backport scope.

   * - getRecordTypeImpl() signature: must be private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options) — NOT returning *AbstractDataProviderType
     - N/A
     - No Qore module registration, QPP API, DataProvider schema, Java dependency or .qtest change in this third-party backport scope.

   * - Dependency JARs committed (for JNI modules): JAR files in qlib/*/jar/ may be gitignored — use git add -f to ensure they're tracked, otherwise CI compilation fails
     - N/A
     - No Qore module registration, QPP API, DataProvider schema, Java dependency or .qtest change in this third-party backport scope.

   * - JAR install rules in CMakeLists.txt for all dependency JARs
     - N/A
     - No Qore module registration, QPP API, DataProvider schema, Java dependency or .qtest change in this third-party backport scope.

   * - No workarounds: No TODOs, FIXMEs, stubs, or partially-implemented features
     - Pass
     - Patches repair ownership, error propagation, numerical underflow, scalar test conversions and CPU dispatch. The approved cpuinfo exception is documented without suppression.

   * - Exception safety: C++ uses ReferenceHolder for Qore allocations, std::unique_ptr for C++ allocations, *xsink checked after every fallible operation
     - Pass
     - The ONNX consumer uses RAII. Existing library ownership is preserved. Python fixtures clean up subprocess groups, sockets and temporary files on failure.

   * - Thread safety: All mutable shared state protected by std::lock_guard<std::mutex> or documented as immutable-after-construction
     - Pass
     - No new mutable shared state. Existing c-ares synchronization remains. The unsafe cpuinfo cleanup was rejected because upstream found reentrancy and thread-safety failures.

   * - Type safety: Strongly-typed code<return(args)> instead of untyped code; static_cast instead of C casts; typed hashdecls for results; enums where appropriate
     - Pass
     - Consumer arrays are typed; tensor dimensions and output shapes are checked. Third-party public ABI types are unchanged.

   * - Performance: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply
     - Pass
     - Arrow baseline dispatch remains outside ISA-specific translation units. Softsign uses direct division for correct extreme values. No new quadratic scans or unbounded retry loops.

   * - Error handling: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable
     - Pass
     - Hashes, archive paths, license retention and offline inputs are validated. Tests cover invalid inference input names, absent models, daemon chdir failures and mock network errors.

   * - Documentation: Doxygen @param, @return, @throw on all public methods; @par Example with realistic business scenarios; @note for important caveats
     - Pass
     - README and evidence distinguish completed tests, recovered logs, pending architectures and the approved exception. Candidate builds are distinct from publication.

   * - QPP flags: [flags=CONSTANT] on methods that never throw; [flags=RET_VALUE_ONLY] on methods that throw but have no side effects
     - N/A
     - No Qore module registration, QPP API, DataProvider schema, Java dependency or .qtest change in this third-party backport scope.

   * - Security: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code
     - Pass
     - Archive checksums and paths are verified; credentials are absent. Installed ONNX ELF files have no build RPATH or executable stack.

   * - Correctness: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features)
     - Pass
     - Each of the eight current recipe hashes matches a successful binary build. All recipes parse on all three targets. All 63 helper tests pass; native and Valgrind evidence is retained per dependency.
