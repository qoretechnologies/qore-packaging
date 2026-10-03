PDFium native build status evidence audit
=========================================

Copyright 2026 Qore Technologies, s.r.o.

Scope: evidence update only. Four native OBS targets passed; two Fedora targets failed in distribution dependency retrieval before compilation. No source/recipe changes and no qualification of the failed targets.

.. list-table:: Complete audit-changes checklist
   :header-rows: 1

   * - Check
     - Status
     - Evidence

   * - 1. Entry exists in doxygen/lang/120_modules.dox.tmpl (for modules in the Qore repo; N/A for external module repos)
     - N/A
     - Evidence-only scope: no implementation, runtime, API, module, test code, concurrency, provider, Java or build recipe change.

   * - 2. Entry exists in doxygen/lang/900_release_notes.dox.tmpl (for modules in the Qore repo; external modules have release notes in their .qm)
     - N/A
     - Evidence-only scope: no implementation, runtime, API, module, test code, concurrency, provider, Java or build recipe change.

   * - 3. qore_user_module() or qore_external_user_module() call in CMakeLists.txt
     - N/A
     - Evidence-only scope: no implementation, runtime, API, module, test code, concurrency, provider, Java or build recipe change.

   * - 4. Module added to QMOD list in CMakeLists.txt
     - N/A
     - Evidence-only scope: no implementation, runtime, API, module, test code, concurrency, provider, Java or build recipe change.

   * - 5. .qm file has @section <lowercasemodname>intro as first doc section — must be all lowercase (e.g., avrodataproviderintro, not AvroDataProviderintro)
     - N/A
     - Evidence-only scope: no implementation, runtime, API, module, test code, concurrency, provider, Java or build recipe change.

   * - 6. %modern in .qm file — no redundant %new-style, %require-types, %strict-args, %enable-all-warnings
     - N/A
     - Evidence-only scope: no implementation, runtime, API, module, test code, concurrency, provider, Java or build recipe change.

   * - 7. No parse directives (%requires, %modern, %new-style) in separated .qc files (check OUTSIDE of @code blocks only)
     - N/A
     - Evidence-only scope: no implementation, runtime, API, module, test code, concurrency, provider, Java or build recipe change.

   * - 8. No %include usage (deprecated for modules)
     - N/A
     - Evidence-only scope: no implementation, runtime, API, module, test code, concurrency, provider, Java or build recipe change.

   * - 9. Copyright 2026 on all new files
     - Pass
     - 2026 copyright in evidence and audit.

   * - 10. Directory layout: .qm inside qlib/<ModuleName>/ directory (not at qlib/<ModuleName>.qm for multi-file modules)
     - N/A
     - Evidence-only scope: no implementation, runtime, API, module, test code, concurrency, provider, Java or build recipe change.

   * - 11. No second .qm for the same module at qlib/<ModuleName>.qm
     - N/A
     - Evidence-only scope: no implementation, runtime, API, module, test code, concurrency, provider, Java or build recipe change.

   * - 12. ns=Qore::XX matches the QoreNamespace constructor path
     - N/A
     - Evidence-only scope: no implementation, runtime, API, module, test code, concurrency, provider, Java or build recipe change.

   * - 13. %modern directive present
     - N/A
     - Evidence-only scope: no implementation, runtime, API, module, test code, concurrency, provider, Java or build recipe change.

   * - 14. Executable permission set (chmod +x)
     - N/A
     - Evidence-only scope: no implementation, runtime, API, module, test code, concurrency, provider, Java or build recipe change.

   * - 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus)
     - N/A
     - Evidence-only scope: no implementation, runtime, API, module, test code, concurrency, provider, Java or build recipe change.

   * - 16. External module dependencies use %try-module — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard %requires
     - N/A
     - Evidence-only scope: no implementation, runtime, API, module, test code, concurrency, provider, Java or build recipe change.

   * - 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks
     - N/A
     - Evidence-only scope: no implementation, runtime, API, module, test code, concurrency, provider, Java or build recipe change.

   * - 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks
     - N/A
     - Evidence-only scope: no implementation, runtime, API, module, test code, concurrency, provider, Java or build recipe change.

   * - 19. If filesystem/network ops exist, verify QoreSandboxManagerHelper usage
     - N/A
     - Evidence-only scope: no implementation, runtime, API, module, test code, concurrency, provider, Java or build recipe change.

   * - 20. No File::, Dir::, Socket::, HTTPClient:: usage without justification
     - N/A
     - Evidence-only scope: no implementation, runtime, API, module, test code, concurrency, provider, Java or build recipe change.

   * - 21. All for/while loops that could iterate >100 times have qore_check_cancel() checks
     - N/A
     - Evidence-only scope: no implementation, runtime, API, module, test code, concurrency, provider, Java or build recipe change.

   * - 22. Uses qore_check_cancel() (NOT deprecated qore_check_io_interrupt())
     - N/A
     - Evidence-only scope: no implementation, runtime, API, module, test code, concurrency, provider, Java or build recipe change.

   * - 23. Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations
     - N/A
     - Evidence-only scope: no implementation, runtime, API, module, test code, concurrency, provider, Java or build recipe change.

   * - 24. No blocking operations without cancellation support
     - N/A
     - Evidence-only scope: no implementation, runtime, API, module, test code, concurrency, provider, Java or build recipe change.

   * - 25. Every action has display_name, short_desc (plain text, <80 chars), desc (markdown)
     - N/A
     - Evidence-only scope: no implementation, runtime, API, module, test code, concurrency, provider, Java or build recipe change.

   * - 26. Every action has options populated via getActionOptionFromFields() — without this, the action shows an empty, unusable form
     - N/A
     - Evidence-only scope: no implementation, runtime, API, module, test code, concurrency, provider, Java or build recipe change.

   * - 27. Every action has output_type set to a typed data type constant (e.g., MyResponseDataType) — not omitted
     - N/A
     - Evidence-only scope: no implementation, runtime, API, module, test code, concurrency, provider, Java or build recipe change.

   * - 28. DPAT_API actions: provider has "supports_request": True and implements doRequestImpl()
     - N/A
     - Evidence-only scope: no implementation, runtime, API, module, test code, concurrency, provider, Java or build recipe change.

   * - 29. DPAT_FIND actions: every option exists in SearchOptions, getRecordTypeImpl() returns *hash<string, AbstractDataField>
     - N/A
     - Evidence-only scope: no implementation, runtime, API, module, test code, concurrency, provider, Java or build recipe change.

   * - 30. Scheme-based apps (with "scheme" in registerApp): actions use "path" and do NOT use "cls" — having both scheme and cls causes a runtime error
     - N/A
     - Evidence-only scope: no implementation, runtime, API, module, test code, concurrency, provider, Java or build recipe change.

   * - 31. Single-key hash slices use trailing comma: Fields{"key",} (without trailing comma, Fields{"key"} returns the value, not a hash)
     - N/A
     - Evidence-only scope: no implementation, runtime, API, module, test code, concurrency, provider, Java or build recipe change.

   * - 32. Typed data type classes exist for request and response types — inherit HashDataType, have const Fields hash, call addQoreFields(Fields) in constructor, export public constant at bottom (e.g., public const MyDataType = new MyDataType();)
     - N/A
     - Evidence-only scope: no implementation, runtime, API, module, test code, concurrency, provider, Java or build recipe change.

   * - 33. Request/input types use public Fields (enables ClassName::Fields in action registration)
     - N/A
     - Evidence-only scope: no implementation, runtime, API, module, test code, concurrency, provider, Java or build recipe change.

   * - 34. Response/output types use private Fields
     - N/A
     - Evidence-only scope: no implementation, runtime, API, module, test code, concurrency, provider, Java or build recipe change.

   * - 35. Each field in data types has display_name, type, and desc (markdown-formatted)
     - N/A
     - Evidence-only scope: no implementation, runtime, API, module, test code, concurrency, provider, Java or build recipe change.

   * - 36. Input fields have example_value where useful (string fields, endpoint URIs, SQL queries, etc.)
     - N/A
     - Evidence-only scope: no implementation, runtime, API, module, test code, concurrency, provider, Java or build recipe change.

   * - 37. Fields with finite allowed values use allowed_values with AllowedValueInfo containing both value and display_name (Title Case, human-readable) — never bare values, never described only in text
     - N/A
     - Evidence-only scope: no implementation, runtime, API, module, test code, concurrency, provider, Java or build recipe change.

   * - 38. Password/secret fields have "sensitive": True
     - N/A
     - Evidence-only scope: no implementation, runtime, API, module, test code, concurrency, provider, Java or build recipe change.

   * - 39. groups uses AppGroup enum values from qlib/DataProvider/AppGroup.qc
     - N/A
     - Evidence-only scope: no implementation, runtime, API, module, test code, concurrency, provider, Java or build recipe change.

   * - 40. App logo stored as separate file, loaded at module level in Priv namespace
     - N/A
     - Evidence-only scope: no implementation, runtime, API, module, test code, concurrency, provider, Java or build recipe change.

   * - 41. App desc uses markdown: bullet list of capabilities, links to project website, business-language explanation of value
     - N/A
     - Evidence-only scope: no implementation, runtime, API, module, test code, concurrency, provider, Java or build recipe change.

   * - 42. display_name is user-friendly ("Apache Avro" not "avro")
     - N/A
     - Evidence-only scope: no implementation, runtime, API, module, test code, concurrency, provider, Java or build recipe change.

   * - 43. short_desc is plain text, under 80 chars, single sentence — no markdown
     - N/A
     - Evidence-only scope: no implementation, runtime, API, module, test code, concurrency, provider, Java or build recipe change.

   * - 44. desc uses markdown: backticks for code/field refs ( field_name ,  True ,  pdf ), \n\n for paragraphs, -  bullet lists for enumerations, bold for caveats
     - N/A
     - Evidence-only scope: no implementation, runtime, API, module, test code, concurrency, provider, Java or build recipe change.

   * - 45. Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use"
     - N/A
     - Evidence-only scope: no implementation, runtime, API, module, test code, concurrency, provider, Java or build recipe change.

   * - 46. No bare True/False/NOTHING — must be backtick-wrapped in desc
     - N/A
     - Evidence-only scope: no implementation, runtime, API, module, test code, concurrency, provider, Java or build recipe change.

   * - 47. No bare field/option names in prose — must use backticks
     - N/A
     - Evidence-only scope: no implementation, runtime, API, module, test code, concurrency, provider, Java or build recipe change.

   * - 48. Long descriptions (>500 chars) use bold section headers and bullet lists
     - N/A
     - Evidence-only scope: no implementation, runtime, API, module, test code, concurrency, provider, Java or build recipe change.

   * - 49. Factory registration in Qore repo: every factory name registered in qlib/DataProvider/DataProvider.qc → FactoryMap (without this, module loads but doesn't appear in Qorus apps)
     - N/A
     - Evidence-only scope: no implementation, runtime, API, module, test code, concurrency, provider, Java or build recipe change.

   * - 50. getRecordTypeImpl() signature: must be private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options) — NOT returning *AbstractDataProviderType
     - N/A
     - Evidence-only scope: no implementation, runtime, API, module, test code, concurrency, provider, Java or build recipe change.

   * - 51. Dependency JARs committed (for JNI modules): JAR files in qlib/*/jar/ may be gitignored — use git add -f to ensure they're tracked, otherwise CI compilation fails
     - N/A
     - Evidence-only scope: no implementation, runtime, API, module, test code, concurrency, provider, Java or build recipe change.

   * - 52. JAR install rules in CMakeLists.txt for all dependency JARs
     - N/A
     - Evidence-only scope: no implementation, runtime, API, module, test code, concurrency, provider, Java or build recipe change.

   * - 53. No workarounds: No TODOs, FIXMEs, stubs, or partially-implemented features
     - Pass
     - No package workaround, retry loop, suppression or disabled test.

   * - 54. Exception safety: C++ uses ReferenceHolder for Qore allocations, std::unique_ptr for C++ allocations, *xsink checked after every fallible operation
     - N/A
     - Evidence-only scope: no implementation, runtime, API, module, test code, concurrency, provider, Java or build recipe change.

   * - 55. Thread safety: All mutable shared state protected by std::lock_guard<std::mutex> or documented as immutable-after-construction
     - N/A
     - Evidence-only scope: no implementation, runtime, API, module, test code, concurrency, provider, Java or build recipe change.

   * - 56. Type safety: Strongly-typed code<return(args)> instead of untyped code; static_cast instead of C casts; typed hashdecls for results; enums where appropriate
     - N/A
     - Evidence-only scope: no implementation, runtime, API, module, test code, concurrency, provider, Java or build recipe change.

   * - 57. Performance: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply
     - N/A
     - Evidence-only scope: no implementation, runtime, API, module, test code, concurrency, provider, Java or build recipe change.

   * - 58. Error handling: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable
     - N/A
     - Evidence-only scope: no implementation, runtime, API, module, test code, concurrency, provider, Java or build recipe change.

   * - 59. Documentation: Doxygen @param, @return, @throw on all public methods; @par Example with realistic business scenarios; @note for important caveats
     - Pass
     - Evidence states exact native successes, Fedora infrastructure failure, one verified rebuild attempt and disabled publication.

   * - 60. QPP flags: [flags=CONSTANT] on methods that never throw; [flags=RET_VALUE_ONLY] on methods that throw but have no side effects
     - N/A
     - Evidence-only scope: no implementation, runtime, API, module, test code, concurrency, provider, Java or build recipe change.

   * - 61. Security: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code
     - Pass
     - Public project/package names and artifact digests only; no credentials.

   * - 62. Correctness: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features)
     - Pass
     - Four successful targets verified against saved OBS XML; failed rebuild log hashes and pre-compilation 404 diagnostics verified. All 39 packaging metadata tests pass.
