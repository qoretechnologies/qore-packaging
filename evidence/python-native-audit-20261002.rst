Python native lifecycle review
==============================

Copyright 2026 Qore Technologies, s.r.o.

Scope: module-python native lifecycle changes, regression tests, CMake documentation configuration and CI/Debian test registration. RPM spec and fixture changes require a separate packaging audit.

.. list-table:: Complete audit-changes checklist
   :header-rows: 1

   * - Check
     - Status
     - Evidence

   * - 1. Entry exists in doxygen/lang/120_modules.dox.tmpl (for modules in the Qore repo; N/A for external module repos)
     - N/A
     - External native bridge maintenance: no new Qore user modules, data providers, public QPP methods, filesystem/network API or JAR payload in this change.

   * - 2. Entry exists in doxygen/lang/900_release_notes.dox.tmpl (for modules in the Qore repo; external modules have release notes in their .qm)
     - Pass
     - docs/mainpage.dox.tmpl records interpreter finalization, cross-interpreter ownership, modern Python calls and callable lifetime fixes.

   * - 3. qore_user_module() or qore_external_user_module() call in CMakeLists.txt
     - N/A
     - External native bridge maintenance: no new Qore user modules, data providers, public QPP methods, filesystem/network API or JAR payload in this change.

   * - 4. Module added to QMOD list in CMakeLists.txt
     - N/A
     - External native bridge maintenance: no new Qore user modules, data providers, public QPP methods, filesystem/network API or JAR payload in this change.

   * - 5. .qm file has @section <lowercasemodname>intro as first doc section — must be all lowercase (e.g., avrodataproviderintro, not AvroDataProviderintro)
     - N/A
     - External native bridge maintenance: no new Qore user modules, data providers, public QPP methods, filesystem/network API or JAR payload in this change.

   * - 6. %modern in .qm file — no redundant %new-style, %require-types, %strict-args, %enable-all-warnings
     - N/A
     - External native bridge maintenance: no new Qore user modules, data providers, public QPP methods, filesystem/network API or JAR payload in this change.

   * - 7. No parse directives (%requires, %modern, %new-style) in separated .qc files (check OUTSIDE of @code blocks only)
     - N/A
     - External native bridge maintenance: no new Qore user modules, data providers, public QPP methods, filesystem/network API or JAR payload in this change.

   * - 8. No %include usage (deprecated for modules)
     - N/A
     - External native bridge maintenance: no new Qore user modules, data providers, public QPP methods, filesystem/network API or JAR payload in this change.

   * - 9. Copyright 2026 on all new files
     - Pass
     - New tests and updated source/CI files carry 2026 copyrights.

   * - 10. Directory layout: .qm inside qlib/<ModuleName>/ directory (not at qlib/<ModuleName>.qm for multi-file modules)
     - N/A
     - External native bridge maintenance: no new Qore user modules, data providers, public QPP methods, filesystem/network API or JAR payload in this change.

   * - 11. No second .qm for the same module at qlib/<ModuleName>.qm
     - N/A
     - External native bridge maintenance: no new Qore user modules, data providers, public QPP methods, filesystem/network API or JAR payload in this change.

   * - 12. ns=Qore::XX matches the QoreNamespace constructor path
     - N/A
     - External native bridge maintenance: no new Qore user modules, data providers, public QPP methods, filesystem/network API or JAR payload in this change.

   * - 13. %modern directive present
     - Pass
     - test/python.qtest uses %modern; the standalone lifecycle regression is Python.

   * - 14. Executable permission set (chmod +x)
     - Pass
     - The Qore suite and standalone lifecycle regression are executable.

   * - 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus)
     - Pass
     - The external module suite resolves the selected build module through QORE_MODULE_DIR, set explicitly in qualification.

   * - 16. External module dependencies use %try-module — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard %requires
     - Pass
     - XML uses the existing %try-module pattern; package qualification preloads it and rejects missing coverage. JNI remains an explicitly separate integration gate.

   * - 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks
     - N/A
     - External native bridge maintenance: no new Qore user modules, data providers, public QPP methods, filesystem/network API or JAR payload in this change.

   * - 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks
     - N/A
     - External native bridge maintenance: no new Qore user modules, data providers, public QPP methods, filesystem/network API or JAR payload in this change.

   * - 19. If filesystem/network ops exist, verify QoreSandboxManagerHelper usage
     - N/A
     - External native bridge maintenance: no new Qore user modules, data providers, public QPP methods, filesystem/network API or JAR payload in this change.

   * - 20. No File::, Dir::, Socket::, HTTPClient:: usage without justification
     - N/A
     - External native bridge maintenance: no new Qore user modules, data providers, public QPP methods, filesystem/network API or JAR payload in this change.

   * - 21. All for/while loops that could iterate >100 times have qore_check_cancel() checks
     - Pass
     - New loops release registered references and thread states during finalization; aborting those cleanup loops would leave invalid Python references. Normal sandbox interruption still passes.

   * - 22. Uses qore_check_cancel() (NOT deprecated qore_check_io_interrupt())
     - N/A
     - External native bridge maintenance: no new Qore user modules, data providers, public QPP methods, filesystem/network API or JAR payload in this change.

   * - 23. Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations
     - N/A
     - External native bridge maintenance: no new Qore user modules, data providers, public QPP methods, filesystem/network API or JAR payload in this change.

   * - 24. No blocking operations without cancellation support
     - Pass
     - Existing interpreter thread joining retains its condition-variable protocol; the cancellation regression passes with debugging enabled.

   * - 25. Every action has display_name, short_desc (plain text, <80 chars), desc (markdown)
     - N/A
     - External native bridge maintenance: no new Qore user modules, data providers, public QPP methods, filesystem/network API or JAR payload in this change.

   * - 26. Every action has options populated via getActionOptionFromFields() — without this, the action shows an empty, unusable form
     - N/A
     - External native bridge maintenance: no new Qore user modules, data providers, public QPP methods, filesystem/network API or JAR payload in this change.

   * - 27. Every action has output_type set to a typed data type constant (e.g., MyResponseDataType) — not omitted
     - N/A
     - External native bridge maintenance: no new Qore user modules, data providers, public QPP methods, filesystem/network API or JAR payload in this change.

   * - 28. DPAT_API actions: provider has "supports_request": True and implements doRequestImpl()
     - N/A
     - External native bridge maintenance: no new Qore user modules, data providers, public QPP methods, filesystem/network API or JAR payload in this change.

   * - 29. DPAT_FIND actions: every option exists in SearchOptions, getRecordTypeImpl() returns *hash<string, AbstractDataField>
     - N/A
     - External native bridge maintenance: no new Qore user modules, data providers, public QPP methods, filesystem/network API or JAR payload in this change.

   * - 30. Scheme-based apps (with "scheme" in registerApp): actions use "path" and do NOT use "cls" — having both scheme and cls causes a runtime error
     - N/A
     - External native bridge maintenance: no new Qore user modules, data providers, public QPP methods, filesystem/network API or JAR payload in this change.

   * - 31. Single-key hash slices use trailing comma: Fields{"key",} (without trailing comma, Fields{"key"} returns the value, not a hash)
     - N/A
     - External native bridge maintenance: no new Qore user modules, data providers, public QPP methods, filesystem/network API or JAR payload in this change.

   * - 32. Typed data type classes exist for request and response types — inherit HashDataType, have const Fields hash, call addQoreFields(Fields) in constructor, export public constant at bottom (e.g., public const MyDataType = new MyDataType();)
     - N/A
     - External native bridge maintenance: no new Qore user modules, data providers, public QPP methods, filesystem/network API or JAR payload in this change.

   * - 33. Request/input types use public Fields (enables ClassName::Fields in action registration)
     - N/A
     - External native bridge maintenance: no new Qore user modules, data providers, public QPP methods, filesystem/network API or JAR payload in this change.

   * - 34. Response/output types use private Fields
     - N/A
     - External native bridge maintenance: no new Qore user modules, data providers, public QPP methods, filesystem/network API or JAR payload in this change.

   * - 35. Each field in data types has display_name, type, and desc (markdown-formatted)
     - N/A
     - External native bridge maintenance: no new Qore user modules, data providers, public QPP methods, filesystem/network API or JAR payload in this change.

   * - 36. Input fields have example_value where useful (string fields, endpoint URIs, SQL queries, etc.)
     - N/A
     - External native bridge maintenance: no new Qore user modules, data providers, public QPP methods, filesystem/network API or JAR payload in this change.

   * - 37. Fields with finite allowed values use allowed_values with AllowedValueInfo containing both value and display_name (Title Case, human-readable) — never bare values, never described only in text
     - N/A
     - External native bridge maintenance: no new Qore user modules, data providers, public QPP methods, filesystem/network API or JAR payload in this change.

   * - 38. Password/secret fields have "sensitive": True
     - N/A
     - External native bridge maintenance: no new Qore user modules, data providers, public QPP methods, filesystem/network API or JAR payload in this change.

   * - 39. groups uses AppGroup enum values from qlib/DataProvider/AppGroup.qc
     - N/A
     - External native bridge maintenance: no new Qore user modules, data providers, public QPP methods, filesystem/network API or JAR payload in this change.

   * - 40. App logo stored as separate file, loaded at module level in Priv namespace
     - N/A
     - External native bridge maintenance: no new Qore user modules, data providers, public QPP methods, filesystem/network API or JAR payload in this change.

   * - 41. App desc uses markdown: bullet list of capabilities, links to project website, business-language explanation of value
     - N/A
     - External native bridge maintenance: no new Qore user modules, data providers, public QPP methods, filesystem/network API or JAR payload in this change.

   * - 42. display_name is user-friendly ("Apache Avro" not "avro")
     - N/A
     - External native bridge maintenance: no new Qore user modules, data providers, public QPP methods, filesystem/network API or JAR payload in this change.

   * - 43. short_desc is plain text, under 80 chars, single sentence — no markdown
     - N/A
     - External native bridge maintenance: no new Qore user modules, data providers, public QPP methods, filesystem/network API or JAR payload in this change.

   * - 44. desc uses markdown: backticks for code/field refs ( field_name ,  True ,  pdf ), \n\n for paragraphs, -  bullet lists for enumerations, bold for caveats
     - N/A
     - External native bridge maintenance: no new Qore user modules, data providers, public QPP methods, filesystem/network API or JAR payload in this change.

   * - 45. Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use"
     - N/A
     - External native bridge maintenance: no new Qore user modules, data providers, public QPP methods, filesystem/network API or JAR payload in this change.

   * - 46. No bare True/False/NOTHING — must be backtick-wrapped in desc
     - N/A
     - External native bridge maintenance: no new Qore user modules, data providers, public QPP methods, filesystem/network API or JAR payload in this change.

   * - 47. No bare field/option names in prose — must use backticks
     - N/A
     - External native bridge maintenance: no new Qore user modules, data providers, public QPP methods, filesystem/network API or JAR payload in this change.

   * - 48. Long descriptions (>500 chars) use bold section headers and bullet lists
     - N/A
     - External native bridge maintenance: no new Qore user modules, data providers, public QPP methods, filesystem/network API or JAR payload in this change.

   * - 49. Factory registration in Qore repo: every factory name registered in qlib/DataProvider/DataProvider.qc → FactoryMap (without this, module loads but doesn't appear in Qorus apps)
     - N/A
     - External native bridge maintenance: no new Qore user modules, data providers, public QPP methods, filesystem/network API or JAR payload in this change.

   * - 50. getRecordTypeImpl() signature: must be private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options) — NOT returning *AbstractDataProviderType
     - N/A
     - External native bridge maintenance: no new Qore user modules, data providers, public QPP methods, filesystem/network API or JAR payload in this change.

   * - 51. Dependency JARs committed (for JNI modules): JAR files in qlib/*/jar/ may be gitignored — use git add -f to ensure they're tracked, otherwise CI compilation fails
     - N/A
     - External native bridge maintenance: no new Qore user modules, data providers, public QPP methods, filesystem/network API or JAR payload in this change.

   * - 52. JAR install rules in CMakeLists.txt for all dependency JARs
     - N/A
     - External native bridge maintenance: no new Qore user modules, data providers, public QPP methods, filesystem/network API or JAR payload in this change.

   * - 53. No workarounds: No TODOs, FIXMEs, stubs, or partially-implemented features
     - Pass
     - No compatibility shims hide removed call APIs. Use PyObject_Call, Py_EndInterpreter, owned capsules, active-interpreter ModuleSpec and proxy conversion. External runtime/compiler diagnostics have explicit user approval with separate evidence.

   * - 54. Exception safety: C++ uses ReferenceHolder for Qore allocations, std::unique_ptr for C++ allocations, *xsink checked after every fallible operation
     - Pass
     - Added temporary Python/Qore values use reference holders; callable metadata uses unique_ptr until a capsule owns it. Persistent registration holds the input reference during allocation and releases it only after registration succeeds. ModuleSpec failures preserve Python exceptions and are regression-tested.

   * - 55. Thread safety: All mutable shared state protected by std::lock_guard<std::mutex> or documented as immutable-after-construction
     - Pass
     - Persistent-reference and thread-state registries use py_thr_lck. Finalization drains active contexts before teardown; native cross-thread and free-threaded regressions exercise ownership and attachment restoration.

   * - 56. Type safety: Strongly-typed code<return(args)> instead of untyped code; static_cast instead of C casts; typed hashdecls for results; enums where appropriate
     - Pass
     - Added method metadata uses typed QoreMethod references; Python objects are converted according to the owning interpreter. No new untyped public Qore API.

   * - 57. Performance: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply
     - Pass
     - Reference registry draining removes entries before DECREF, permitting reentrant finalizers without rescanning cleared entries. No new public hot-path copies beyond callable-owned names and docs.

   * - 58. Error handling: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable
     - Pass
     - Empty call arguments, callback errors, injected ModuleSpec MemoryError, deleted interpreters and retained callables have negative coverage; the original error is propagated.

   * - 59. Documentation: Doxygen @param, @return, @throw on all public methods; @par Example with realistic business scenarios; @note for important caveats
     - Pass
     - Durable design documentation describes ownership and thread-state rules; release notes describe user-visible behavior. Strict Doxygen passes in the native matrix.

   * - 60. QPP flags: [flags=CONSTANT] on methods that never throw; [flags=RET_VALUE_ONLY] on methods that throw but have no side effects
     - N/A
     - External native bridge maintenance: no new Qore user modules, data providers, public QPP methods, filesystem/network API or JAR payload in this change.

   * - 61. Security: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code
     - Pass
     - No credentials or new network endpoints. Standalone tests use private temporary directories and argument-vector subprocess execution.

   * - 62. Correctness: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features)
     - Pass
     - Normal Python 3.12, 3.13 and 3.14 run 30 cases / 270 assertions. Free-threaded Python 3.14 runs 30 cases / 209 assertions with its existing JNI/unsupported-operation skips. Native Valgrind and standalone retained-callable evidence is reviewed separately before commit.
