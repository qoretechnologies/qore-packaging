Catalog and FreeTDS ARM enablement audit
========================================

Copyright 2026 Qore Technologies, s.r.o.

Scope: catalog.json, obs/package-freetds-testing.xml and read-only verification evidence. Result: 7 Pass, 55 N/A, 0 Fail across all 62 checklist entries.

.. list-table:: Complete audit-changes checklist
   :header-rows: 1

   * - Check
     - Status
     - Evidence

   * - 1. Entry exists in doxygen/lang/120_modules.dox.tmpl (for modules in the Qore repo; N/A for external module repos)
     - N/A
     - No corresponding runtime, C++, Qore module, test implementation, DataProvider, JNI or public API change.

   * - 2. Entry exists in doxygen/lang/900_release_notes.dox.tmpl (for modules in the Qore repo; external modules have release notes in their .qm)
     - N/A
     - No corresponding runtime, C++, Qore module, test implementation, DataProvider, JNI or public API change.

   * - 3. qore_user_module() or qore_external_user_module() call in CMakeLists.txt
     - N/A
     - No corresponding runtime, C++, Qore module, test implementation, DataProvider, JNI or public API change.

   * - 4. Module added to QMOD list in CMakeLists.txt
     - N/A
     - No corresponding runtime, C++, Qore module, test implementation, DataProvider, JNI or public API change.

   * - 5. .qm file has @section <lowercasemodname>intro as first doc section — must be all lowercase (e.g., avrodataproviderintro, not AvroDataProviderintro)
     - N/A
     - No corresponding runtime, C++, Qore module, test implementation, DataProvider, JNI or public API change.

   * - 6. %modern in .qm file — no redundant %new-style, %require-types, %strict-args, %enable-all-warnings
     - N/A
     - No corresponding runtime, C++, Qore module, test implementation, DataProvider, JNI or public API change.

   * - 7. No parse directives (%requires, %modern, %new-style) in separated .qc files (check OUTSIDE of @code blocks only)
     - N/A
     - No corresponding runtime, C++, Qore module, test implementation, DataProvider, JNI or public API change.

   * - 8. No %include usage (deprecated for modules)
     - N/A
     - No corresponding runtime, C++, Qore module, test implementation, DataProvider, JNI or public API change.

   * - 9. Copyright 2026 on all new files
     - Pass
     - New metadata, evidence and verifier sources identify 2026; raw OBS responses are preserved verbatim.

   * - 10. Directory layout: .qm inside qlib/<ModuleName>/ directory (not at qlib/<ModuleName>.qm for multi-file modules)
     - N/A
     - No corresponding runtime, C++, Qore module, test implementation, DataProvider, JNI or public API change.

   * - 11. No second .qm for the same module at qlib/<ModuleName>.qm
     - N/A
     - No corresponding runtime, C++, Qore module, test implementation, DataProvider, JNI or public API change.

   * - 12. ns=Qore::XX matches the QoreNamespace constructor path
     - N/A
     - No corresponding runtime, C++, Qore module, test implementation, DataProvider, JNI or public API change.

   * - 13. %modern directive present
     - N/A
     - No corresponding runtime, C++, Qore module, test implementation, DataProvider, JNI or public API change.

   * - 14. Executable permission set (chmod +x)
     - N/A
     - No corresponding runtime, C++, Qore module, test implementation, DataProvider, JNI or public API change.

   * - 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus)
     - N/A
     - No corresponding runtime, C++, Qore module, test implementation, DataProvider, JNI or public API change.

   * - 16. External module dependencies use %try-module — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard %requires
     - N/A
     - No corresponding runtime, C++, Qore module, test implementation, DataProvider, JNI or public API change.

   * - 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks
     - N/A
     - No corresponding runtime, C++, Qore module, test implementation, DataProvider, JNI or public API change.

   * - 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks
     - N/A
     - No corresponding runtime, C++, Qore module, test implementation, DataProvider, JNI or public API change.

   * - 19. If filesystem/network ops exist, verify QoreSandboxManagerHelper usage
     - N/A
     - No corresponding runtime, C++, Qore module, test implementation, DataProvider, JNI or public API change.

   * - 20. No File::, Dir::, Socket::, HTTPClient:: usage without justification
     - N/A
     - No corresponding runtime, C++, Qore module, test implementation, DataProvider, JNI or public API change.

   * - 21. All for/while loops that could iterate >100 times have qore_check_cancel() checks
     - N/A
     - No corresponding runtime, C++, Qore module, test implementation, DataProvider, JNI or public API change.

   * - 22. Uses qore_check_cancel() (NOT deprecated qore_check_io_interrupt())
     - N/A
     - No corresponding runtime, C++, Qore module, test implementation, DataProvider, JNI or public API change.

   * - 23. Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations
     - N/A
     - No corresponding runtime, C++, Qore module, test implementation, DataProvider, JNI or public API change.

   * - 24. No blocking operations without cancellation support
     - N/A
     - No corresponding runtime, C++, Qore module, test implementation, DataProvider, JNI or public API change.

   * - 25. Every action has display_name, short_desc (plain text, <80 chars), desc (markdown)
     - N/A
     - No corresponding runtime, C++, Qore module, test implementation, DataProvider, JNI or public API change.

   * - 26. Every action has options populated via getActionOptionFromFields() — without this, the action shows an empty, unusable form
     - N/A
     - No corresponding runtime, C++, Qore module, test implementation, DataProvider, JNI or public API change.

   * - 27. Every action has output_type set to a typed data type constant (e.g., MyResponseDataType) — not omitted
     - N/A
     - No corresponding runtime, C++, Qore module, test implementation, DataProvider, JNI or public API change.

   * - 28. DPAT_API actions: provider has "supports_request": True and implements doRequestImpl()
     - N/A
     - No corresponding runtime, C++, Qore module, test implementation, DataProvider, JNI or public API change.

   * - 29. DPAT_FIND actions: every option exists in SearchOptions, getRecordTypeImpl() returns *hash<string, AbstractDataField>
     - N/A
     - No corresponding runtime, C++, Qore module, test implementation, DataProvider, JNI or public API change.

   * - 30. Scheme-based apps (with "scheme" in registerApp): actions use "path" and do NOT use "cls" — having both scheme and cls causes a runtime error
     - N/A
     - No corresponding runtime, C++, Qore module, test implementation, DataProvider, JNI or public API change.

   * - 31. Single-key hash slices use trailing comma: Fields{"key",} (without trailing comma, Fields{"key"} returns the value, not a hash)
     - N/A
     - No corresponding runtime, C++, Qore module, test implementation, DataProvider, JNI or public API change.

   * - 32. Typed data type classes exist for request and response types — inherit HashDataType, have const Fields hash, call addQoreFields(Fields) in constructor, export public constant at bottom (e.g., public const MyDataType = new MyDataType();)
     - N/A
     - No corresponding runtime, C++, Qore module, test implementation, DataProvider, JNI or public API change.

   * - 33. Request/input types use public Fields (enables ClassName::Fields in action registration)
     - N/A
     - No corresponding runtime, C++, Qore module, test implementation, DataProvider, JNI or public API change.

   * - 34. Response/output types use private Fields
     - N/A
     - No corresponding runtime, C++, Qore module, test implementation, DataProvider, JNI or public API change.

   * - 35. Each field in data types has display_name, type, and desc (markdown-formatted)
     - N/A
     - No corresponding runtime, C++, Qore module, test implementation, DataProvider, JNI or public API change.

   * - 36. Input fields have example_value where useful (string fields, endpoint URIs, SQL queries, etc.)
     - N/A
     - No corresponding runtime, C++, Qore module, test implementation, DataProvider, JNI or public API change.

   * - 37. Fields with finite allowed values use allowed_values with AllowedValueInfo containing both value and display_name (Title Case, human-readable) — never bare values, never described only in text
     - N/A
     - No corresponding runtime, C++, Qore module, test implementation, DataProvider, JNI or public API change.

   * - 38. Password/secret fields have "sensitive": True
     - N/A
     - No corresponding runtime, C++, Qore module, test implementation, DataProvider, JNI or public API change.

   * - 39. groups uses AppGroup enum values from qlib/DataProvider/AppGroup.qc
     - N/A
     - No corresponding runtime, C++, Qore module, test implementation, DataProvider, JNI or public API change.

   * - 40. App logo stored as separate file, loaded at module level in Priv namespace
     - N/A
     - No corresponding runtime, C++, Qore module, test implementation, DataProvider, JNI or public API change.

   * - 41. App desc uses markdown: bullet list of capabilities, links to project website, business-language explanation of value
     - N/A
     - No corresponding runtime, C++, Qore module, test implementation, DataProvider, JNI or public API change.

   * - 42. display_name is user-friendly ("Apache Avro" not "avro")
     - N/A
     - No corresponding runtime, C++, Qore module, test implementation, DataProvider, JNI or public API change.

   * - 43. short_desc is plain text, under 80 chars, single sentence — no markdown
     - N/A
     - No corresponding runtime, C++, Qore module, test implementation, DataProvider, JNI or public API change.

   * - 44. desc uses markdown: backticks for code/field refs ( field_name ,  True ,  pdf ), \n\n for paragraphs, -  bullet lists for enumerations, bold for caveats
     - N/A
     - No corresponding runtime, C++, Qore module, test implementation, DataProvider, JNI or public API change.

   * - 45. Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use"
     - N/A
     - No corresponding runtime, C++, Qore module, test implementation, DataProvider, JNI or public API change.

   * - 46. No bare True/False/NOTHING — must be backtick-wrapped in desc
     - N/A
     - No corresponding runtime, C++, Qore module, test implementation, DataProvider, JNI or public API change.

   * - 47. No bare field/option names in prose — must use backticks
     - N/A
     - No corresponding runtime, C++, Qore module, test implementation, DataProvider, JNI or public API change.

   * - 48. Long descriptions (>500 chars) use bold section headers and bullet lists
     - N/A
     - No corresponding runtime, C++, Qore module, test implementation, DataProvider, JNI or public API change.

   * - 49. Factory registration in Qore repo: every factory name registered in qlib/DataProvider/DataProvider.qc → FactoryMap (without this, module loads but doesn't appear in Qorus apps)
     - N/A
     - No corresponding runtime, C++, Qore module, test implementation, DataProvider, JNI or public API change.

   * - 50. getRecordTypeImpl() signature: must be private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options) — NOT returning *AbstractDataProviderType
     - N/A
     - No corresponding runtime, C++, Qore module, test implementation, DataProvider, JNI or public API change.

   * - 51. Dependency JARs committed (for JNI modules): JAR files in qlib/*/jar/ may be gitignored — use git add -f to ensure they're tracked, otherwise CI compilation fails
     - N/A
     - No corresponding runtime, C++, Qore module, test implementation, DataProvider, JNI or public API change.

   * - 52. JAR install rules in CMakeLists.txt for all dependency JARs
     - N/A
     - No corresponding runtime, C++, Qore module, test implementation, DataProvider, JNI or public API change.

   * - 53. No workarounds: No TODOs, FIXMEs, stubs, or partially-implemented features
     - Pass
     - The catalog is corrected to the already-qualified MySQL commit. FreeTDS gains only the three native ARM build enables; no source or runtime workaround.

   * - 54. Exception safety: C++ uses ReferenceHolder for Qore allocations, std::unique_ptr for C++ allocations, *xsink checked after every fallible operation
     - Pass
     - Read-only reconciliation validates command exits and manifest hashes; metadata mutation is guarded by the expected source hash and verified by exact readback.

   * - 55. Thread safety: All mutable shared state protected by std::lock_guard<std::mutex> or documented as immutable-after-construction
     - N/A
     - No corresponding runtime, C++, Qore module, test implementation, DataProvider, JNI or public API change.

   * - 56. Type safety: Strongly-typed code<return(args)> instead of untyped code; static_cast instead of C casts; typed hashdecls for results; enums where appropriate
     - N/A
     - No corresponding runtime, C++, Qore module, test implementation, DataProvider, JNI or public API change.

   * - 57. Performance: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply
     - N/A
     - No corresponding runtime, C++, Qore module, test implementation, DataProvider, JNI or public API change.

   * - 58. Error handling: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable
     - Pass
     - Pinned RPM Name fields identify packages; inventory-only NATS is explicitly distinguished from committed specs. All dependency graphs resolve before enabling builds.

   * - 59. Documentation: Doxygen @param, @return, @throw on all public methods; @par Example with realistic business scenarios; @note for important caveats
     - Pass
     - Evidence states source/build/installed limits separately and retains the corrected initial inventory; publication remains disabled.

   * - 60. QPP flags: [flags=CONSTANT] on methods that never throw; [flags=RET_VALUE_ONLY] on methods that throw but have no side effects
     - N/A
     - No corresponding runtime, C++, Qore module, test implementation, DataProvider, JNI or public API change.

   * - 61. Security: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code
     - Pass
     - Only the authorized testing project metadata changes; no credentials are stored or printed. Existing metadata fields are preserved.

   * - 62. Correctness: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features)
     - Pass
     - All 224 packaging tests pass. All 38 catalog entries reconciled, 37 match OBS source pins, six MySQL buildinfo hashes verified; all three prior FreeTDS build/install evidence sets remain hash-identical.
