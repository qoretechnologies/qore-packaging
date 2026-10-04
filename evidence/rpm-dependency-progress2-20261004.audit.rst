gRPC metadata qualification and NATS route/paging review
========================================================

Copyright 2026 Qore Technologies, s.r.o.

Scope: README.rst plus grpcio-remaining-diagnostics-20261004.json, grpcio-rpm-candidate14b-20261004.json and nats-routes-paging-20261004.json. This documentation/evidence commit records completed checks and pending decisions. Candidate dependency recipes, patches and controls remain uncommitted; production behavior and warning/publication policies do not change.

.. list-table:: Complete audit-changes checklist
   :header-rows: 1

   * - Check
     - Status
     - Evidence

   * - 1. Entry exists in doxygen/lang/120_modules.dox.tmpl (for modules in the Qore repo; N/A for external module repos)
     - N/A
     - Documentation/JSON evidence only. This item concerns executable code, APIs, module registration or runtime behavior absent from this commit.

   * - 2. Entry exists in doxygen/lang/900_release_notes.dox.tmpl (for modules in the Qore repo; external modules have release notes in their .qm)
     - N/A
     - Documentation/JSON evidence only. This item concerns executable code, APIs, module registration or runtime behavior absent from this commit.

   * - 3. qore_user_module() or qore_external_user_module() call in CMakeLists.txt
     - N/A
     - Documentation/JSON evidence only. This item concerns executable code, APIs, module registration or runtime behavior absent from this commit.

   * - 4. Module added to QMOD list in CMakeLists.txt
     - N/A
     - Documentation/JSON evidence only. This item concerns executable code, APIs, module registration or runtime behavior absent from this commit.

   * - 5. .qm file has @section <lowercasemodname>intro as first doc section — must be all lowercase (e.g., avrodataproviderintro, not AvroDataProviderintro)
     - N/A
     - Documentation/JSON evidence only. This item concerns executable code, APIs, module registration or runtime behavior absent from this commit.

   * - 6. %modern in .qm file — no redundant %new-style, %require-types, %strict-args, %enable-all-warnings
     - N/A
     - Documentation/JSON evidence only. This item concerns executable code, APIs, module registration or runtime behavior absent from this commit.

   * - 7. No parse directives (%requires, %modern, %new-style) in separated .qc files (check OUTSIDE of @code blocks only)
     - N/A
     - Documentation/JSON evidence only. This item concerns executable code, APIs, module registration or runtime behavior absent from this commit.

   * - 8. No %include usage (deprecated for modules)
     - N/A
     - Documentation/JSON evidence only. This item concerns executable code, APIs, module registration or runtime behavior absent from this commit.

   * - 9. Copyright 2026 on all new files
     - Pass
     - New evidence and this audit carry 2026 copyright.

   * - 10. Directory layout: .qm inside qlib/<ModuleName>/ directory (not at qlib/<ModuleName>.qm for multi-file modules)
     - N/A
     - Documentation/JSON evidence only. This item concerns executable code, APIs, module registration or runtime behavior absent from this commit.

   * - 11. No second .qm for the same module at qlib/<ModuleName>.qm
     - N/A
     - Documentation/JSON evidence only. This item concerns executable code, APIs, module registration or runtime behavior absent from this commit.

   * - 12. ns=Qore::XX matches the QoreNamespace constructor path
     - N/A
     - Documentation/JSON evidence only. This item concerns executable code, APIs, module registration or runtime behavior absent from this commit.

   * - 13. %modern directive present
     - N/A
     - Documentation/JSON evidence only. This item concerns executable code, APIs, module registration or runtime behavior absent from this commit.

   * - 14. Executable permission set (chmod +x)
     - N/A
     - Documentation/JSON evidence only. This item concerns executable code, APIs, module registration or runtime behavior absent from this commit.

   * - 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus)
     - N/A
     - Documentation/JSON evidence only. This item concerns executable code, APIs, module registration or runtime behavior absent from this commit.

   * - 16. External module dependencies use %try-module — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard %requires
     - N/A
     - Documentation/JSON evidence only. This item concerns executable code, APIs, module registration or runtime behavior absent from this commit.

   * - 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks
     - N/A
     - Documentation/JSON evidence only. This item concerns executable code, APIs, module registration or runtime behavior absent from this commit.

   * - 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks
     - N/A
     - Documentation/JSON evidence only. This item concerns executable code, APIs, module registration or runtime behavior absent from this commit.

   * - 19. If filesystem/network ops exist, verify QoreSandboxManagerHelper usage
     - N/A
     - Documentation/JSON evidence only. This item concerns executable code, APIs, module registration or runtime behavior absent from this commit.

   * - 20. No File::, Dir::, Socket::, HTTPClient:: usage without justification
     - N/A
     - Documentation/JSON evidence only. This item concerns executable code, APIs, module registration or runtime behavior absent from this commit.

   * - 21. All for/while loops that could iterate >100 times have qore_check_cancel() checks
     - N/A
     - Documentation/JSON evidence only. This item concerns executable code, APIs, module registration or runtime behavior absent from this commit.

   * - 22. Uses qore_check_cancel() (NOT deprecated qore_check_io_interrupt())
     - N/A
     - Documentation/JSON evidence only. This item concerns executable code, APIs, module registration or runtime behavior absent from this commit.

   * - 23. Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations
     - N/A
     - Documentation/JSON evidence only. This item concerns executable code, APIs, module registration or runtime behavior absent from this commit.

   * - 24. No blocking operations without cancellation support
     - N/A
     - Documentation/JSON evidence only. This item concerns executable code, APIs, module registration or runtime behavior absent from this commit.

   * - 25. Every action has display_name, short_desc (plain text, <80 chars), desc (markdown)
     - N/A
     - Documentation/JSON evidence only. This item concerns executable code, APIs, module registration or runtime behavior absent from this commit.

   * - 26. Every action has options populated via getActionOptionFromFields() — without this, the action shows an empty, unusable form
     - N/A
     - Documentation/JSON evidence only. This item concerns executable code, APIs, module registration or runtime behavior absent from this commit.

   * - 27. Every action has output_type set to a typed data type constant (e.g., MyResponseDataType) — not omitted
     - N/A
     - Documentation/JSON evidence only. This item concerns executable code, APIs, module registration or runtime behavior absent from this commit.

   * - 28. DPAT_API actions: provider has "supports_request": True and implements doRequestImpl()
     - N/A
     - Documentation/JSON evidence only. This item concerns executable code, APIs, module registration or runtime behavior absent from this commit.

   * - 29. DPAT_FIND actions: every option exists in SearchOptions, getRecordTypeImpl() returns *hash<string, AbstractDataField>
     - N/A
     - Documentation/JSON evidence only. This item concerns executable code, APIs, module registration or runtime behavior absent from this commit.

   * - 30. Scheme-based apps (with "scheme" in registerApp): actions use "path" and do NOT use "cls" — having both scheme and cls causes a runtime error
     - N/A
     - Documentation/JSON evidence only. This item concerns executable code, APIs, module registration or runtime behavior absent from this commit.

   * - 31. Single-key hash slices use trailing comma: Fields{"key",} (without trailing comma, Fields{"key"} returns the value, not a hash)
     - N/A
     - Documentation/JSON evidence only. This item concerns executable code, APIs, module registration or runtime behavior absent from this commit.

   * - 32. Typed data type classes exist for request and response types — inherit HashDataType, have const Fields hash, call addQoreFields(Fields) in constructor, export public constant at bottom (e.g., public const MyDataType = new MyDataType();)
     - N/A
     - Documentation/JSON evidence only. This item concerns executable code, APIs, module registration or runtime behavior absent from this commit.

   * - 33. Request/input types use public Fields (enables ClassName::Fields in action registration)
     - N/A
     - Documentation/JSON evidence only. This item concerns executable code, APIs, module registration or runtime behavior absent from this commit.

   * - 34. Response/output types use private Fields
     - N/A
     - Documentation/JSON evidence only. This item concerns executable code, APIs, module registration or runtime behavior absent from this commit.

   * - 35. Each field in data types has display_name, type, and desc (markdown-formatted)
     - N/A
     - Documentation/JSON evidence only. This item concerns executable code, APIs, module registration or runtime behavior absent from this commit.

   * - 36. Input fields have example_value where useful (string fields, endpoint URIs, SQL queries, etc.)
     - N/A
     - Documentation/JSON evidence only. This item concerns executable code, APIs, module registration or runtime behavior absent from this commit.

   * - 37. Fields with finite allowed values use allowed_values with AllowedValueInfo containing both value and display_name (Title Case, human-readable) — never bare values, never described only in text
     - N/A
     - Documentation/JSON evidence only. This item concerns executable code, APIs, module registration or runtime behavior absent from this commit.

   * - 38. Password/secret fields have "sensitive": True
     - N/A
     - Documentation/JSON evidence only. This item concerns executable code, APIs, module registration or runtime behavior absent from this commit.

   * - 39. groups uses AppGroup enum values from qlib/DataProvider/AppGroup.qc
     - N/A
     - Documentation/JSON evidence only. This item concerns executable code, APIs, module registration or runtime behavior absent from this commit.

   * - 40. App logo stored as separate file, loaded at module level in Priv namespace
     - N/A
     - Documentation/JSON evidence only. This item concerns executable code, APIs, module registration or runtime behavior absent from this commit.

   * - 41. App desc uses markdown: bullet list of capabilities, links to project website, business-language explanation of value
     - N/A
     - Documentation/JSON evidence only. This item concerns executable code, APIs, module registration or runtime behavior absent from this commit.

   * - 42. display_name is user-friendly ("Apache Avro" not "avro")
     - N/A
     - Documentation/JSON evidence only. This item concerns executable code, APIs, module registration or runtime behavior absent from this commit.

   * - 43. short_desc is plain text, under 80 chars, single sentence — no markdown
     - N/A
     - Documentation/JSON evidence only. This item concerns executable code, APIs, module registration or runtime behavior absent from this commit.

   * - 44. desc uses markdown: backticks for code/field refs ( field_name ,  True ,  pdf ), \n\n for paragraphs, -  bullet lists for enumerations, bold for caveats
     - N/A
     - Documentation/JSON evidence only. This item concerns executable code, APIs, module registration or runtime behavior absent from this commit.

   * - 45. Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use"
     - N/A
     - Documentation/JSON evidence only. This item concerns executable code, APIs, module registration or runtime behavior absent from this commit.

   * - 46. No bare True/False/NOTHING — must be backtick-wrapped in desc
     - N/A
     - Documentation/JSON evidence only. This item concerns executable code, APIs, module registration or runtime behavior absent from this commit.

   * - 47. No bare field/option names in prose — must use backticks
     - N/A
     - Documentation/JSON evidence only. This item concerns executable code, APIs, module registration or runtime behavior absent from this commit.

   * - 48. Long descriptions (>500 chars) use bold section headers and bullet lists
     - N/A
     - Documentation/JSON evidence only. This item concerns executable code, APIs, module registration or runtime behavior absent from this commit.

   * - 49. Factory registration in Qore repo: every factory name registered in qlib/DataProvider/DataProvider.qc → FactoryMap (without this, module loads but doesn't appear in Qorus apps)
     - N/A
     - Documentation/JSON evidence only. This item concerns executable code, APIs, module registration or runtime behavior absent from this commit.

   * - 50. getRecordTypeImpl() signature: must be private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options) — NOT returning *AbstractDataProviderType
     - N/A
     - Documentation/JSON evidence only. This item concerns executable code, APIs, module registration or runtime behavior absent from this commit.

   * - 51. Dependency JARs committed (for JNI modules): JAR files in qlib/*/jar/ may be gitignored — use git add -f to ensure they're tracked, otherwise CI compilation fails
     - N/A
     - Documentation/JSON evidence only. This item concerns executable code, APIs, module registration or runtime behavior absent from this commit.

   * - 52. JAR install rules in CMakeLists.txt for all dependency JARs
     - N/A
     - Documentation/JSON evidence only. This item concerns executable code, APIs, module registration or runtime behavior absent from this commit.

   * - 53. No workarounds: No TODOs, FIXMEs, stubs, or partially-implemented features
     - Pass
     - No runtime workaround is adopted. Three gRPC scopes, the NATS paging proposal and the existing Node decision remain pending. Fedora OBS retrieval remains unresolved.

   * - 54. Exception safety: C++ uses ReferenceHolder for Qore allocations, std::unique_ptr for C++ allocations, *xsink checked after every fallible operation
     - N/A
     - Documentation/JSON evidence only. This item concerns executable code, APIs, module registration or runtime behavior absent from this commit.

   * - 55. Thread safety: All mutable shared state protected by std::lock_guard<std::mutex> or documented as immutable-after-construction
     - N/A
     - Documentation/JSON evidence only. This item concerns executable code, APIs, module registration or runtime behavior absent from this commit.

   * - 56. Type safety: Strongly-typed code<return(args)> instead of untyped code; static_cast instead of C casts; typed hashdecls for results; enums where appropriate
     - N/A
     - Documentation/JSON evidence only. This item concerns executable code, APIs, module registration or runtime behavior absent from this commit.

   * - 57. Performance: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply
     - Pass
     - Candidate 14b reuses unchanged compiled sources through normal RPM --noprep build/install/check. Exact native-library equality avoids redundant Valgrind runs; all relevant new checks ran.

   * - 58. Error handling: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable
     - Pass
     - The failed metadata assertion and rejected NATS fixture experiments are explicitly recorded; no failed run is counted as qualification. Diagnostic counts distinguish existing approvals and pending requests.

   * - 59. Documentation: Doxygen @param, @return, @throw on all public methods; @par Example with realistic business scenarios; @note for important caveats
     - Pass
     - README and evidence explain roots, source/manifest changes, reproduction limits, qualification and outstanding release gates.

   * - 60. QPP flags: [flags=CONSTANT] on methods that never throw; [flags=RET_VALUE_ONLY] on methods that throw but have no side effects
     - N/A
     - Documentation/JSON evidence only. This item concerns executable code, APIs, module registration or runtime behavior absent from this commit.

   * - 61. Security: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code
     - Pass
     - Evidence contains commands, public source metadata and local artifact hashes; no credentials or secret values. OBS publication remains disabled.

   * - 62. Correctness: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features)
     - Pass
     - 188 evidence hashes verified. Full gRPC checks and both installed bridges pass. NATS route controls pass 480 cases; proposed paging fixture passes 39 runs. All 62 audit checklist items are classified.
