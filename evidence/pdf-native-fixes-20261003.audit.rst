PDF ownership and build integration audit
=========================================

Copyright 2026 Qore Technologies, s.r.o.

Scope: module-pdf ownership fixes, regression tests, uninstall/CMake integration, release notes and bundled-library documentation. Source hashes/results: pdf-native-fixes-20261003.json. No new Qore module, QPP API, DataProvider registration or Java dependency.

.. list-table:: Complete audit-changes checklist
   :header-rows: 1

   * - Check
     - Status
     - Evidence

   * - 1. Entry exists in doxygen/lang/120_modules.dox.tmpl (for modules in the Qore repo; N/A for external module repos)
     - N/A
     - Not applicable: no new Qore module, QPP class/method, provider registration/field/type or Java dependency.

   * - 2. Entry exists in doxygen/lang/900_release_notes.dox.tmpl (for modules in the Qore repo; external modules have release notes in their .qm)
     - N/A
     - Not applicable: no new Qore module, QPP class/method, provider registration/field/type or Java dependency.

   * - 3. qore_user_module() or qore_external_user_module() call in CMakeLists.txt
     - N/A
     - Not applicable: no new Qore module, QPP class/method, provider registration/field/type or Java dependency.

   * - 4. Module added to QMOD list in CMakeLists.txt
     - N/A
     - Not applicable: no new Qore module, QPP class/method, provider registration/field/type or Java dependency.

   * - 5. .qm file has @section <lowercasemodname>intro as first doc section — must be all lowercase (e.g., avrodataproviderintro, not AvroDataProviderintro)
     - N/A
     - Not applicable: no new Qore module, QPP class/method, provider registration/field/type or Java dependency.

   * - 6. %modern in .qm file — no redundant %new-style, %require-types, %strict-args, %enable-all-warnings
     - N/A
     - Not applicable: no new Qore module, QPP class/method, provider registration/field/type or Java dependency.

   * - 7. No parse directives (%requires, %modern, %new-style) in separated .qc files (check OUTSIDE of @code blocks only)
     - N/A
     - Not applicable: no new Qore module, QPP class/method, provider registration/field/type or Java dependency.

   * - 8. No %include usage (deprecated for modules)
     - N/A
     - Not applicable: no new Qore module, QPP class/method, provider registration/field/type or Java dependency.

   * - 9. Copyright 2026 on all new files
     - Pass
     - New regression, uninstall template/test and CMake changes carry 2026 notices; third-party authors and terms retained.

   * - 10. Directory layout: .qm inside qlib/<ModuleName>/ directory (not at qlib/<ModuleName>.qm for multi-file modules)
     - N/A
     - Not applicable: no new Qore module, QPP class/method, provider registration/field/type or Java dependency.

   * - 11. No second .qm for the same module at qlib/<ModuleName>.qm
     - N/A
     - Not applicable: no new Qore module, QPP class/method, provider registration/field/type or Java dependency.

   * - 12. ns=Qore::XX matches the QoreNamespace constructor path
     - N/A
     - Not applicable: no new Qore module, QPP class/method, provider registration/field/type or Java dependency.

   * - 13. %modern directive present
     - Pass
     - test/pdf.qtest retains %modern.

   * - 14. Executable permission set (chmod +x)
     - Pass
     - test/pdf.qtest is executable (100755).

   * - 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus)
     - Pass
     - Local build/qlib paths precede %requires; qualification explicitly loads the rebuilt binary and AOT provider.

   * - 16. External module dependencies use %try-module — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard %requires
     - Pass
     - QUnit, Util and pdf are required core/own modules; no optional external module added.

   * - 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks
     - Pass
     - Input-read/output-write sandbox guards remain in split; no new I/O in serialization or owning-view conversion.

   * - 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks
     - Pass
     - No network operations added.

   * - 19. If filesystem/network ops exist, verify QoreSandboxManagerHelper usage
     - Pass
     - split retains QoreSandboxManagerHelper checks before processing input/output paths.

   * - 20. No File::, Dir::, Socket::, HTTPClient:: usage without justification
     - Pass
     - New fixtures use temporary directories and deliberately missing/conflicting paths; no runtime Qore I/O added.

   * - 21. All for/while loops that could iterate >100 times have qore_check_cancel() checks
     - Pass
     - split retains cancellation every page; the native reader regression has a small fixed one-page fixture.

   * - 22. Uses qore_check_cancel() (NOT deprecated qore_check_io_interrupt())
     - Pass
     - Uses qore_check_cancel, with no deprecated check introduced.

   * - 23. Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations
     - Pass
     - Existing per-page cancellation exceeds the required frequency.

   * - 24. No blocking operations without cancellation support
     - Pass
     - No new blocking operation; QPDF processing retains its entry/per-page cancellation checks.

   * - 25. Every action has display_name, short_desc (plain text, <80 chars), desc (markdown)
     - N/A
     - Not applicable: no new Qore module, QPP class/method, provider registration/field/type or Java dependency.

   * - 26. Every action has options populated via getActionOptionFromFields() — without this, the action shows an empty, unusable form
     - N/A
     - Not applicable: no new Qore module, QPP class/method, provider registration/field/type or Java dependency.

   * - 27. Every action has output_type set to a typed data type constant (e.g., MyResponseDataType) — not omitted
     - N/A
     - Not applicable: no new Qore module, QPP class/method, provider registration/field/type or Java dependency.

   * - 28. DPAT_API actions: provider has "supports_request": True and implements doRequestImpl()
     - N/A
     - Not applicable: no new Qore module, QPP class/method, provider registration/field/type or Java dependency.

   * - 29. DPAT_FIND actions: every option exists in SearchOptions, getRecordTypeImpl() returns *hash<string, AbstractDataField>
     - N/A
     - Not applicable: no new Qore module, QPP class/method, provider registration/field/type or Java dependency.

   * - 30. Scheme-based apps (with "scheme" in registerApp): actions use "path" and do NOT use "cls" — having both scheme and cls causes a runtime error
     - N/A
     - Not applicable: no new Qore module, QPP class/method, provider registration/field/type or Java dependency.

   * - 31. Single-key hash slices use trailing comma: Fields{"key",} (without trailing comma, Fields{"key"} returns the value, not a hash)
     - N/A
     - Not applicable: no new Qore module, QPP class/method, provider registration/field/type or Java dependency.

   * - 32. Typed data type classes exist for request and response types — inherit HashDataType, have const Fields hash, call addQoreFields(Fields) in constructor, export public constant at bottom (e.g., public const MyDataType = new MyDataType();)
     - N/A
     - Not applicable: no new Qore module, QPP class/method, provider registration/field/type or Java dependency.

   * - 33. Request/input types use public Fields (enables ClassName::Fields in action registration)
     - N/A
     - Not applicable: no new Qore module, QPP class/method, provider registration/field/type or Java dependency.

   * - 34. Response/output types use private Fields
     - N/A
     - Not applicable: no new Qore module, QPP class/method, provider registration/field/type or Java dependency.

   * - 35. Each field in data types has display_name, type, and desc (markdown-formatted)
     - N/A
     - Not applicable: no new Qore module, QPP class/method, provider registration/field/type or Java dependency.

   * - 36. Input fields have example_value where useful (string fields, endpoint URIs, SQL queries, etc.)
     - N/A
     - Not applicable: no new Qore module, QPP class/method, provider registration/field/type or Java dependency.

   * - 37. Fields with finite allowed values use allowed_values with AllowedValueInfo containing both value and display_name (Title Case, human-readable) — never bare values, never described only in text
     - N/A
     - Not applicable: no new Qore module, QPP class/method, provider registration/field/type or Java dependency.

   * - 38. Password/secret fields have "sensitive": True
     - N/A
     - Not applicable: no new Qore module, QPP class/method, provider registration/field/type or Java dependency.

   * - 39. groups uses AppGroup enum values from qlib/DataProvider/AppGroup.qc
     - N/A
     - Not applicable: no new Qore module, QPP class/method, provider registration/field/type or Java dependency.

   * - 40. App logo stored as separate file, loaded at module level in Priv namespace
     - N/A
     - Not applicable: no new Qore module, QPP class/method, provider registration/field/type or Java dependency.

   * - 41. App desc uses markdown: bullet list of capabilities, links to project website, business-language explanation of value
     - N/A
     - Not applicable: no new Qore module, QPP class/method, provider registration/field/type or Java dependency.

   * - 42. display_name is user-friendly ("Apache Avro" not "avro")
     - N/A
     - Not applicable: no new Qore module, QPP class/method, provider registration/field/type or Java dependency.

   * - 43. short_desc is plain text, under 80 chars, single sentence — no markdown
     - N/A
     - Not applicable: no new Qore module, QPP class/method, provider registration/field/type or Java dependency.

   * - 44. desc uses markdown: backticks for code/field refs ( field_name ,  True ,  pdf ), \n\n for paragraphs, -  bullet lists for enumerations, bold for caveats
     - N/A
     - Not applicable: no new Qore module, QPP class/method, provider registration/field/type or Java dependency.

   * - 45. Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use"
     - N/A
     - Not applicable: no new Qore module, QPP class/method, provider registration/field/type or Java dependency.

   * - 46. No bare True/False/NOTHING — must be backtick-wrapped in desc
     - N/A
     - Not applicable: no new Qore module, QPP class/method, provider registration/field/type or Java dependency.

   * - 47. No bare field/option names in prose — must use backticks
     - N/A
     - Not applicable: no new Qore module, QPP class/method, provider registration/field/type or Java dependency.

   * - 48. Long descriptions (>500 chars) use bold section headers and bullet lists
     - N/A
     - Not applicable: no new Qore module, QPP class/method, provider registration/field/type or Java dependency.

   * - 49. Factory registration in Qore repo: every factory name registered in qlib/DataProvider/DataProvider.qc → FactoryMap (without this, module loads but doesn't appear in Qorus apps)
     - N/A
     - Not applicable: no new Qore module, QPP class/method, provider registration/field/type or Java dependency.

   * - 50. getRecordTypeImpl() signature: must be private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options) — NOT returning *AbstractDataProviderType
     - N/A
     - Not applicable: no new Qore module, QPP class/method, provider registration/field/type or Java dependency.

   * - 51. Dependency JARs committed (for JNI modules): JAR files in qlib/*/jar/ may be gitignored — use git add -f to ensure they're tracked, otherwise CI compilation fails
     - N/A
     - Not applicable: no new Qore module, QPP class/method, provider registration/field/type or Java dependency.

   * - 52. JAR install rules in CMakeLists.txt for all dependency JARs
     - N/A
     - Not applicable: no new Qore module, QPP class/method, provider registration/field/type or Java dependency.

   * - 53. No workarounds: No TODOs, FIXMEs, stubs, or partially-implemented features
     - Pass
     - Ownership root causes are fixed without suppression or relaxed thresholds. External compiler/Valgrind sites have explicit approval in linked evidence.

   * - 54. Exception safety: C++ uses ReferenceHolder for Qore allocations, std::unique_ptr for C++ allocations, *xsink checked after every fallible operation
     - Pass
     - QPDF output uses its shared owner; ReferenceHolder retains the result list until success and checks the sink after push. Failure regressions and native Valgrind controls pass.

   * - 55. Thread safety: All mutable shared state protected by std::lock_guard<std::mutex> or documented as immutable-after-construction
     - Pass
     - No shared mutable state added; ownership is local or standard shared_ptr reference counting. Existing reader access lifetime rules remain.

   * - 56. Type safety: Strongly-typed code<return(args)> instead of untyped code; static_cast instead of C casts; typed hashdecls for results; enums where appropriate
     - Pass
     - Typed list<string>, typed closures and a standard const shared_ptr conversion replace the invalid cast.

   * - 57. Performance: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply
     - Pass
     - No new nested production loops or buffer copies. One shared_ptr reference increment retains the returned object.

   * - 58. Error handling: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable
     - Pass
     - Missing-input/output and partial split failures clean the result while retaining the original exception; no-renderer negative calls execute through assertThrows.

   * - 59. Documentation: Doxygen @param, @return, @throw on all public methods; @par Example with realistic business scenarios; @note for important caveats
     - Pass
     - Release notes record the three fixes; THIRD_PARTY explains the owning-view contract/regression. No new Qore public method.

   * - 60. QPP flags: [flags=CONSTANT] on methods that never throw; [flags=RET_VALUE_ONLY] on methods that throw but have no side effects
     - N/A
     - Not applicable: no new Qore module, QPP class/method, provider registration/field/type or Java dependency.

   * - 61. Security: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code
     - Pass
     - Sandbox and cancellation guards retained; uninstall rejects relative paths/directories before deletion and does not follow symlink targets.

   * - 62. Correctness: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features)
     - Pass
     - 79 cases/616 assertions pass on each distribution; all seven suites have zero lost allocations. Native controls, no-renderer build, 4 uninstall and 5 metadata tests pass.
