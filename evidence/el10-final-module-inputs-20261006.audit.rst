AlmaLinux final native module input audit
=========================================

Copyright 2026 Qore Technologies, s.r.o.

Scope: AlmaLinux ARM SSH2/PROJ and PostgreSQL signed package manifests, CI jobs and qualification documentation; no module runtime changes.

.. list-table:: Complete audit-changes checklist
   :header-rows: 1

   * - Check
     - Status
     - Evidence

   * - 1. Entry exists in doxygen/lang/120_modules.dox.tmpl (for modules in the Qore repo; N/A for external module repos)
     - N/A
     - Manifest/CI/documentation scope: no new Qore/C++ APIs, providers, cancellation, sandbox operations or dependency JARs.

   * - 2. Entry exists in doxygen/lang/900_release_notes.dox.tmpl (for modules in the Qore repo; external modules have release notes in their .qm)
     - N/A
     - Manifest/CI/documentation scope: no new Qore/C++ APIs, providers, cancellation, sandbox operations or dependency JARs.

   * - 3. qore_user_module() or qore_external_user_module() call in CMakeLists.txt
     - N/A
     - Manifest/CI/documentation scope: no new Qore/C++ APIs, providers, cancellation, sandbox operations or dependency JARs.

   * - 4. Module added to QMOD list in CMakeLists.txt
     - N/A
     - Manifest/CI/documentation scope: no new Qore/C++ APIs, providers, cancellation, sandbox operations or dependency JARs.

   * - 5. .qm file has @section <lowercasemodname>intro as first doc section — must be all lowercase (e.g., avrodataproviderintro, not AvroDataProviderintro)
     - N/A
     - Manifest/CI/documentation scope: no new Qore/C++ APIs, providers, cancellation, sandbox operations or dependency JARs.

   * - 6. %modern in .qm file — no redundant %new-style, %require-types, %strict-args, %enable-all-warnings
     - N/A
     - Manifest/CI/documentation scope: no new Qore/C++ APIs, providers, cancellation, sandbox operations or dependency JARs.

   * - 7. No parse directives (%requires, %modern, %new-style) in separated .qc files (check OUTSIDE of @code blocks only)
     - N/A
     - Manifest/CI/documentation scope: no new Qore/C++ APIs, providers, cancellation, sandbox operations or dependency JARs.

   * - 8. No %include usage (deprecated for modules)
     - N/A
     - Manifest/CI/documentation scope: no new Qore/C++ APIs, providers, cancellation, sandbox operations or dependency JARs.

   * - 9. Copyright 2026 on all new files
     - Pass
     - New files carry 2026 copyright metadata.

   * - 10. Directory layout: .qm inside qlib/<ModuleName>/ directory (not at qlib/<ModuleName>.qm for multi-file modules)
     - N/A
     - Manifest/CI/documentation scope: no new Qore/C++ APIs, providers, cancellation, sandbox operations or dependency JARs.

   * - 11. No second .qm for the same module at qlib/<ModuleName>.qm
     - N/A
     - Manifest/CI/documentation scope: no new Qore/C++ APIs, providers, cancellation, sandbox operations or dependency JARs.

   * - 12. ns=Qore::XX matches the QoreNamespace constructor path
     - N/A
     - Manifest/CI/documentation scope: no new Qore/C++ APIs, providers, cancellation, sandbox operations or dependency JARs.

   * - 13. %modern directive present
     - N/A
     - Manifest/CI/documentation scope: no new Qore/C++ APIs, providers, cancellation, sandbox operations or dependency JARs.

   * - 14. Executable permission set (chmod +x)
     - N/A
     - Manifest/CI/documentation scope: no new Qore/C++ APIs, providers, cancellation, sandbox operations or dependency JARs.

   * - 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus)
     - N/A
     - Manifest/CI/documentation scope: no new Qore/C++ APIs, providers, cancellation, sandbox operations or dependency JARs.

   * - 16. External module dependencies use %try-module — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard %requires
     - N/A
     - Manifest/CI/documentation scope: no new Qore/C++ APIs, providers, cancellation, sandbox operations or dependency JARs.

   * - 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks
     - N/A
     - Manifest/CI/documentation scope: no new Qore/C++ APIs, providers, cancellation, sandbox operations or dependency JARs.

   * - 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks
     - N/A
     - Manifest/CI/documentation scope: no new Qore/C++ APIs, providers, cancellation, sandbox operations or dependency JARs.

   * - 19. If filesystem/network ops exist, verify QoreSandboxManagerHelper usage
     - N/A
     - Manifest/CI/documentation scope: no new Qore/C++ APIs, providers, cancellation, sandbox operations or dependency JARs.

   * - 20. No File::, Dir::, Socket::, HTTPClient:: usage without justification
     - N/A
     - Manifest/CI/documentation scope: no new Qore/C++ APIs, providers, cancellation, sandbox operations or dependency JARs.

   * - 21. All for/while loops that could iterate >100 times have qore_check_cancel() checks
     - N/A
     - Manifest/CI/documentation scope: no new Qore/C++ APIs, providers, cancellation, sandbox operations or dependency JARs.

   * - 22. Uses qore_check_cancel() (NOT deprecated qore_check_io_interrupt())
     - N/A
     - Manifest/CI/documentation scope: no new Qore/C++ APIs, providers, cancellation, sandbox operations or dependency JARs.

   * - 23. Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations
     - N/A
     - Manifest/CI/documentation scope: no new Qore/C++ APIs, providers, cancellation, sandbox operations or dependency JARs.

   * - 24. No blocking operations without cancellation support
     - N/A
     - Manifest/CI/documentation scope: no new Qore/C++ APIs, providers, cancellation, sandbox operations or dependency JARs.

   * - 25. Every action has display_name, short_desc (plain text, <80 chars), desc (markdown)
     - N/A
     - Manifest/CI/documentation scope: no new Qore/C++ APIs, providers, cancellation, sandbox operations or dependency JARs.

   * - 26. Every action has options populated via getActionOptionFromFields() — without this, the action shows an empty, unusable form
     - N/A
     - Manifest/CI/documentation scope: no new Qore/C++ APIs, providers, cancellation, sandbox operations or dependency JARs.

   * - 27. Every action has output_type set to a typed data type constant (e.g., MyResponseDataType) — not omitted
     - N/A
     - Manifest/CI/documentation scope: no new Qore/C++ APIs, providers, cancellation, sandbox operations or dependency JARs.

   * - 28. DPAT_API actions: provider has "supports_request": True and implements doRequestImpl()
     - N/A
     - Manifest/CI/documentation scope: no new Qore/C++ APIs, providers, cancellation, sandbox operations or dependency JARs.

   * - 29. DPAT_FIND actions: every option exists in SearchOptions, getRecordTypeImpl() returns *hash<string, AbstractDataField>
     - N/A
     - Manifest/CI/documentation scope: no new Qore/C++ APIs, providers, cancellation, sandbox operations or dependency JARs.

   * - 30. Scheme-based apps (with "scheme" in registerApp): actions use "path" and do NOT use "cls" — having both scheme and cls causes a runtime error
     - N/A
     - Manifest/CI/documentation scope: no new Qore/C++ APIs, providers, cancellation, sandbox operations or dependency JARs.

   * - 31. Single-key hash slices use trailing comma: Fields{"key",} (without trailing comma, Fields{"key"} returns the value, not a hash)
     - N/A
     - Manifest/CI/documentation scope: no new Qore/C++ APIs, providers, cancellation, sandbox operations or dependency JARs.

   * - 32. Typed data type classes exist for request and response types — inherit HashDataType, have const Fields hash, call addQoreFields(Fields) in constructor, export public constant at bottom (e.g., public const MyDataType = new MyDataType();)
     - N/A
     - Manifest/CI/documentation scope: no new Qore/C++ APIs, providers, cancellation, sandbox operations or dependency JARs.

   * - 33. Request/input types use public Fields (enables ClassName::Fields in action registration)
     - N/A
     - Manifest/CI/documentation scope: no new Qore/C++ APIs, providers, cancellation, sandbox operations or dependency JARs.

   * - 34. Response/output types use private Fields
     - N/A
     - Manifest/CI/documentation scope: no new Qore/C++ APIs, providers, cancellation, sandbox operations or dependency JARs.

   * - 35. Each field in data types has display_name, type, and desc (markdown-formatted)
     - N/A
     - Manifest/CI/documentation scope: no new Qore/C++ APIs, providers, cancellation, sandbox operations or dependency JARs.

   * - 36. Input fields have example_value where useful (string fields, endpoint URIs, SQL queries, etc.)
     - N/A
     - Manifest/CI/documentation scope: no new Qore/C++ APIs, providers, cancellation, sandbox operations or dependency JARs.

   * - 37. Fields with finite allowed values use allowed_values with AllowedValueInfo containing both value and display_name (Title Case, human-readable) — never bare values, never described only in text
     - N/A
     - Manifest/CI/documentation scope: no new Qore/C++ APIs, providers, cancellation, sandbox operations or dependency JARs.

   * - 38. Password/secret fields have "sensitive": True
     - N/A
     - Manifest/CI/documentation scope: no new Qore/C++ APIs, providers, cancellation, sandbox operations or dependency JARs.

   * - 39. groups uses AppGroup enum values from qlib/DataProvider/AppGroup.qc
     - N/A
     - Manifest/CI/documentation scope: no new Qore/C++ APIs, providers, cancellation, sandbox operations or dependency JARs.

   * - 40. App logo stored as separate file, loaded at module level in Priv namespace
     - N/A
     - Manifest/CI/documentation scope: no new Qore/C++ APIs, providers, cancellation, sandbox operations or dependency JARs.

   * - 41. App desc uses markdown: bullet list of capabilities, links to project website, business-language explanation of value
     - N/A
     - Manifest/CI/documentation scope: no new Qore/C++ APIs, providers, cancellation, sandbox operations or dependency JARs.

   * - 42. display_name is user-friendly ("Apache Avro" not "avro")
     - N/A
     - Manifest/CI/documentation scope: no new Qore/C++ APIs, providers, cancellation, sandbox operations or dependency JARs.

   * - 43. short_desc is plain text, under 80 chars, single sentence — no markdown
     - N/A
     - Manifest/CI/documentation scope: no new Qore/C++ APIs, providers, cancellation, sandbox operations or dependency JARs.

   * - 44. desc uses markdown: backticks for code/field refs ( field_name ,  True ,  pdf ), \n\n for paragraphs, -  bullet lists for enumerations, bold for caveats
     - N/A
     - Manifest/CI/documentation scope: no new Qore/C++ APIs, providers, cancellation, sandbox operations or dependency JARs.

   * - 45. Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use"
     - N/A
     - Manifest/CI/documentation scope: no new Qore/C++ APIs, providers, cancellation, sandbox operations or dependency JARs.

   * - 46. No bare True/False/NOTHING — must be backtick-wrapped in desc
     - N/A
     - Manifest/CI/documentation scope: no new Qore/C++ APIs, providers, cancellation, sandbox operations or dependency JARs.

   * - 47. No bare field/option names in prose — must use backticks
     - N/A
     - Manifest/CI/documentation scope: no new Qore/C++ APIs, providers, cancellation, sandbox operations or dependency JARs.

   * - 48. Long descriptions (>500 chars) use bold section headers and bullet lists
     - N/A
     - Manifest/CI/documentation scope: no new Qore/C++ APIs, providers, cancellation, sandbox operations or dependency JARs.

   * - 49. Factory registration in Qore repo: every factory name registered in qlib/DataProvider/DataProvider.qc → FactoryMap (without this, module loads but doesn't appear in Qorus apps)
     - N/A
     - Manifest/CI/documentation scope: no new Qore/C++ APIs, providers, cancellation, sandbox operations or dependency JARs.

   * - 50. getRecordTypeImpl() signature: must be private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options) — NOT returning *AbstractDataProviderType
     - N/A
     - Manifest/CI/documentation scope: no new Qore/C++ APIs, providers, cancellation, sandbox operations or dependency JARs.

   * - 51. Dependency JARs committed (for JNI modules): JAR files in qlib/*/jar/ may be gitignored — use git add -f to ensure they're tracked, otherwise CI compilation fails
     - N/A
     - Manifest/CI/documentation scope: no new Qore/C++ APIs, providers, cancellation, sandbox operations or dependency JARs.

   * - 52. JAR install rules in CMakeLists.txt for all dependency JARs
     - N/A
     - Manifest/CI/documentation scope: no new Qore/C++ APIs, providers, cancellation, sandbox operations or dependency JARs.

   * - 53. No workarounds: No TODOs, FIXMEs, stubs, or partially-implemented features
     - Pass
     - No suppression, compiler change, bypass or weakened gate.

   * - 54. Exception safety: C++ uses ReferenceHolder for Qore allocations, std::unique_ptr for C++ allocations, *xsink checked after every fallible operation
     - N/A
     - Manifest/CI/documentation scope: no new Qore/C++ APIs, providers, cancellation, sandbox operations or dependency JARs.

   * - 55. Thread safety: All mutable shared state protected by std::lock_guard<std::mutex> or documented as immutable-after-construction
     - Pass
     - Independent CI jobs use fresh isolated images and immutable digest checks.

   * - 56. Type safety: Strongly-typed code<return(args)> instead of untyped code; static_cast instead of C casts; typed hashdecls for results; enums where appropriate
     - N/A
     - Manifest/CI/documentation scope: no new Qore/C++ APIs, providers, cancellation, sandbox operations or dependency JARs.

   * - 57. Performance: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply
     - N/A
     - Manifest/CI/documentation scope: no new Qore/C++ APIs, providers, cancellation, sandbox operations or dependency JARs.

   * - 58. Error handling: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable
     - Pass
     - Runner validates manifests before installation and checks every package signature/hash; stale filename detected and dependency inputs refreshed from current OBS build.

   * - 59. Documentation: Doxygen @param, @return, @throw on all public methods; @par Example with realistic business scenarios; @note for important caveats
     - Pass
     - Documents native inputs ready and installed results pending; prior Fedora/Leap evidence preserved.

   * - 60. QPP flags: [flags=CONSTANT] on methods that never throw; [flags=RET_VALUE_ONLY] on methods that throw but have no side effects
     - N/A
     - Manifest/CI/documentation scope: no new Qore/C++ APIs, providers, cancellation, sandbox operations or dependency JARs.

   * - 61. Security: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code
     - Pass
     - Only public OBS RPM and immutable Git fixture URLs; existing signing-key digest and validation retained.

   * - 62. Correctness: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features)
     - Pass
     - All 176 packaging tests and GitLab CI lint pass; 18 public RPM payload digests verified. Native source histories match qualified catalog pins; installed checks are pending.
