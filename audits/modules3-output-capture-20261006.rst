Installed fixture output capture audit
======================================

Copyright 2026 Qore Technologies, s.r.o.

Scope: run_logged Python helper, its four regression tests and workflow documentation. Evidence: evidence/modules3-output-capture-20261006.json.

.. list-table:: Complete audit-changes checklist
   :header-rows: 1

   * - Check
     - Status
     - Evidence

   * - 1. Entry exists in doxygen/lang/120_modules.dox.tmpl (for modules in the Qore repo; N/A for external module repos)
     - N/A
     - Python fixture output capture only; no C++, Qore, QPP, DataProvider, module registration, JAR or concurrent runtime code changed.

   * - 2. Entry exists in doxygen/lang/900_release_notes.dox.tmpl (for modules in the Qore repo; external modules have release notes in their .qm)
     - N/A
     - Python fixture output capture only; no C++, Qore, QPP, DataProvider, module registration, JAR or concurrent runtime code changed.

   * - 3. qore_user_module() or qore_external_user_module() call in CMakeLists.txt
     - N/A
     - Python fixture output capture only; no C++, Qore, QPP, DataProvider, module registration, JAR or concurrent runtime code changed.

   * - 4. Module added to QMOD list in CMakeLists.txt
     - N/A
     - Python fixture output capture only; no C++, Qore, QPP, DataProvider, module registration, JAR or concurrent runtime code changed.

   * - 5. .qm file has @section <lowercasemodname>intro as first doc section — must be all lowercase (e.g., avrodataproviderintro, not AvroDataProviderintro)
     - N/A
     - Python fixture output capture only; no C++, Qore, QPP, DataProvider, module registration, JAR or concurrent runtime code changed.

   * - 6. %modern in .qm file — no redundant %new-style, %require-types, %strict-args, %enable-all-warnings
     - N/A
     - Python fixture output capture only; no C++, Qore, QPP, DataProvider, module registration, JAR or concurrent runtime code changed.

   * - 7. No parse directives (%requires, %modern, %new-style) in separated .qc files (check OUTSIDE of @code blocks only)
     - N/A
     - Python fixture output capture only; no C++, Qore, QPP, DataProvider, module registration, JAR or concurrent runtime code changed.

   * - 8. No %include usage (deprecated for modules)
     - N/A
     - Python fixture output capture only; no C++, Qore, QPP, DataProvider, module registration, JAR or concurrent runtime code changed.

   * - 9. Copyright 2026 on all new files
     - Pass
     - Copyright 2026 retained.

   * - 10. Directory layout: .qm inside qlib/<ModuleName>/ directory (not at qlib/<ModuleName>.qm for multi-file modules)
     - N/A
     - Python fixture output capture only; no C++, Qore, QPP, DataProvider, module registration, JAR or concurrent runtime code changed.

   * - 11. No second .qm for the same module at qlib/<ModuleName>.qm
     - N/A
     - Python fixture output capture only; no C++, Qore, QPP, DataProvider, module registration, JAR or concurrent runtime code changed.

   * - 12. ns=Qore::XX matches the QoreNamespace constructor path
     - N/A
     - Python fixture output capture only; no C++, Qore, QPP, DataProvider, module registration, JAR or concurrent runtime code changed.

   * - 13. %modern directive present
     - N/A
     - Python fixture output capture only; no C++, Qore, QPP, DataProvider, module registration, JAR or concurrent runtime code changed.

   * - 14. Executable permission set (chmod +x)
     - N/A
     - Python fixture output capture only; no C++, Qore, QPP, DataProvider, module registration, JAR or concurrent runtime code changed.

   * - 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus)
     - N/A
     - Python fixture output capture only; no C++, Qore, QPP, DataProvider, module registration, JAR or concurrent runtime code changed.

   * - 16. External module dependencies use %try-module — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard %requires
     - N/A
     - Python fixture output capture only; no C++, Qore, QPP, DataProvider, module registration, JAR or concurrent runtime code changed.

   * - 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks
     - N/A
     - Python fixture output capture only; no C++, Qore, QPP, DataProvider, module registration, JAR or concurrent runtime code changed.

   * - 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks
     - N/A
     - Python fixture output capture only; no C++, Qore, QPP, DataProvider, module registration, JAR or concurrent runtime code changed.

   * - 19. If filesystem/network ops exist, verify QoreSandboxManagerHelper usage
     - N/A
     - Python fixture output capture only; no C++, Qore, QPP, DataProvider, module registration, JAR or concurrent runtime code changed.

   * - 20. No File::, Dir::, Socket::, HTTPClient:: usage without justification
     - N/A
     - Python fixture output capture only; no C++, Qore, QPP, DataProvider, module registration, JAR or concurrent runtime code changed.

   * - 21. All for/while loops that could iterate >100 times have qore_check_cancel() checks
     - N/A
     - Python fixture output capture only; no C++, Qore, QPP, DataProvider, module registration, JAR or concurrent runtime code changed.

   * - 22. Uses qore_check_cancel() (NOT deprecated qore_check_io_interrupt())
     - N/A
     - Python fixture output capture only; no C++, Qore, QPP, DataProvider, module registration, JAR or concurrent runtime code changed.

   * - 23. Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations
     - N/A
     - Python fixture output capture only; no C++, Qore, QPP, DataProvider, module registration, JAR or concurrent runtime code changed.

   * - 24. No blocking operations without cancellation support
     - N/A
     - Python fixture output capture only; no C++, Qore, QPP, DataProvider, module registration, JAR or concurrent runtime code changed.

   * - 25. Every action has display_name, short_desc (plain text, <80 chars), desc (markdown)
     - N/A
     - Python fixture output capture only; no C++, Qore, QPP, DataProvider, module registration, JAR or concurrent runtime code changed.

   * - 26. Every action has options populated via getActionOptionFromFields() — without this, the action shows an empty, unusable form
     - N/A
     - Python fixture output capture only; no C++, Qore, QPP, DataProvider, module registration, JAR or concurrent runtime code changed.

   * - 27. Every action has output_type set to a typed data type constant (e.g., MyResponseDataType) — not omitted
     - N/A
     - Python fixture output capture only; no C++, Qore, QPP, DataProvider, module registration, JAR or concurrent runtime code changed.

   * - 28. DPAT_API actions: provider has "supports_request": True and implements doRequestImpl()
     - N/A
     - Python fixture output capture only; no C++, Qore, QPP, DataProvider, module registration, JAR or concurrent runtime code changed.

   * - 29. DPAT_FIND actions: every option exists in SearchOptions, getRecordTypeImpl() returns *hash<string, AbstractDataField>
     - N/A
     - Python fixture output capture only; no C++, Qore, QPP, DataProvider, module registration, JAR or concurrent runtime code changed.

   * - 30. Scheme-based apps (with "scheme" in registerApp): actions use "path" and do NOT use "cls" — having both scheme and cls causes a runtime error
     - N/A
     - Python fixture output capture only; no C++, Qore, QPP, DataProvider, module registration, JAR or concurrent runtime code changed.

   * - 31. Single-key hash slices use trailing comma: Fields{"key",} (without trailing comma, Fields{"key"} returns the value, not a hash)
     - N/A
     - Python fixture output capture only; no C++, Qore, QPP, DataProvider, module registration, JAR or concurrent runtime code changed.

   * - 32. Typed data type classes exist for request and response types — inherit HashDataType, have const Fields hash, call addQoreFields(Fields) in constructor, export public constant at bottom (e.g., public const MyDataType = new MyDataType();)
     - N/A
     - Python fixture output capture only; no C++, Qore, QPP, DataProvider, module registration, JAR or concurrent runtime code changed.

   * - 33. Request/input types use public Fields (enables ClassName::Fields in action registration)
     - N/A
     - Python fixture output capture only; no C++, Qore, QPP, DataProvider, module registration, JAR or concurrent runtime code changed.

   * - 34. Response/output types use private Fields
     - N/A
     - Python fixture output capture only; no C++, Qore, QPP, DataProvider, module registration, JAR or concurrent runtime code changed.

   * - 35. Each field in data types has display_name, type, and desc (markdown-formatted)
     - N/A
     - Python fixture output capture only; no C++, Qore, QPP, DataProvider, module registration, JAR or concurrent runtime code changed.

   * - 36. Input fields have example_value where useful (string fields, endpoint URIs, SQL queries, etc.)
     - N/A
     - Python fixture output capture only; no C++, Qore, QPP, DataProvider, module registration, JAR or concurrent runtime code changed.

   * - 37. Fields with finite allowed values use allowed_values with AllowedValueInfo containing both value and display_name (Title Case, human-readable) — never bare values, never described only in text
     - N/A
     - Python fixture output capture only; no C++, Qore, QPP, DataProvider, module registration, JAR or concurrent runtime code changed.

   * - 38. Password/secret fields have "sensitive": True
     - N/A
     - Python fixture output capture only; no C++, Qore, QPP, DataProvider, module registration, JAR or concurrent runtime code changed.

   * - 39. groups uses AppGroup enum values from qlib/DataProvider/AppGroup.qc
     - N/A
     - Python fixture output capture only; no C++, Qore, QPP, DataProvider, module registration, JAR or concurrent runtime code changed.

   * - 40. App logo stored as separate file, loaded at module level in Priv namespace
     - N/A
     - Python fixture output capture only; no C++, Qore, QPP, DataProvider, module registration, JAR or concurrent runtime code changed.

   * - 41. App desc uses markdown: bullet list of capabilities, links to project website, business-language explanation of value
     - N/A
     - Python fixture output capture only; no C++, Qore, QPP, DataProvider, module registration, JAR or concurrent runtime code changed.

   * - 42. display_name is user-friendly ("Apache Avro" not "avro")
     - N/A
     - Python fixture output capture only; no C++, Qore, QPP, DataProvider, module registration, JAR or concurrent runtime code changed.

   * - 43. short_desc is plain text, under 80 chars, single sentence — no markdown
     - N/A
     - Python fixture output capture only; no C++, Qore, QPP, DataProvider, module registration, JAR or concurrent runtime code changed.

   * - 44. desc uses markdown: backticks for code/field refs ( field_name ,  True ,  pdf ), \n\n for paragraphs, -  bullet lists for enumerations, bold for caveats
     - N/A
     - Python fixture output capture only; no C++, Qore, QPP, DataProvider, module registration, JAR or concurrent runtime code changed.

   * - 45. Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use"
     - N/A
     - Python fixture output capture only; no C++, Qore, QPP, DataProvider, module registration, JAR or concurrent runtime code changed.

   * - 46. No bare True/False/NOTHING — must be backtick-wrapped in desc
     - N/A
     - Python fixture output capture only; no C++, Qore, QPP, DataProvider, module registration, JAR or concurrent runtime code changed.

   * - 47. No bare field/option names in prose — must use backticks
     - N/A
     - Python fixture output capture only; no C++, Qore, QPP, DataProvider, module registration, JAR or concurrent runtime code changed.

   * - 48. Long descriptions (>500 chars) use bold section headers and bullet lists
     - N/A
     - Python fixture output capture only; no C++, Qore, QPP, DataProvider, module registration, JAR or concurrent runtime code changed.

   * - 49. Factory registration in Qore repo: every factory name registered in qlib/DataProvider/DataProvider.qc → FactoryMap (without this, module loads but doesn't appear in Qorus apps)
     - N/A
     - Python fixture output capture only; no C++, Qore, QPP, DataProvider, module registration, JAR or concurrent runtime code changed.

   * - 50. getRecordTypeImpl() signature: must be private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options) — NOT returning *AbstractDataProviderType
     - N/A
     - Python fixture output capture only; no C++, Qore, QPP, DataProvider, module registration, JAR or concurrent runtime code changed.

   * - 51. Dependency JARs committed (for JNI modules): JAR files in qlib/*/jar/ may be gitignored — use git add -f to ensure they're tracked, otherwise CI compilation fails
     - N/A
     - Python fixture output capture only; no C++, Qore, QPP, DataProvider, module registration, JAR or concurrent runtime code changed.

   * - 52. JAR install rules in CMakeLists.txt for all dependency JARs
     - N/A
     - Python fixture output capture only; no C++, Qore, QPP, DataProvider, module registration, JAR or concurrent runtime code changed.

   * - 53. No workarounds: No TODOs, FIXMEs, stubs, or partially-implemented features
     - Pass
     - Root cause fixed in fixture descriptor ownership; no skipped tests or changed package behavior.

   * - 54. Exception safety: C++ uses ReferenceHolder for Qore allocations, std::unique_ptr for C++ allocations, *xsink checked after every fallible operation
     - Pass
     - Pipe descriptors close on ownership/Popen failure; log-copy failures terminate and reap the child; negative tests verify no leaked descriptors.

   * - 55. Thread safety: All mutable shared state protected by std::lock_guard<std::mutex> or documented as immutable-after-construction
     - N/A
     - Python fixture output capture only; no C++, Qore, QPP, DataProvider, module registration, JAR or concurrent runtime code changed.

   * - 56. Type safety: Strongly-typed code<return(args)> instead of untyped code; static_cast instead of C casts; typed hashdecls for results; enums where appropriate
     - Pass
     - Explicit optional uid/gid tuple and fixed argument lists.

   * - 57. Performance: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply
     - Pass
     - Streamed copying bounds memory regardless of log size; 1 MiB control passes.

   * - 58. Error handling: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable
     - Pass
     - Failed fixture exit status retained; ownership, launch and output errors propagate with cleanup.

   * - 59. Documentation: Doxygen @param, @return, @throw on all public methods; @par Example with realistic business scenarios; @note for important caveats
     - Pass
     - Workflow and helper docstring explain descriptor ownership and streaming.

   * - 60. QPP flags: [flags=CONSTANT] on methods that never throw; [flags=RET_VALUE_ONLY] on methods that throw but have no side effects
     - N/A
     - Python fixture output capture only; no C++, Qore, QPP, DataProvider, module registration, JAR or concurrent runtime code changed.

   * - 61. Security: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code
     - Pass
     - Only the fixture pipe is owned by its test user; artifact log stays private to the runner. No shell evaluation introduced.

   * - 62. Correctness: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features)
     - Pass
     - 156 unit tests and 11 ncurses suites pass, including both real stdout redirection cases with complete ordered logs.
