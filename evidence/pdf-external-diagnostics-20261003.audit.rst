PDF external diagnostic controls audit
======================================

Copyright 2026 Qore Technologies, s.r.o.

Scope: two standalone native compiler/Valgrind controls and the explicit user-approved diagnostic records. No runtime, compiler-option or suppression changes.

.. list-table:: Complete audit-changes checklist
   :header-rows: 1

   * - Check
     - Status
     - Evidence

   * - 1. Entry exists in doxygen/lang/120_modules.dox.tmpl (for modules in the Qore repo; N/A for external module repos)
     - N/A
     - Standalone diagnostic controls and evidence only; no Qore module/provider/API, sandbox operation, production loop or package behavior change.

   * - 2. Entry exists in doxygen/lang/900_release_notes.dox.tmpl (for modules in the Qore repo; external modules have release notes in their .qm)
     - N/A
     - Standalone diagnostic controls and evidence only; no Qore module/provider/API, sandbox operation, production loop or package behavior change.

   * - 3. qore_user_module() or qore_external_user_module() call in CMakeLists.txt
     - N/A
     - Standalone diagnostic controls and evidence only; no Qore module/provider/API, sandbox operation, production loop or package behavior change.

   * - 4. Module added to QMOD list in CMakeLists.txt
     - N/A
     - Standalone diagnostic controls and evidence only; no Qore module/provider/API, sandbox operation, production loop or package behavior change.

   * - 5. .qm file has @section <lowercasemodname>intro as first doc section — must be all lowercase (e.g., avrodataproviderintro, not AvroDataProviderintro)
     - N/A
     - Standalone diagnostic controls and evidence only; no Qore module/provider/API, sandbox operation, production loop or package behavior change.

   * - 6. %modern in .qm file — no redundant %new-style, %require-types, %strict-args, %enable-all-warnings
     - N/A
     - Standalone diagnostic controls and evidence only; no Qore module/provider/API, sandbox operation, production loop or package behavior change.

   * - 7. No parse directives (%requires, %modern, %new-style) in separated .qc files (check OUTSIDE of @code blocks only)
     - N/A
     - Standalone diagnostic controls and evidence only; no Qore module/provider/API, sandbox operation, production loop or package behavior change.

   * - 8. No %include usage (deprecated for modules)
     - N/A
     - Standalone diagnostic controls and evidence only; no Qore module/provider/API, sandbox operation, production loop or package behavior change.

   * - 9. Copyright 2026 on all new files
     - Pass
     - Both controls and records carry 2026 copyright.

   * - 10. Directory layout: .qm inside qlib/<ModuleName>/ directory (not at qlib/<ModuleName>.qm for multi-file modules)
     - N/A
     - Standalone diagnostic controls and evidence only; no Qore module/provider/API, sandbox operation, production loop or package behavior change.

   * - 11. No second .qm for the same module at qlib/<ModuleName>.qm
     - N/A
     - Standalone diagnostic controls and evidence only; no Qore module/provider/API, sandbox operation, production loop or package behavior change.

   * - 12. ns=Qore::XX matches the QoreNamespace constructor path
     - N/A
     - Standalone diagnostic controls and evidence only; no Qore module/provider/API, sandbox operation, production loop or package behavior change.

   * - 13. %modern directive present
     - N/A
     - Standalone diagnostic controls and evidence only; no Qore module/provider/API, sandbox operation, production loop or package behavior change.

   * - 14. Executable permission set (chmod +x)
     - N/A
     - Standalone diagnostic controls and evidence only; no Qore module/provider/API, sandbox operation, production loop or package behavior change.

   * - 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus)
     - N/A
     - Standalone diagnostic controls and evidence only; no Qore module/provider/API, sandbox operation, production loop or package behavior change.

   * - 16. External module dependencies use %try-module — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard %requires
     - N/A
     - Standalone diagnostic controls and evidence only; no Qore module/provider/API, sandbox operation, production loop or package behavior change.

   * - 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks
     - N/A
     - Standalone diagnostic controls and evidence only; no Qore module/provider/API, sandbox operation, production loop or package behavior change.

   * - 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks
     - N/A
     - Standalone diagnostic controls and evidence only; no Qore module/provider/API, sandbox operation, production loop or package behavior change.

   * - 19. If filesystem/network ops exist, verify QoreSandboxManagerHelper usage
     - N/A
     - Standalone diagnostic controls and evidence only; no Qore module/provider/API, sandbox operation, production loop or package behavior change.

   * - 20. No File::, Dir::, Socket::, HTTPClient:: usage without justification
     - N/A
     - Standalone diagnostic controls and evidence only; no Qore module/provider/API, sandbox operation, production loop or package behavior change.

   * - 21. All for/while loops that could iterate >100 times have qore_check_cancel() checks
     - N/A
     - Standalone diagnostic controls and evidence only; no Qore module/provider/API, sandbox operation, production loop or package behavior change.

   * - 22. Uses qore_check_cancel() (NOT deprecated qore_check_io_interrupt())
     - N/A
     - Standalone diagnostic controls and evidence only; no Qore module/provider/API, sandbox operation, production loop or package behavior change.

   * - 23. Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations
     - N/A
     - Standalone diagnostic controls and evidence only; no Qore module/provider/API, sandbox operation, production loop or package behavior change.

   * - 24. No blocking operations without cancellation support
     - N/A
     - Standalone diagnostic controls and evidence only; no Qore module/provider/API, sandbox operation, production loop or package behavior change.

   * - 25. Every action has display_name, short_desc (plain text, <80 chars), desc (markdown)
     - N/A
     - Standalone diagnostic controls and evidence only; no Qore module/provider/API, sandbox operation, production loop or package behavior change.

   * - 26. Every action has options populated via getActionOptionFromFields() — without this, the action shows an empty, unusable form
     - N/A
     - Standalone diagnostic controls and evidence only; no Qore module/provider/API, sandbox operation, production loop or package behavior change.

   * - 27. Every action has output_type set to a typed data type constant (e.g., MyResponseDataType) — not omitted
     - N/A
     - Standalone diagnostic controls and evidence only; no Qore module/provider/API, sandbox operation, production loop or package behavior change.

   * - 28. DPAT_API actions: provider has "supports_request": True and implements doRequestImpl()
     - N/A
     - Standalone diagnostic controls and evidence only; no Qore module/provider/API, sandbox operation, production loop or package behavior change.

   * - 29. DPAT_FIND actions: every option exists in SearchOptions, getRecordTypeImpl() returns *hash<string, AbstractDataField>
     - N/A
     - Standalone diagnostic controls and evidence only; no Qore module/provider/API, sandbox operation, production loop or package behavior change.

   * - 30. Scheme-based apps (with "scheme" in registerApp): actions use "path" and do NOT use "cls" — having both scheme and cls causes a runtime error
     - N/A
     - Standalone diagnostic controls and evidence only; no Qore module/provider/API, sandbox operation, production loop or package behavior change.

   * - 31. Single-key hash slices use trailing comma: Fields{"key",} (without trailing comma, Fields{"key"} returns the value, not a hash)
     - N/A
     - Standalone diagnostic controls and evidence only; no Qore module/provider/API, sandbox operation, production loop or package behavior change.

   * - 32. Typed data type classes exist for request and response types — inherit HashDataType, have const Fields hash, call addQoreFields(Fields) in constructor, export public constant at bottom (e.g., public const MyDataType = new MyDataType();)
     - N/A
     - Standalone diagnostic controls and evidence only; no Qore module/provider/API, sandbox operation, production loop or package behavior change.

   * - 33. Request/input types use public Fields (enables ClassName::Fields in action registration)
     - N/A
     - Standalone diagnostic controls and evidence only; no Qore module/provider/API, sandbox operation, production loop or package behavior change.

   * - 34. Response/output types use private Fields
     - N/A
     - Standalone diagnostic controls and evidence only; no Qore module/provider/API, sandbox operation, production loop or package behavior change.

   * - 35. Each field in data types has display_name, type, and desc (markdown-formatted)
     - N/A
     - Standalone diagnostic controls and evidence only; no Qore module/provider/API, sandbox operation, production loop or package behavior change.

   * - 36. Input fields have example_value where useful (string fields, endpoint URIs, SQL queries, etc.)
     - N/A
     - Standalone diagnostic controls and evidence only; no Qore module/provider/API, sandbox operation, production loop or package behavior change.

   * - 37. Fields with finite allowed values use allowed_values with AllowedValueInfo containing both value and display_name (Title Case, human-readable) — never bare values, never described only in text
     - N/A
     - Standalone diagnostic controls and evidence only; no Qore module/provider/API, sandbox operation, production loop or package behavior change.

   * - 38. Password/secret fields have "sensitive": True
     - N/A
     - Standalone diagnostic controls and evidence only; no Qore module/provider/API, sandbox operation, production loop or package behavior change.

   * - 39. groups uses AppGroup enum values from qlib/DataProvider/AppGroup.qc
     - N/A
     - Standalone diagnostic controls and evidence only; no Qore module/provider/API, sandbox operation, production loop or package behavior change.

   * - 40. App logo stored as separate file, loaded at module level in Priv namespace
     - N/A
     - Standalone diagnostic controls and evidence only; no Qore module/provider/API, sandbox operation, production loop or package behavior change.

   * - 41. App desc uses markdown: bullet list of capabilities, links to project website, business-language explanation of value
     - N/A
     - Standalone diagnostic controls and evidence only; no Qore module/provider/API, sandbox operation, production loop or package behavior change.

   * - 42. display_name is user-friendly ("Apache Avro" not "avro")
     - N/A
     - Standalone diagnostic controls and evidence only; no Qore module/provider/API, sandbox operation, production loop or package behavior change.

   * - 43. short_desc is plain text, under 80 chars, single sentence — no markdown
     - N/A
     - Standalone diagnostic controls and evidence only; no Qore module/provider/API, sandbox operation, production loop or package behavior change.

   * - 44. desc uses markdown: backticks for code/field refs ( field_name ,  True ,  pdf ), \n\n for paragraphs, -  bullet lists for enumerations, bold for caveats
     - N/A
     - Standalone diagnostic controls and evidence only; no Qore module/provider/API, sandbox operation, production loop or package behavior change.

   * - 45. Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use"
     - N/A
     - Standalone diagnostic controls and evidence only; no Qore module/provider/API, sandbox operation, production loop or package behavior change.

   * - 46. No bare True/False/NOTHING — must be backtick-wrapped in desc
     - N/A
     - Standalone diagnostic controls and evidence only; no Qore module/provider/API, sandbox operation, production loop or package behavior change.

   * - 47. No bare field/option names in prose — must use backticks
     - N/A
     - Standalone diagnostic controls and evidence only; no Qore module/provider/API, sandbox operation, production loop or package behavior change.

   * - 48. Long descriptions (>500 chars) use bold section headers and bullet lists
     - N/A
     - Standalone diagnostic controls and evidence only; no Qore module/provider/API, sandbox operation, production loop or package behavior change.

   * - 49. Factory registration in Qore repo: every factory name registered in qlib/DataProvider/DataProvider.qc → FactoryMap (without this, module loads but doesn't appear in Qorus apps)
     - N/A
     - Standalone diagnostic controls and evidence only; no Qore module/provider/API, sandbox operation, production loop or package behavior change.

   * - 50. getRecordTypeImpl() signature: must be private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options) — NOT returning *AbstractDataProviderType
     - N/A
     - Standalone diagnostic controls and evidence only; no Qore module/provider/API, sandbox operation, production loop or package behavior change.

   * - 51. Dependency JARs committed (for JNI modules): JAR files in qlib/*/jar/ may be gitignored — use git add -f to ensure they're tracked, otherwise CI compilation fails
     - N/A
     - Standalone diagnostic controls and evidence only; no Qore module/provider/API, sandbox operation, production loop or package behavior change.

   * - 52. JAR install rules in CMakeLists.txt for all dependency JARs
     - N/A
     - Standalone diagnostic controls and evidence only; no Qore module/provider/API, sandbox operation, production loop or package behavior change.

   * - 53. No workarounds: No TODOs, FIXMEs, stubs, or partially-implemented features
     - Pass
     - User approved the exact GCC 14 vector-copy warning and six GCC 16/Valgrind padding-comparison sites; no production workaround or broad suppression.

   * - 54. Exception safety: C++ uses ReferenceHolder for Qore allocations, std::unique_ptr for C++ allocations, *xsink checked after every fallible operation
     - Pass
     - Control allocations use std::vector and std::unique_ptr; exception unwinding frees owned data.

   * - 55. Thread safety: All mutable shared state protected by std::lock_guard<std::mutex> or documented as immutable-after-construction
     - Pass
     - Both controls are single-threaded and use local data only.

   * - 56. Type safety: Strongly-typed code<return(args)> instead of untyped code; static_cast instead of C casts; typed hashdecls for results; enums where appropriate
     - Pass
     - Fixed-width integer fields and explicit casts reproduce the reviewed layouts; char aliasing is used only to mark padding undefined for Memcheck.

   * - 57. Performance: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply
     - Pass
     - Fixed iteration counts exercise repeatability and lifetime cleanup; no production path is added.

   * - 58. Error handling: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable
     - Pass
     - Assertions validate all vector entries, boundary/sentinel state and zero/nonzero reference comparisons.

   * - 59. Documentation: Doxygen @param, @return, @throw on all public methods; @par Example with realistic business scenarios; @note for important caveats
     - Pass
     - Evidence describes the exact root causes, mathematical comparison proof, acceptance scope and excluded real native leaks.

   * - 60. QPP flags: [flags=CONSTANT] on methods that never throw; [flags=RET_VALUE_ONLY] on methods that throw but have no side effects
     - N/A
     - Standalone diagnostic controls and evidence only; no Qore module/provider/API, sandbox operation, production loop or package behavior change.

   * - 61. Security: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code
     - Pass
     - No external input or credentials; bounded vectors and fixed-layout padding instrumentation.

   * - 62. Correctness: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features)
     - Pass
     - Recorded test source bytes equal the files being committed. GCC 14 control completes 10000 iterations with 2570002 allocations freed and zero Valgrind errors; GCC 16 is warning-free. Padding control verifies all branches and frees 301 allocations, reproducing only the approved diagnostic.
