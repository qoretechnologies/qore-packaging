FreeTDS qualification evidence audit
====================================

Copyright 2026 Qore Technologies, s.r.o.

Scope: catalog pin, rollout status, OBS package metadata and qualification evidence only. The module implementation, recipe and fixture audits are recorded separately in freetds-doc-audit-20261002.rst and freetds-rpm-audit-20261002.rst.

.. list-table:: Complete audit-changes checklist
   :header-rows: 1

   * - Check
     - Status
     - Evidence

   * - 1. Entry exists in doxygen/lang/120_modules.dox.tmpl (for modules in the Qore repo; N/A for external module repos)
     - N/A
     - Not applicable to declarative metadata/evidence; no Qore, C++, provider, test implementation or public API changes in this scoped update.

   * - 2. Entry exists in doxygen/lang/900_release_notes.dox.tmpl (for modules in the Qore repo; external modules have release notes in their .qm)
     - N/A
     - Not applicable to declarative metadata/evidence; no Qore, C++, provider, test implementation or public API changes in this scoped update.

   * - 3. qore_user_module() or qore_external_user_module() call in CMakeLists.txt
     - N/A
     - Not applicable to declarative metadata/evidence; no Qore, C++, provider, test implementation or public API changes in this scoped update.

   * - 4. Module added to QMOD list in CMakeLists.txt
     - N/A
     - Not applicable to declarative metadata/evidence; no Qore, C++, provider, test implementation or public API changes in this scoped update.

   * - 5. .qm file has @section <lowercasemodname>intro as first doc section — must be all lowercase (e.g., avrodataproviderintro, not AvroDataProviderintro)
     - N/A
     - Not applicable to declarative metadata/evidence; no Qore, C++, provider, test implementation or public API changes in this scoped update.

   * - 6. %modern in .qm file — no redundant %new-style, %require-types, %strict-args, %enable-all-warnings
     - N/A
     - Not applicable to declarative metadata/evidence; no Qore, C++, provider, test implementation or public API changes in this scoped update.

   * - 7. No parse directives (%requires, %modern, %new-style) in separated .qc files (check OUTSIDE of @code blocks only)
     - N/A
     - Not applicable to declarative metadata/evidence; no Qore, C++, provider, test implementation or public API changes in this scoped update.

   * - 8. No %include usage (deprecated for modules)
     - N/A
     - Not applicable to declarative metadata/evidence; no Qore, C++, provider, test implementation or public API changes in this scoped update.

   * - 9. Copyright 2026 on all new files
     - Pass
     - All new evidence and metadata carry 2026 copyright.

   * - 10. Directory layout: .qm inside qlib/<ModuleName>/ directory (not at qlib/<ModuleName>.qm for multi-file modules)
     - N/A
     - Not applicable to declarative metadata/evidence; no Qore, C++, provider, test implementation or public API changes in this scoped update.

   * - 11. No second .qm for the same module at qlib/<ModuleName>.qm
     - N/A
     - Not applicable to declarative metadata/evidence; no Qore, C++, provider, test implementation or public API changes in this scoped update.

   * - 12. ns=Qore::XX matches the QoreNamespace constructor path
     - N/A
     - Not applicable to declarative metadata/evidence; no Qore, C++, provider, test implementation or public API changes in this scoped update.

   * - 13. %modern directive present
     - N/A
     - Not applicable to declarative metadata/evidence; no Qore, C++, provider, test implementation or public API changes in this scoped update.

   * - 14. Executable permission set (chmod +x)
     - N/A
     - Not applicable to declarative metadata/evidence; no Qore, C++, provider, test implementation or public API changes in this scoped update.

   * - 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus)
     - N/A
     - Not applicable to declarative metadata/evidence; no Qore, C++, provider, test implementation or public API changes in this scoped update.

   * - 16. External module dependencies use %try-module — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard %requires
     - N/A
     - Not applicable to declarative metadata/evidence; no Qore, C++, provider, test implementation or public API changes in this scoped update.

   * - 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks
     - N/A
     - Not applicable to declarative metadata/evidence; no Qore, C++, provider, test implementation or public API changes in this scoped update.

   * - 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks
     - N/A
     - Not applicable to declarative metadata/evidence; no Qore, C++, provider, test implementation or public API changes in this scoped update.

   * - 19. If filesystem/network ops exist, verify QoreSandboxManagerHelper usage
     - N/A
     - Not applicable to declarative metadata/evidence; no Qore, C++, provider, test implementation or public API changes in this scoped update.

   * - 20. No File::, Dir::, Socket::, HTTPClient:: usage without justification
     - N/A
     - Not applicable to declarative metadata/evidence; no Qore, C++, provider, test implementation or public API changes in this scoped update.

   * - 21. All for/while loops that could iterate >100 times have qore_check_cancel() checks
     - N/A
     - Not applicable to declarative metadata/evidence; no Qore, C++, provider, test implementation or public API changes in this scoped update.

   * - 22. Uses qore_check_cancel() (NOT deprecated qore_check_io_interrupt())
     - N/A
     - Not applicable to declarative metadata/evidence; no Qore, C++, provider, test implementation or public API changes in this scoped update.

   * - 23. Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations
     - N/A
     - Not applicable to declarative metadata/evidence; no Qore, C++, provider, test implementation or public API changes in this scoped update.

   * - 24. No blocking operations without cancellation support
     - N/A
     - Not applicable to declarative metadata/evidence; no Qore, C++, provider, test implementation or public API changes in this scoped update.

   * - 25. Every action has display_name, short_desc (plain text, <80 chars), desc (markdown)
     - N/A
     - Not applicable to declarative metadata/evidence; no Qore, C++, provider, test implementation or public API changes in this scoped update.

   * - 26. Every action has options populated via getActionOptionFromFields() — without this, the action shows an empty, unusable form
     - N/A
     - Not applicable to declarative metadata/evidence; no Qore, C++, provider, test implementation or public API changes in this scoped update.

   * - 27. Every action has output_type set to a typed data type constant (e.g., MyResponseDataType) — not omitted
     - N/A
     - Not applicable to declarative metadata/evidence; no Qore, C++, provider, test implementation or public API changes in this scoped update.

   * - 28. DPAT_API actions: provider has "supports_request": True and implements doRequestImpl()
     - N/A
     - Not applicable to declarative metadata/evidence; no Qore, C++, provider, test implementation or public API changes in this scoped update.

   * - 29. DPAT_FIND actions: every option exists in SearchOptions, getRecordTypeImpl() returns *hash<string, AbstractDataField>
     - N/A
     - Not applicable to declarative metadata/evidence; no Qore, C++, provider, test implementation or public API changes in this scoped update.

   * - 30. Scheme-based apps (with "scheme" in registerApp): actions use "path" and do NOT use "cls" — having both scheme and cls causes a runtime error
     - N/A
     - Not applicable to declarative metadata/evidence; no Qore, C++, provider, test implementation or public API changes in this scoped update.

   * - 31. Single-key hash slices use trailing comma: Fields{"key",} (without trailing comma, Fields{"key"} returns the value, not a hash)
     - N/A
     - Not applicable to declarative metadata/evidence; no Qore, C++, provider, test implementation or public API changes in this scoped update.

   * - 32. Typed data type classes exist for request and response types — inherit HashDataType, have const Fields hash, call addQoreFields(Fields) in constructor, export public constant at bottom (e.g., public const MyDataType = new MyDataType();)
     - N/A
     - Not applicable to declarative metadata/evidence; no Qore, C++, provider, test implementation or public API changes in this scoped update.

   * - 33. Request/input types use public Fields (enables ClassName::Fields in action registration)
     - N/A
     - Not applicable to declarative metadata/evidence; no Qore, C++, provider, test implementation or public API changes in this scoped update.

   * - 34. Response/output types use private Fields
     - N/A
     - Not applicable to declarative metadata/evidence; no Qore, C++, provider, test implementation or public API changes in this scoped update.

   * - 35. Each field in data types has display_name, type, and desc (markdown-formatted)
     - N/A
     - Not applicable to declarative metadata/evidence; no Qore, C++, provider, test implementation or public API changes in this scoped update.

   * - 36. Input fields have example_value where useful (string fields, endpoint URIs, SQL queries, etc.)
     - N/A
     - Not applicable to declarative metadata/evidence; no Qore, C++, provider, test implementation or public API changes in this scoped update.

   * - 37. Fields with finite allowed values use allowed_values with AllowedValueInfo containing both value and display_name (Title Case, human-readable) — never bare values, never described only in text
     - N/A
     - Not applicable to declarative metadata/evidence; no Qore, C++, provider, test implementation or public API changes in this scoped update.

   * - 38. Password/secret fields have "sensitive": True
     - N/A
     - Not applicable to declarative metadata/evidence; no Qore, C++, provider, test implementation or public API changes in this scoped update.

   * - 39. groups uses AppGroup enum values from qlib/DataProvider/AppGroup.qc
     - N/A
     - Not applicable to declarative metadata/evidence; no Qore, C++, provider, test implementation or public API changes in this scoped update.

   * - 40. App logo stored as separate file, loaded at module level in Priv namespace
     - N/A
     - Not applicable to declarative metadata/evidence; no Qore, C++, provider, test implementation or public API changes in this scoped update.

   * - 41. App desc uses markdown: bullet list of capabilities, links to project website, business-language explanation of value
     - N/A
     - Not applicable to declarative metadata/evidence; no Qore, C++, provider, test implementation or public API changes in this scoped update.

   * - 42. display_name is user-friendly ("Apache Avro" not "avro")
     - N/A
     - Not applicable to declarative metadata/evidence; no Qore, C++, provider, test implementation or public API changes in this scoped update.

   * - 43. short_desc is plain text, under 80 chars, single sentence — no markdown
     - N/A
     - Not applicable to declarative metadata/evidence; no Qore, C++, provider, test implementation or public API changes in this scoped update.

   * - 44. desc uses markdown: backticks for code/field refs ( field_name ,  True ,  pdf ), \n\n for paragraphs, -  bullet lists for enumerations, bold for caveats
     - N/A
     - Not applicable to declarative metadata/evidence; no Qore, C++, provider, test implementation or public API changes in this scoped update.

   * - 45. Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use"
     - N/A
     - Not applicable to declarative metadata/evidence; no Qore, C++, provider, test implementation or public API changes in this scoped update.

   * - 46. No bare True/False/NOTHING — must be backtick-wrapped in desc
     - N/A
     - Not applicable to declarative metadata/evidence; no Qore, C++, provider, test implementation or public API changes in this scoped update.

   * - 47. No bare field/option names in prose — must use backticks
     - N/A
     - Not applicable to declarative metadata/evidence; no Qore, C++, provider, test implementation or public API changes in this scoped update.

   * - 48. Long descriptions (>500 chars) use bold section headers and bullet lists
     - N/A
     - Not applicable to declarative metadata/evidence; no Qore, C++, provider, test implementation or public API changes in this scoped update.

   * - 49. Factory registration in Qore repo: every factory name registered in qlib/DataProvider/DataProvider.qc → FactoryMap (without this, module loads but doesn't appear in Qorus apps)
     - N/A
     - Not applicable to declarative metadata/evidence; no Qore, C++, provider, test implementation or public API changes in this scoped update.

   * - 50. getRecordTypeImpl() signature: must be private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options) — NOT returning *AbstractDataProviderType
     - N/A
     - Not applicable to declarative metadata/evidence; no Qore, C++, provider, test implementation or public API changes in this scoped update.

   * - 51. Dependency JARs committed (for JNI modules): JAR files in qlib/*/jar/ may be gitignored — use git add -f to ensure they're tracked, otherwise CI compilation fails
     - N/A
     - Not applicable to declarative metadata/evidence; no Qore, C++, provider, test implementation or public API changes in this scoped update.

   * - 52. JAR install rules in CMakeLists.txt for all dependency JARs
     - N/A
     - Not applicable to declarative metadata/evidence; no Qore, C++, provider, test implementation or public API changes in this scoped update.

   * - 53. No workarounds: No TODOs, FIXMEs, stubs, or partially-implemented features
     - Pass
     - No workaround; the public package uses distribution FreeTDS. Live SQL and proprietary OCS are explicitly unqualified.

   * - 54. Exception safety: C++ uses ReferenceHolder for Qore allocations, std::unique_ptr for C++ allocations, *xsink checked after every fallible operation
     - N/A
     - Not applicable to declarative metadata/evidence; no Qore, C++, provider, test implementation or public API changes in this scoped update.

   * - 55. Thread safety: All mutable shared state protected by std::lock_guard<std::mutex> or documented as immutable-after-construction
     - N/A
     - Not applicable to declarative metadata/evidence; no Qore, C++, provider, test implementation or public API changes in this scoped update.

   * - 56. Type safety: Strongly-typed code<return(args)> instead of untyped code; static_cast instead of C casts; typed hashdecls for results; enums where appropriate
     - N/A
     - Not applicable to declarative metadata/evidence; no Qore, C++, provider, test implementation or public API changes in this scoped update.

   * - 57. Performance: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply
     - N/A
     - Not applicable to declarative metadata/evidence; no Qore, C++, provider, test implementation or public API changes in this scoped update.

   * - 58. Error handling: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable
     - Pass
     - Canonical commit, RPM hashes, all build/install exits and exact test coverage verified before recording success.

   * - 59. Documentation: Doxygen @param, @return, @throw on all public methods; @par Example with realistic business scenarios; @note for important caveats
     - Pass
     - README describes actual offline coverage and remaining release gates.

   * - 60. QPP flags: [flags=CONSTANT] on methods that never throw; [flags=RET_VALUE_ONLY] on methods that throw but have no side effects
     - N/A
     - Not applicable to declarative metadata/evidence; no Qore, C++, provider, test implementation or public API changes in this scoped update.

   * - 61. Security: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code
     - Pass
     - Source URL is public, metadata contains no secrets, publication remains disabled.

   * - 62. Correctness: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features)
     - Pass
     - All three canonical offline builds and runtime/SDK checks pass without warnings; 71 orchestration tests pass.
