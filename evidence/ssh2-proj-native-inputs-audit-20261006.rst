SSH2 and PROJ native installed qualification inputs audit
=========================================================

Copyright 2026 Qore Technologies, s.r.o.

Scope: Fedora/Leap ARM manifests, two opt-in CI jobs, native build evidence and qualification documentation. Installed results remain pending.

.. list-table:: Complete audit-changes checklist
   :header-rows: 1

   * - Check
     - Status
     - Evidence

   * - 1. Entry exists in doxygen/lang/120_modules.dox.tmpl (for modules in the Qore repo; N/A for external module repos)
     - N/A
     - Manifest, CI and evidence-only change; no C++, Qore module, provider, public API, sandbox or cancellation behavior changed.

   * - 2. Entry exists in doxygen/lang/900_release_notes.dox.tmpl (for modules in the Qore repo; external modules have release notes in their .qm)
     - N/A
     - Manifest, CI and evidence-only change; no C++, Qore module, provider, public API, sandbox or cancellation behavior changed.

   * - 3. qore_user_module() or qore_external_user_module() call in CMakeLists.txt
     - N/A
     - Manifest, CI and evidence-only change; no C++, Qore module, provider, public API, sandbox or cancellation behavior changed.

   * - 4. Module added to QMOD list in CMakeLists.txt
     - N/A
     - Manifest, CI and evidence-only change; no C++, Qore module, provider, public API, sandbox or cancellation behavior changed.

   * - 5. .qm file has @section <lowercasemodname>intro as first doc section — must be all lowercase (e.g., avrodataproviderintro, not AvroDataProviderintro)
     - N/A
     - Manifest, CI and evidence-only change; no C++, Qore module, provider, public API, sandbox or cancellation behavior changed.

   * - 6. %modern in .qm file — no redundant %new-style, %require-types, %strict-args, %enable-all-warnings
     - N/A
     - Manifest, CI and evidence-only change; no C++, Qore module, provider, public API, sandbox or cancellation behavior changed.

   * - 7. No parse directives (%requires, %modern, %new-style) in separated .qc files (check OUTSIDE of @code blocks only)
     - N/A
     - Manifest, CI and evidence-only change; no C++, Qore module, provider, public API, sandbox or cancellation behavior changed.

   * - 8. No %include usage (deprecated for modules)
     - N/A
     - Manifest, CI and evidence-only change; no C++, Qore module, provider, public API, sandbox or cancellation behavior changed.

   * - 9. Copyright 2026 on all new files
     - Pass
     - New evidence and inherited manifests carry 2026 copyright.

   * - 10. Directory layout: .qm inside qlib/<ModuleName>/ directory (not at qlib/<ModuleName>.qm for multi-file modules)
     - N/A
     - Manifest, CI and evidence-only change; no C++, Qore module, provider, public API, sandbox or cancellation behavior changed.

   * - 11. No second .qm for the same module at qlib/<ModuleName>.qm
     - N/A
     - Manifest, CI and evidence-only change; no C++, Qore module, provider, public API, sandbox or cancellation behavior changed.

   * - 12. ns=Qore::XX matches the QoreNamespace constructor path
     - N/A
     - Manifest, CI and evidence-only change; no C++, Qore module, provider, public API, sandbox or cancellation behavior changed.

   * - 13. %modern directive present
     - N/A
     - Manifest, CI and evidence-only change; no C++, Qore module, provider, public API, sandbox or cancellation behavior changed.

   * - 14. Executable permission set (chmod +x)
     - N/A
     - Manifest, CI and evidence-only change; no C++, Qore module, provider, public API, sandbox or cancellation behavior changed.

   * - 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus)
     - N/A
     - Manifest, CI and evidence-only change; no C++, Qore module, provider, public API, sandbox or cancellation behavior changed.

   * - 16. External module dependencies use %try-module — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard %requires
     - N/A
     - Manifest, CI and evidence-only change; no C++, Qore module, provider, public API, sandbox or cancellation behavior changed.

   * - 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks
     - N/A
     - Manifest, CI and evidence-only change; no C++, Qore module, provider, public API, sandbox or cancellation behavior changed.

   * - 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks
     - N/A
     - Manifest, CI and evidence-only change; no C++, Qore module, provider, public API, sandbox or cancellation behavior changed.

   * - 19. If filesystem/network ops exist, verify QoreSandboxManagerHelper usage
     - N/A
     - Manifest, CI and evidence-only change; no C++, Qore module, provider, public API, sandbox or cancellation behavior changed.

   * - 20. No File::, Dir::, Socket::, HTTPClient:: usage without justification
     - N/A
     - Manifest, CI and evidence-only change; no C++, Qore module, provider, public API, sandbox or cancellation behavior changed.

   * - 21. All for/while loops that could iterate >100 times have qore_check_cancel() checks
     - N/A
     - Manifest, CI and evidence-only change; no C++, Qore module, provider, public API, sandbox or cancellation behavior changed.

   * - 22. Uses qore_check_cancel() (NOT deprecated qore_check_io_interrupt())
     - N/A
     - Manifest, CI and evidence-only change; no C++, Qore module, provider, public API, sandbox or cancellation behavior changed.

   * - 23. Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations
     - N/A
     - Manifest, CI and evidence-only change; no C++, Qore module, provider, public API, sandbox or cancellation behavior changed.

   * - 24. No blocking operations without cancellation support
     - N/A
     - Manifest, CI and evidence-only change; no C++, Qore module, provider, public API, sandbox or cancellation behavior changed.

   * - 25. Every action has display_name, short_desc (plain text, <80 chars), desc (markdown)
     - N/A
     - Manifest, CI and evidence-only change; no C++, Qore module, provider, public API, sandbox or cancellation behavior changed.

   * - 26. Every action has options populated via getActionOptionFromFields() — without this, the action shows an empty, unusable form
     - N/A
     - Manifest, CI and evidence-only change; no C++, Qore module, provider, public API, sandbox or cancellation behavior changed.

   * - 27. Every action has output_type set to a typed data type constant (e.g., MyResponseDataType) — not omitted
     - N/A
     - Manifest, CI and evidence-only change; no C++, Qore module, provider, public API, sandbox or cancellation behavior changed.

   * - 28. DPAT_API actions: provider has "supports_request": True and implements doRequestImpl()
     - N/A
     - Manifest, CI and evidence-only change; no C++, Qore module, provider, public API, sandbox or cancellation behavior changed.

   * - 29. DPAT_FIND actions: every option exists in SearchOptions, getRecordTypeImpl() returns *hash<string, AbstractDataField>
     - N/A
     - Manifest, CI and evidence-only change; no C++, Qore module, provider, public API, sandbox or cancellation behavior changed.

   * - 30. Scheme-based apps (with "scheme" in registerApp): actions use "path" and do NOT use "cls" — having both scheme and cls causes a runtime error
     - N/A
     - Manifest, CI and evidence-only change; no C++, Qore module, provider, public API, sandbox or cancellation behavior changed.

   * - 31. Single-key hash slices use trailing comma: Fields{"key",} (without trailing comma, Fields{"key"} returns the value, not a hash)
     - N/A
     - Manifest, CI and evidence-only change; no C++, Qore module, provider, public API, sandbox or cancellation behavior changed.

   * - 32. Typed data type classes exist for request and response types — inherit HashDataType, have const Fields hash, call addQoreFields(Fields) in constructor, export public constant at bottom (e.g., public const MyDataType = new MyDataType();)
     - N/A
     - Manifest, CI and evidence-only change; no C++, Qore module, provider, public API, sandbox or cancellation behavior changed.

   * - 33. Request/input types use public Fields (enables ClassName::Fields in action registration)
     - N/A
     - Manifest, CI and evidence-only change; no C++, Qore module, provider, public API, sandbox or cancellation behavior changed.

   * - 34. Response/output types use private Fields
     - N/A
     - Manifest, CI and evidence-only change; no C++, Qore module, provider, public API, sandbox or cancellation behavior changed.

   * - 35. Each field in data types has display_name, type, and desc (markdown-formatted)
     - N/A
     - Manifest, CI and evidence-only change; no C++, Qore module, provider, public API, sandbox or cancellation behavior changed.

   * - 36. Input fields have example_value where useful (string fields, endpoint URIs, SQL queries, etc.)
     - N/A
     - Manifest, CI and evidence-only change; no C++, Qore module, provider, public API, sandbox or cancellation behavior changed.

   * - 37. Fields with finite allowed values use allowed_values with AllowedValueInfo containing both value and display_name (Title Case, human-readable) — never bare values, never described only in text
     - N/A
     - Manifest, CI and evidence-only change; no C++, Qore module, provider, public API, sandbox or cancellation behavior changed.

   * - 38. Password/secret fields have "sensitive": True
     - N/A
     - Manifest, CI and evidence-only change; no C++, Qore module, provider, public API, sandbox or cancellation behavior changed.

   * - 39. groups uses AppGroup enum values from qlib/DataProvider/AppGroup.qc
     - N/A
     - Manifest, CI and evidence-only change; no C++, Qore module, provider, public API, sandbox or cancellation behavior changed.

   * - 40. App logo stored as separate file, loaded at module level in Priv namespace
     - N/A
     - Manifest, CI and evidence-only change; no C++, Qore module, provider, public API, sandbox or cancellation behavior changed.

   * - 41. App desc uses markdown: bullet list of capabilities, links to project website, business-language explanation of value
     - N/A
     - Manifest, CI and evidence-only change; no C++, Qore module, provider, public API, sandbox or cancellation behavior changed.

   * - 42. display_name is user-friendly ("Apache Avro" not "avro")
     - N/A
     - Manifest, CI and evidence-only change; no C++, Qore module, provider, public API, sandbox or cancellation behavior changed.

   * - 43. short_desc is plain text, under 80 chars, single sentence — no markdown
     - N/A
     - Manifest, CI and evidence-only change; no C++, Qore module, provider, public API, sandbox or cancellation behavior changed.

   * - 44. desc uses markdown: backticks for code/field refs ( field_name ,  True ,  pdf ), \n\n for paragraphs, -  bullet lists for enumerations, bold for caveats
     - N/A
     - Manifest, CI and evidence-only change; no C++, Qore module, provider, public API, sandbox or cancellation behavior changed.

   * - 45. Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use"
     - N/A
     - Manifest, CI and evidence-only change; no C++, Qore module, provider, public API, sandbox or cancellation behavior changed.

   * - 46. No bare True/False/NOTHING — must be backtick-wrapped in desc
     - N/A
     - Manifest, CI and evidence-only change; no C++, Qore module, provider, public API, sandbox or cancellation behavior changed.

   * - 47. No bare field/option names in prose — must use backticks
     - N/A
     - Manifest, CI and evidence-only change; no C++, Qore module, provider, public API, sandbox or cancellation behavior changed.

   * - 48. Long descriptions (>500 chars) use bold section headers and bullet lists
     - N/A
     - Manifest, CI and evidence-only change; no C++, Qore module, provider, public API, sandbox or cancellation behavior changed.

   * - 49. Factory registration in Qore repo: every factory name registered in qlib/DataProvider/DataProvider.qc → FactoryMap (without this, module loads but doesn't appear in Qorus apps)
     - N/A
     - Manifest, CI and evidence-only change; no C++, Qore module, provider, public API, sandbox or cancellation behavior changed.

   * - 50. getRecordTypeImpl() signature: must be private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options) — NOT returning *AbstractDataProviderType
     - N/A
     - Manifest, CI and evidence-only change; no C++, Qore module, provider, public API, sandbox or cancellation behavior changed.

   * - 51. Dependency JARs committed (for JNI modules): JAR files in qlib/*/jar/ may be gitignored — use git add -f to ensure they're tracked, otherwise CI compilation fails
     - N/A
     - Manifest, CI and evidence-only change; no C++, Qore module, provider, public API, sandbox or cancellation behavior changed.

   * - 52. JAR install rules in CMakeLists.txt for all dependency JARs
     - N/A
     - Manifest, CI and evidence-only change; no C++, Qore module, provider, public API, sandbox or cancellation behavior changed.

   * - 53. No workarounds: No TODOs, FIXMEs, stubs, or partially-implemented features
     - Pass
     - No workaround; only explicitly approved existing diagnostics accepted.

   * - 54. Exception safety: C++ uses ReferenceHolder for Qore allocations, std::unique_ptr for C++ allocations, *xsink checked after every fallible operation
     - Pass
     - Existing runner rejects invalid manifests before installation; no execution logic change.

   * - 55. Thread safety: All mutable shared state protected by std::lock_guard<std::mutex> or documented as immutable-after-construction
     - Pass
     - Commit, source and artifact hashes identify independent immutable inputs.

   * - 56. Type safety: Strongly-typed code<return(args)> instead of untyped code; static_cast instead of C casts; typed hashdecls for results; enums where appropriate
     - N/A
     - Manifest, CI and evidence-only change; no C++, Qore module, provider, public API, sandbox or cancellation behavior changed.

   * - 57. Performance: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply
     - N/A
     - Manifest, CI and evidence-only change; no C++, Qore module, provider, public API, sandbox or cancellation behavior changed.

   * - 58. Error handling: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable
     - Pass
     - Both manifests validate; all source fixtures matched public and Git bytes; source histories match uploaded revisions.

   * - 59. Documentation: Doxygen @param, @return, @throw on all public methods; @par Example with realistic business scenarios; @note for important caveats
     - Pass
     - Documents opt-in CI variables, clean runtime/SDK phases and remaining AlmaLinux gate.

   * - 60. QPP flags: [flags=CONSTANT] on methods that never throw; [flags=RET_VALUE_ONLY] on methods that throw but have no side effects
     - N/A
     - Manifest, CI and evidence-only change; no C++, Qore module, provider, public API, sandbox or cancellation behavior changed.

   * - 61. Security: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code
     - Pass
     - HTTPS, per-artifact SHA256, pinned signing key and RPM signature verification retained.

   * - 62. Correctness: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features)
     - Pass
     - Eight matching native source builds pass; 176 unit tests pass. Installed results explicitly not yet claimed.
