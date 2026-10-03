Leap debugedit backport audit
=============================

Copyright 2026 Qore Technologies, s.r.o.

Scope: debugedit 5.1 distribution recipe, verified upstream source/signature and six unchanged openSUSE integration patches. No Qore or module implementation is changed.

.. list-table:: Complete audit-changes checklist
   :header-rows: 1

   * - Check
     - Status
     - Evidence

   * - 1. Entry exists in doxygen/lang/120_modules.dox.tmpl (for modules in the Qore repo; N/A for external module repos)
     - N/A
     - No Qore API, module, data-provider or QPP changes in this build-tool backport.

   * - 2. Entry exists in doxygen/lang/900_release_notes.dox.tmpl (for modules in the Qore repo; external modules have release notes in their .qm)
     - N/A
     - No Qore API, module, data-provider or QPP changes in this build-tool backport.

   * - 3. qore_user_module() or qore_external_user_module() call in CMakeLists.txt
     - N/A
     - No Qore API, module, data-provider or QPP changes in this build-tool backport.

   * - 4. Module added to QMOD list in CMakeLists.txt
     - N/A
     - No Qore API, module, data-provider or QPP changes in this build-tool backport.

   * - 5. .qm file has @section <lowercasemodname>intro as first doc section — must be all lowercase (e.g., avrodataproviderintro, not AvroDataProviderintro)
     - N/A
     - No Qore API, module, data-provider or QPP changes in this build-tool backport.

   * - 6. %modern in .qm file — no redundant %new-style, %require-types, %strict-args, %enable-all-warnings
     - N/A
     - No Qore API, module, data-provider or QPP changes in this build-tool backport.

   * - 7. No parse directives (%requires, %modern, %new-style) in separated .qc files (check OUTSIDE of @code blocks only)
     - N/A
     - No Qore API, module, data-provider or QPP changes in this build-tool backport.

   * - 8. No %include usage (deprecated for modules)
     - N/A
     - No Qore API, module, data-provider or QPP changes in this build-tool backport.

   * - 9. Copyright 2026 on all new files
     - Pass
     - Backport recipe, evidence and qualification controls identify 2026.

   * - 10. Directory layout: .qm inside qlib/<ModuleName>/ directory (not at qlib/<ModuleName>.qm for multi-file modules)
     - N/A
     - No Qore API, module, data-provider or QPP changes in this build-tool backport.

   * - 11. No second .qm for the same module at qlib/<ModuleName>.qm
     - N/A
     - No Qore API, module, data-provider or QPP changes in this build-tool backport.

   * - 12. ns=Qore::XX matches the QoreNamespace constructor path
     - N/A
     - No Qore API, module, data-provider or QPP changes in this build-tool backport.

   * - 13. %modern directive present
     - N/A
     - No Qore API, module, data-provider or QPP changes in this build-tool backport.

   * - 14. Executable permission set (chmod +x)
     - N/A
     - No Qore API, module, data-provider or QPP changes in this build-tool backport.

   * - 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus)
     - N/A
     - No Qore API, module, data-provider or QPP changes in this build-tool backport.

   * - 16. External module dependencies use %try-module — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard %requires
     - N/A
     - No Qore API, module, data-provider or QPP changes in this build-tool backport.

   * - 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks
     - N/A
     - No Qore API, module, data-provider or QPP changes in this build-tool backport.

   * - 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks
     - N/A
     - No Qore API, module, data-provider or QPP changes in this build-tool backport.

   * - 19. If filesystem/network ops exist, verify QoreSandboxManagerHelper usage
     - N/A
     - No Qore API, module, data-provider or QPP changes in this build-tool backport.

   * - 20. No File::, Dir::, Socket::, HTTPClient:: usage without justification
     - N/A
     - No Qore API, module, data-provider or QPP changes in this build-tool backport.

   * - 21. All for/while loops that could iterate >100 times have qore_check_cancel() checks
     - N/A
     - No Qore API, module, data-provider or QPP changes in this build-tool backport.

   * - 22. Uses qore_check_cancel() (NOT deprecated qore_check_io_interrupt())
     - N/A
     - No Qore API, module, data-provider or QPP changes in this build-tool backport.

   * - 23. Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations
     - N/A
     - No Qore API, module, data-provider or QPP changes in this build-tool backport.

   * - 24. No blocking operations without cancellation support
     - N/A
     - No Qore API, module, data-provider or QPP changes in this build-tool backport.

   * - 25. Every action has display_name, short_desc (plain text, <80 chars), desc (markdown)
     - N/A
     - No Qore API, module, data-provider or QPP changes in this build-tool backport.

   * - 26. Every action has options populated via getActionOptionFromFields() — without this, the action shows an empty, unusable form
     - N/A
     - No Qore API, module, data-provider or QPP changes in this build-tool backport.

   * - 27. Every action has output_type set to a typed data type constant (e.g., MyResponseDataType) — not omitted
     - N/A
     - No Qore API, module, data-provider or QPP changes in this build-tool backport.

   * - 28. DPAT_API actions: provider has "supports_request": True and implements doRequestImpl()
     - N/A
     - No Qore API, module, data-provider or QPP changes in this build-tool backport.

   * - 29. DPAT_FIND actions: every option exists in SearchOptions, getRecordTypeImpl() returns *hash<string, AbstractDataField>
     - N/A
     - No Qore API, module, data-provider or QPP changes in this build-tool backport.

   * - 30. Scheme-based apps (with "scheme" in registerApp): actions use "path" and do NOT use "cls" — having both scheme and cls causes a runtime error
     - N/A
     - No Qore API, module, data-provider or QPP changes in this build-tool backport.

   * - 31. Single-key hash slices use trailing comma: Fields{"key",} (without trailing comma, Fields{"key"} returns the value, not a hash)
     - N/A
     - No Qore API, module, data-provider or QPP changes in this build-tool backport.

   * - 32. Typed data type classes exist for request and response types — inherit HashDataType, have const Fields hash, call addQoreFields(Fields) in constructor, export public constant at bottom (e.g., public const MyDataType = new MyDataType();)
     - N/A
     - No Qore API, module, data-provider or QPP changes in this build-tool backport.

   * - 33. Request/input types use public Fields (enables ClassName::Fields in action registration)
     - N/A
     - No Qore API, module, data-provider or QPP changes in this build-tool backport.

   * - 34. Response/output types use private Fields
     - N/A
     - No Qore API, module, data-provider or QPP changes in this build-tool backport.

   * - 35. Each field in data types has display_name, type, and desc (markdown-formatted)
     - N/A
     - No Qore API, module, data-provider or QPP changes in this build-tool backport.

   * - 36. Input fields have example_value where useful (string fields, endpoint URIs, SQL queries, etc.)
     - N/A
     - No Qore API, module, data-provider or QPP changes in this build-tool backport.

   * - 37. Fields with finite allowed values use allowed_values with AllowedValueInfo containing both value and display_name (Title Case, human-readable) — never bare values, never described only in text
     - N/A
     - No Qore API, module, data-provider or QPP changes in this build-tool backport.

   * - 38. Password/secret fields have "sensitive": True
     - N/A
     - No Qore API, module, data-provider or QPP changes in this build-tool backport.

   * - 39. groups uses AppGroup enum values from qlib/DataProvider/AppGroup.qc
     - N/A
     - No Qore API, module, data-provider or QPP changes in this build-tool backport.

   * - 40. App logo stored as separate file, loaded at module level in Priv namespace
     - N/A
     - No Qore API, module, data-provider or QPP changes in this build-tool backport.

   * - 41. App desc uses markdown: bullet list of capabilities, links to project website, business-language explanation of value
     - N/A
     - No Qore API, module, data-provider or QPP changes in this build-tool backport.

   * - 42. display_name is user-friendly ("Apache Avro" not "avro")
     - N/A
     - No Qore API, module, data-provider or QPP changes in this build-tool backport.

   * - 43. short_desc is plain text, under 80 chars, single sentence — no markdown
     - N/A
     - No Qore API, module, data-provider or QPP changes in this build-tool backport.

   * - 44. desc uses markdown: backticks for code/field refs ( field_name ,  True ,  pdf ), \n\n for paragraphs, -  bullet lists for enumerations, bold for caveats
     - N/A
     - No Qore API, module, data-provider or QPP changes in this build-tool backport.

   * - 45. Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use"
     - N/A
     - No Qore API, module, data-provider or QPP changes in this build-tool backport.

   * - 46. No bare True/False/NOTHING — must be backtick-wrapped in desc
     - N/A
     - No Qore API, module, data-provider or QPP changes in this build-tool backport.

   * - 47. No bare field/option names in prose — must use backticks
     - N/A
     - No Qore API, module, data-provider or QPP changes in this build-tool backport.

   * - 48. Long descriptions (>500 chars) use bold section headers and bullet lists
     - N/A
     - No Qore API, module, data-provider or QPP changes in this build-tool backport.

   * - 49. Factory registration in Qore repo: every factory name registered in qlib/DataProvider/DataProvider.qc → FactoryMap (without this, module loads but doesn't appear in Qorus apps)
     - N/A
     - No Qore API, module, data-provider or QPP changes in this build-tool backport.

   * - 50. getRecordTypeImpl() signature: must be private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options) — NOT returning *AbstractDataProviderType
     - N/A
     - No Qore API, module, data-provider or QPP changes in this build-tool backport.

   * - 51. Dependency JARs committed (for JNI modules): JAR files in qlib/*/jar/ may be gitignored — use git add -f to ensure they're tracked, otherwise CI compilation fails
     - N/A
     - No Qore API, module, data-provider or QPP changes in this build-tool backport.

   * - 52. JAR install rules in CMakeLists.txt for all dependency JARs
     - N/A
     - No Qore API, module, data-provider or QPP changes in this build-tool backport.

   * - 53. No workarounds: No TODOs, FIXMEs, stubs, or partially-implemented features
     - Pass
     - Indexed DWARF support comes from upstream 5.1. No warning suppression or debug stripping bypass. The inherited hardlink patch is root-caused and tested for missing/empty match lists.

   * - 54. Exception safety: C++ uses ReferenceHolder for Qore allocations, std::unique_ptr for C++ allocations, *xsink checked after every fallible operation
     - Pass
     - No new native implementation; upstream indexed-DWARF control under Valgrind has all 417 allocations freed.

   * - 55. Thread safety: All mutable shared state protected by std::lock_guard<std::mutex> or documented as immutable-after-construction
     - Pass
     - Parallel debug extraction passes with in-root and outside-root hardlink fixtures; no new shared mutable state.

   * - 56. Type safety: Strongly-typed code<return(args)> instead of untyped code; static_cast instead of C casts; typed hashdecls for results; enums where appropriate
     - N/A
     - No Qore API, module, data-provider or QPP changes in this build-tool backport.

   * - 57. Performance: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply
     - Pass
     - No extra runtime cost to Qore; tool runs only while extracting package debug information.

   * - 58. Error handling: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable
     - Pass
     - Upstream 35 tests include malformed input; source, artifact and signature verification fail on mismatches. Installed controls assert helper outputs.

   * - 59. Documentation: Doxygen @param, @return, @throw on all public methods; @par Example with realistic business scenarios; @note for important caveats
     - Pass
     - README, changelog and evidence describe the dependency, cause, distribution provenance and qualification limits.

   * - 60. QPP flags: [flags=CONSTANT] on methods that never throw; [flags=RET_VALUE_ONLY] on methods that throw but have no side effects
     - N/A
     - No Qore API, module, data-provider or QPP changes in this build-tool backport.

   * - 61. Security: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code
     - Pass
     - Archive SHA256 and OBS source MD5 pins plus detached signature verification; private test network; PIE hardening; no credentials.

   * - 62. Correctness: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features)
     - Pass
     - 35 upstream tests, real mixed-DWARF control, native Valgrind, installed zero-warning lint, hardlink extraction, debug index and executable checks pass.
