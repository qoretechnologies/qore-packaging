Installed gRPC qualification audit
==================================

Copyright 2026 Qore Technologies, s.r.o.

Scope: installed gRPC command generation, pinned fixture/runtime requirements, negative tool regressions, native ARM manifests, explicit CI jobs and qualification guide. All 62 checks: 10 Pass, 52 N/A, 0 Fail. No C++ changes or native implementation changes in this runner scope; Valgrind is not applicable.

.. list-table:: Complete audit-changes checklist
   :header-rows: 1

   * - Check
     - Status
     - Evidence

   * - 1. Entry exists in doxygen/lang/120_modules.dox.tmpl (for modules in the Qore repo; N/A for external module repos)
     - N/A
     - No new Qore/QPP/C++ module, DataProvider action/type/registration, JNI dependency, native sandbox/cancellation implementation or public runtime API. Python unittest files are executed through unittest discovery; existing runner executable mode is unchanged.

   * - 2. Entry exists in doxygen/lang/900_release_notes.dox.tmpl (for modules in the Qore repo; external modules have release notes in their .qm)
     - N/A
     - No new Qore/QPP/C++ module, DataProvider action/type/registration, JNI dependency, native sandbox/cancellation implementation or public runtime API. Python unittest files are executed through unittest discovery; existing runner executable mode is unchanged.

   * - 3. qore_user_module() or qore_external_user_module() call in CMakeLists.txt
     - N/A
     - No new Qore/QPP/C++ module, DataProvider action/type/registration, JNI dependency, native sandbox/cancellation implementation or public runtime API. Python unittest files are executed through unittest discovery; existing runner executable mode is unchanged.

   * - 4. Module added to QMOD list in CMakeLists.txt
     - N/A
     - No new Qore/QPP/C++ module, DataProvider action/type/registration, JNI dependency, native sandbox/cancellation implementation or public runtime API. Python unittest files are executed through unittest discovery; existing runner executable mode is unchanged.

   * - 5. .qm file has @section <lowercasemodname>intro as first doc section — must be all lowercase (e.g., avrodataproviderintro, not AvroDataProviderintro)
     - N/A
     - No new Qore/QPP/C++ module, DataProvider action/type/registration, JNI dependency, native sandbox/cancellation implementation or public runtime API. Python unittest files are executed through unittest discovery; existing runner executable mode is unchanged.

   * - 6. %modern in .qm file — no redundant %new-style, %require-types, %strict-args, %enable-all-warnings
     - N/A
     - No new Qore/QPP/C++ module, DataProvider action/type/registration, JNI dependency, native sandbox/cancellation implementation or public runtime API. Python unittest files are executed through unittest discovery; existing runner executable mode is unchanged.

   * - 7. No parse directives (%requires, %modern, %new-style) in separated .qc files (check OUTSIDE of @code blocks only)
     - N/A
     - No new Qore/QPP/C++ module, DataProvider action/type/registration, JNI dependency, native sandbox/cancellation implementation or public runtime API. Python unittest files are executed through unittest discovery; existing runner executable mode is unchanged.

   * - 8. No %include usage (deprecated for modules)
     - N/A
     - No new Qore/QPP/C++ module, DataProvider action/type/registration, JNI dependency, native sandbox/cancellation implementation or public runtime API. Python unittest files are executed through unittest discovery; existing runner executable mode is unchanged.

   * - 9. Copyright 2026 on all new files
     - Pass
     - All touched code and the new guide carry Copyright 2026.

   * - 10. Directory layout: .qm inside qlib/<ModuleName>/ directory (not at qlib/<ModuleName>.qm for multi-file modules)
     - N/A
     - No new Qore/QPP/C++ module, DataProvider action/type/registration, JNI dependency, native sandbox/cancellation implementation or public runtime API. Python unittest files are executed through unittest discovery; existing runner executable mode is unchanged.

   * - 11. No second .qm for the same module at qlib/<ModuleName>.qm
     - N/A
     - No new Qore/QPP/C++ module, DataProvider action/type/registration, JNI dependency, native sandbox/cancellation implementation or public runtime API. Python unittest files are executed through unittest discovery; existing runner executable mode is unchanged.

   * - 12. ns=Qore::XX matches the QoreNamespace constructor path
     - N/A
     - No new Qore/QPP/C++ module, DataProvider action/type/registration, JNI dependency, native sandbox/cancellation implementation or public runtime API. Python unittest files are executed through unittest discovery; existing runner executable mode is unchanged.

   * - 13. %modern directive present
     - N/A
     - No new Qore/QPP/C++ module, DataProvider action/type/registration, JNI dependency, native sandbox/cancellation implementation or public runtime API. Python unittest files are executed through unittest discovery; existing runner executable mode is unchanged.

   * - 14. Executable permission set (chmod +x)
     - N/A
     - No new Qore/QPP/C++ module, DataProvider action/type/registration, JNI dependency, native sandbox/cancellation implementation or public runtime API. Python unittest files are executed through unittest discovery; existing runner executable mode is unchanged.

   * - 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus)
     - N/A
     - No new Qore/QPP/C++ module, DataProvider action/type/registration, JNI dependency, native sandbox/cancellation implementation or public runtime API. Python unittest files are executed through unittest discovery; existing runner executable mode is unchanged.

   * - 16. External module dependencies use %try-module — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard %requires
     - N/A
     - No new Qore/QPP/C++ module, DataProvider action/type/registration, JNI dependency, native sandbox/cancellation implementation or public runtime API. Python unittest files are executed through unittest discovery; existing runner executable mode is unchanged.

   * - 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks
     - N/A
     - No new Qore/QPP/C++ module, DataProvider action/type/registration, JNI dependency, native sandbox/cancellation implementation or public runtime API. Python unittest files are executed through unittest discovery; existing runner executable mode is unchanged.

   * - 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks
     - N/A
     - No new Qore/QPP/C++ module, DataProvider action/type/registration, JNI dependency, native sandbox/cancellation implementation or public runtime API. Python unittest files are executed through unittest discovery; existing runner executable mode is unchanged.

   * - 19. If filesystem/network ops exist, verify QoreSandboxManagerHelper usage
     - N/A
     - No new Qore/QPP/C++ module, DataProvider action/type/registration, JNI dependency, native sandbox/cancellation implementation or public runtime API. Python unittest files are executed through unittest discovery; existing runner executable mode is unchanged.

   * - 20. No File::, Dir::, Socket::, HTTPClient:: usage without justification
     - N/A
     - No new Qore/QPP/C++ module, DataProvider action/type/registration, JNI dependency, native sandbox/cancellation implementation or public runtime API. Python unittest files are executed through unittest discovery; existing runner executable mode is unchanged.

   * - 21. All for/while loops that could iterate >100 times have qore_check_cancel() checks
     - N/A
     - No new Qore/QPP/C++ module, DataProvider action/type/registration, JNI dependency, native sandbox/cancellation implementation or public runtime API. Python unittest files are executed through unittest discovery; existing runner executable mode is unchanged.

   * - 22. Uses qore_check_cancel() (NOT deprecated qore_check_io_interrupt())
     - N/A
     - No new Qore/QPP/C++ module, DataProvider action/type/registration, JNI dependency, native sandbox/cancellation implementation or public runtime API. Python unittest files are executed through unittest discovery; existing runner executable mode is unchanged.

   * - 23. Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations
     - N/A
     - No new Qore/QPP/C++ module, DataProvider action/type/registration, JNI dependency, native sandbox/cancellation implementation or public runtime API. Python unittest files are executed through unittest discovery; existing runner executable mode is unchanged.

   * - 24. No blocking operations without cancellation support
     - N/A
     - No new Qore/QPP/C++ module, DataProvider action/type/registration, JNI dependency, native sandbox/cancellation implementation or public runtime API. Python unittest files are executed through unittest discovery; existing runner executable mode is unchanged.

   * - 25. Every action has display_name, short_desc (plain text, <80 chars), desc (markdown)
     - N/A
     - No new Qore/QPP/C++ module, DataProvider action/type/registration, JNI dependency, native sandbox/cancellation implementation or public runtime API. Python unittest files are executed through unittest discovery; existing runner executable mode is unchanged.

   * - 26. Every action has options populated via getActionOptionFromFields() — without this, the action shows an empty, unusable form
     - N/A
     - No new Qore/QPP/C++ module, DataProvider action/type/registration, JNI dependency, native sandbox/cancellation implementation or public runtime API. Python unittest files are executed through unittest discovery; existing runner executable mode is unchanged.

   * - 27. Every action has output_type set to a typed data type constant (e.g., MyResponseDataType) — not omitted
     - N/A
     - No new Qore/QPP/C++ module, DataProvider action/type/registration, JNI dependency, native sandbox/cancellation implementation or public runtime API. Python unittest files are executed through unittest discovery; existing runner executable mode is unchanged.

   * - 28. DPAT_API actions: provider has "supports_request": True and implements doRequestImpl()
     - N/A
     - No new Qore/QPP/C++ module, DataProvider action/type/registration, JNI dependency, native sandbox/cancellation implementation or public runtime API. Python unittest files are executed through unittest discovery; existing runner executable mode is unchanged.

   * - 29. DPAT_FIND actions: every option exists in SearchOptions, getRecordTypeImpl() returns *hash<string, AbstractDataField>
     - N/A
     - No new Qore/QPP/C++ module, DataProvider action/type/registration, JNI dependency, native sandbox/cancellation implementation or public runtime API. Python unittest files are executed through unittest discovery; existing runner executable mode is unchanged.

   * - 30. Scheme-based apps (with "scheme" in registerApp): actions use "path" and do NOT use "cls" — having both scheme and cls causes a runtime error
     - N/A
     - No new Qore/QPP/C++ module, DataProvider action/type/registration, JNI dependency, native sandbox/cancellation implementation or public runtime API. Python unittest files are executed through unittest discovery; existing runner executable mode is unchanged.

   * - 31. Single-key hash slices use trailing comma: Fields{"key",} (without trailing comma, Fields{"key"} returns the value, not a hash)
     - N/A
     - No new Qore/QPP/C++ module, DataProvider action/type/registration, JNI dependency, native sandbox/cancellation implementation or public runtime API. Python unittest files are executed through unittest discovery; existing runner executable mode is unchanged.

   * - 32. Typed data type classes exist for request and response types — inherit HashDataType, have const Fields hash, call addQoreFields(Fields) in constructor, export public constant at bottom (e.g., public const MyDataType = new MyDataType();)
     - N/A
     - No new Qore/QPP/C++ module, DataProvider action/type/registration, JNI dependency, native sandbox/cancellation implementation or public runtime API. Python unittest files are executed through unittest discovery; existing runner executable mode is unchanged.

   * - 33. Request/input types use public Fields (enables ClassName::Fields in action registration)
     - N/A
     - No new Qore/QPP/C++ module, DataProvider action/type/registration, JNI dependency, native sandbox/cancellation implementation or public runtime API. Python unittest files are executed through unittest discovery; existing runner executable mode is unchanged.

   * - 34. Response/output types use private Fields
     - N/A
     - No new Qore/QPP/C++ module, DataProvider action/type/registration, JNI dependency, native sandbox/cancellation implementation or public runtime API. Python unittest files are executed through unittest discovery; existing runner executable mode is unchanged.

   * - 35. Each field in data types has display_name, type, and desc (markdown-formatted)
     - N/A
     - No new Qore/QPP/C++ module, DataProvider action/type/registration, JNI dependency, native sandbox/cancellation implementation or public runtime API. Python unittest files are executed through unittest discovery; existing runner executable mode is unchanged.

   * - 36. Input fields have example_value where useful (string fields, endpoint URIs, SQL queries, etc.)
     - N/A
     - No new Qore/QPP/C++ module, DataProvider action/type/registration, JNI dependency, native sandbox/cancellation implementation or public runtime API. Python unittest files are executed through unittest discovery; existing runner executable mode is unchanged.

   * - 37. Fields with finite allowed values use allowed_values with AllowedValueInfo containing both value and display_name (Title Case, human-readable) — never bare values, never described only in text
     - N/A
     - No new Qore/QPP/C++ module, DataProvider action/type/registration, JNI dependency, native sandbox/cancellation implementation or public runtime API. Python unittest files are executed through unittest discovery; existing runner executable mode is unchanged.

   * - 38. Password/secret fields have "sensitive": True
     - N/A
     - No new Qore/QPP/C++ module, DataProvider action/type/registration, JNI dependency, native sandbox/cancellation implementation or public runtime API. Python unittest files are executed through unittest discovery; existing runner executable mode is unchanged.

   * - 39. groups uses AppGroup enum values from qlib/DataProvider/AppGroup.qc
     - N/A
     - No new Qore/QPP/C++ module, DataProvider action/type/registration, JNI dependency, native sandbox/cancellation implementation or public runtime API. Python unittest files are executed through unittest discovery; existing runner executable mode is unchanged.

   * - 40. App logo stored as separate file, loaded at module level in Priv namespace
     - N/A
     - No new Qore/QPP/C++ module, DataProvider action/type/registration, JNI dependency, native sandbox/cancellation implementation or public runtime API. Python unittest files are executed through unittest discovery; existing runner executable mode is unchanged.

   * - 41. App desc uses markdown: bullet list of capabilities, links to project website, business-language explanation of value
     - N/A
     - No new Qore/QPP/C++ module, DataProvider action/type/registration, JNI dependency, native sandbox/cancellation implementation or public runtime API. Python unittest files are executed through unittest discovery; existing runner executable mode is unchanged.

   * - 42. display_name is user-friendly ("Apache Avro" not "avro")
     - N/A
     - No new Qore/QPP/C++ module, DataProvider action/type/registration, JNI dependency, native sandbox/cancellation implementation or public runtime API. Python unittest files are executed through unittest discovery; existing runner executable mode is unchanged.

   * - 43. short_desc is plain text, under 80 chars, single sentence — no markdown
     - N/A
     - No new Qore/QPP/C++ module, DataProvider action/type/registration, JNI dependency, native sandbox/cancellation implementation or public runtime API. Python unittest files are executed through unittest discovery; existing runner executable mode is unchanged.

   * - 44. desc uses markdown: backticks for code/field refs ( field_name ,  True ,  pdf ), \n\n for paragraphs, -  bullet lists for enumerations, bold for caveats
     - N/A
     - No new Qore/QPP/C++ module, DataProvider action/type/registration, JNI dependency, native sandbox/cancellation implementation or public runtime API. Python unittest files are executed through unittest discovery; existing runner executable mode is unchanged.

   * - 45. Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use"
     - N/A
     - No new Qore/QPP/C++ module, DataProvider action/type/registration, JNI dependency, native sandbox/cancellation implementation or public runtime API. Python unittest files are executed through unittest discovery; existing runner executable mode is unchanged.

   * - 46. No bare True/False/NOTHING — must be backtick-wrapped in desc
     - N/A
     - No new Qore/QPP/C++ module, DataProvider action/type/registration, JNI dependency, native sandbox/cancellation implementation or public runtime API. Python unittest files are executed through unittest discovery; existing runner executable mode is unchanged.

   * - 47. No bare field/option names in prose — must use backticks
     - N/A
     - No new Qore/QPP/C++ module, DataProvider action/type/registration, JNI dependency, native sandbox/cancellation implementation or public runtime API. Python unittest files are executed through unittest discovery; existing runner executable mode is unchanged.

   * - 48. Long descriptions (>500 chars) use bold section headers and bullet lists
     - N/A
     - No new Qore/QPP/C++ module, DataProvider action/type/registration, JNI dependency, native sandbox/cancellation implementation or public runtime API. Python unittest files are executed through unittest discovery; existing runner executable mode is unchanged.

   * - 49. Factory registration in Qore repo: every factory name registered in qlib/DataProvider/DataProvider.qc → FactoryMap (without this, module loads but doesn't appear in Qorus apps)
     - N/A
     - No new Qore/QPP/C++ module, DataProvider action/type/registration, JNI dependency, native sandbox/cancellation implementation or public runtime API. Python unittest files are executed through unittest discovery; existing runner executable mode is unchanged.

   * - 50. getRecordTypeImpl() signature: must be private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options) — NOT returning *AbstractDataProviderType
     - N/A
     - No new Qore/QPP/C++ module, DataProvider action/type/registration, JNI dependency, native sandbox/cancellation implementation or public runtime API. Python unittest files are executed through unittest discovery; existing runner executable mode is unchanged.

   * - 51. Dependency JARs committed (for JNI modules): JAR files in qlib/*/jar/ may be gitignored — use git add -f to ensure they're tracked, otherwise CI compilation fails
     - N/A
     - No new Qore/QPP/C++ module, DataProvider action/type/registration, JNI dependency, native sandbox/cancellation implementation or public runtime API. Python unittest files are executed through unittest discovery; existing runner executable mode is unchanged.

   * - 52. JAR install rules in CMakeLists.txt for all dependency JARs
     - N/A
     - No new Qore/QPP/C++ module, DataProvider action/type/registration, JNI dependency, native sandbox/cancellation implementation or public runtime API. Python unittest files are executed through unittest discovery; existing runner executable mode is unchanged.

   * - 53. No workarounds: No TODOs, FIXMEs, stubs, or partially-implemented features
     - Pass
     - Run all thirteen suites and the actual SDK consumer. No warning filters, runtime compiler dependencies or checks disabled.

   * - 54. Exception safety: C++ uses ReferenceHolder for Qore allocations, std::unique_ptr for C++ allocations, *xsink checked after every fallible operation
     - Pass
     - Existing scoped temporary directories, checked subprocesses and final status records remain; new module path errors fail before execution.

   * - 55. Thread safety: All mutable shared state protected by std::lock_guard<std::mutex> or documented as immutable-after-construction
     - Pass
     - Runtime/SDK jobs use isolated containers and phase directories; fixtures and manifests are immutable inputs.

   * - 56. Type safety: Strongly-typed code<return(args)> instead of untyped code; static_cast instead of C casts; typed hashdecls for results; enums where appropriate
     - Pass
     - Path objects, structured subprocess argument lists, explicit binary/AOT suffixes and validated module/phase names.

   * - 57. Performance: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply
     - Pass
     - One bounded pass through 21 fixtures and 13 suite commands; cached identical RPM bytes reused only after hash verification.

   * - 58. Error handling: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable
     - Pass
     - Four regression methods cover missing/duplicate/moving/wrong-repository inputs, missing/runtime-misclassified process dependency and unsafe/ambiguous/mixed module paths.

   * - 59. Documentation: Doxygen @param, @return, @throw on all public methods; @par Example with realistic business scenarios; @note for important caveats
     - Pass
     - qualification/grpc.rst documents runtime/SDK scope, dependencies, command selection, immutable fixtures, source resolution, live-service limits and remaining repository gates.

   * - 60. QPP flags: [flags=CONSTANT] on methods that never throw; [flags=RET_VALUE_ONLY] on methods that throw but have no side effects
     - N/A
     - No new Qore/QPP/C++ module, DataProvider action/type/registration, JNI dependency, native sandbox/cancellation implementation or public runtime API. Python unittest files are executed through unittest discovery; existing runner executable mode is unchanged.

   * - 61. Security: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code
     - Pass
     - All 59 pinned RPM downloads and 21 immutable source fixture downloads verified. Existing strict signature validation is retained; tests execute as an unprivileged user after host module environment variables are removed. No compiler in the runtime-only phase.

   * - 62. Correctness: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features)
     - Pass
     - All 231 tool tests pass. Both local installed phases passed 13 suites / 378 cases / 1,768 assertions against prior revision 3; all six final revision 5 native builds pass 379 cases / 1,790 assertions. New manifests pin revision 5; signed ARM installed qualification is the next gate.
