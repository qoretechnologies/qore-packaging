gRPC GCC 13 diagnostic control audit
====================================

Copyright 2026 Qore Technologies, s.r.o.

Scope: two standalone native controls, approved diagnostic evidence, remote release-policy application evidence, and status documentation. Every check below reviewed; package code and filters are outside this commit.

.. list-table:: Complete audit-changes checklist
   :header-rows: 1

   * - Check
     - Status
     - Evidence

   * - 1. Entry exists in doxygen/lang/120_modules.dox.tmpl (for modules in the Qore repo; N/A for external module repos)
     - N/A
     - Not applicable to standalone upstream diagnostic controls and packaging evidence: no Qore modules, QPP, provider APIs, sandboxed operations or public runtime interfaces changed.

   * - 2. Entry exists in doxygen/lang/900_release_notes.dox.tmpl (for modules in the Qore repo; external modules have release notes in their .qm)
     - N/A
     - Not applicable to standalone upstream diagnostic controls and packaging evidence: no Qore modules, QPP, provider APIs, sandboxed operations or public runtime interfaces changed.

   * - 3. qore_user_module() or qore_external_user_module() call in CMakeLists.txt
     - N/A
     - Not applicable to standalone upstream diagnostic controls and packaging evidence: no Qore modules, QPP, provider APIs, sandboxed operations or public runtime interfaces changed.

   * - 4. Module added to QMOD list in CMakeLists.txt
     - N/A
     - Not applicable to standalone upstream diagnostic controls and packaging evidence: no Qore modules, QPP, provider APIs, sandboxed operations or public runtime interfaces changed.

   * - 5. .qm file has @section <lowercasemodname>intro as first doc section — must be all lowercase (e.g., avrodataproviderintro, not AvroDataProviderintro)
     - N/A
     - Not applicable to standalone upstream diagnostic controls and packaging evidence: no Qore modules, QPP, provider APIs, sandboxed operations or public runtime interfaces changed.

   * - 6. %modern in .qm file — no redundant %new-style, %require-types, %strict-args, %enable-all-warnings
     - N/A
     - Not applicable to standalone upstream diagnostic controls and packaging evidence: no Qore modules, QPP, provider APIs, sandboxed operations or public runtime interfaces changed.

   * - 7. No parse directives (%requires, %modern, %new-style) in separated .qc files (check OUTSIDE of @code blocks only)
     - N/A
     - Not applicable to standalone upstream diagnostic controls and packaging evidence: no Qore modules, QPP, provider APIs, sandboxed operations or public runtime interfaces changed.

   * - 8. No %include usage (deprecated for modules)
     - N/A
     - Not applicable to standalone upstream diagnostic controls and packaging evidence: no Qore modules, QPP, provider APIs, sandboxed operations or public runtime interfaces changed.

   * - 9. Copyright 2026 on all new files
     - Pass
     - Both new controls and evidence carry copyright 2026.

   * - 10. Directory layout: .qm inside qlib/<ModuleName>/ directory (not at qlib/<ModuleName>.qm for multi-file modules)
     - N/A
     - Not applicable to standalone upstream diagnostic controls and packaging evidence: no Qore modules, QPP, provider APIs, sandboxed operations or public runtime interfaces changed.

   * - 11. No second .qm for the same module at qlib/<ModuleName>.qm
     - N/A
     - Not applicable to standalone upstream diagnostic controls and packaging evidence: no Qore modules, QPP, provider APIs, sandboxed operations or public runtime interfaces changed.

   * - 12. ns=Qore::XX matches the QoreNamespace constructor path
     - N/A
     - Not applicable to standalone upstream diagnostic controls and packaging evidence: no Qore modules, QPP, provider APIs, sandboxed operations or public runtime interfaces changed.

   * - 13. %modern directive present
     - N/A
     - Not applicable to standalone upstream diagnostic controls and packaging evidence: no Qore modules, QPP, provider APIs, sandboxed operations or public runtime interfaces changed.

   * - 14. Executable permission set (chmod +x)
     - N/A
     - Not applicable to standalone upstream diagnostic controls and packaging evidence: no Qore modules, QPP, provider APIs, sandboxed operations or public runtime interfaces changed.

   * - 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus)
     - N/A
     - Not applicable to standalone upstream diagnostic controls and packaging evidence: no Qore modules, QPP, provider APIs, sandboxed operations or public runtime interfaces changed.

   * - 16. External module dependencies use %try-module — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard %requires
     - N/A
     - Not applicable to standalone upstream diagnostic controls and packaging evidence: no Qore modules, QPP, provider APIs, sandboxed operations or public runtime interfaces changed.

   * - 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks
     - N/A
     - Not applicable to standalone upstream diagnostic controls and packaging evidence: no Qore modules, QPP, provider APIs, sandboxed operations or public runtime interfaces changed.

   * - 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks
     - N/A
     - Not applicable to standalone upstream diagnostic controls and packaging evidence: no Qore modules, QPP, provider APIs, sandboxed operations or public runtime interfaces changed.

   * - 19. If filesystem/network ops exist, verify QoreSandboxManagerHelper usage
     - N/A
     - Not applicable to standalone upstream diagnostic controls and packaging evidence: no Qore modules, QPP, provider APIs, sandboxed operations or public runtime interfaces changed.

   * - 20. No File::, Dir::, Socket::, HTTPClient:: usage without justification
     - N/A
     - Not applicable to standalone upstream diagnostic controls and packaging evidence: no Qore modules, QPP, provider APIs, sandboxed operations or public runtime interfaces changed.

   * - 21. All for/while loops that could iterate >100 times have qore_check_cancel() checks
     - N/A
     - Not applicable to standalone upstream diagnostic controls and packaging evidence: no Qore modules, QPP, provider APIs, sandboxed operations or public runtime interfaces changed.

   * - 22. Uses qore_check_cancel() (NOT deprecated qore_check_io_interrupt())
     - N/A
     - Not applicable to standalone upstream diagnostic controls and packaging evidence: no Qore modules, QPP, provider APIs, sandboxed operations or public runtime interfaces changed.

   * - 23. Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations
     - N/A
     - Not applicable to standalone upstream diagnostic controls and packaging evidence: no Qore modules, QPP, provider APIs, sandboxed operations or public runtime interfaces changed.

   * - 24. No blocking operations without cancellation support
     - N/A
     - Not applicable to standalone upstream diagnostic controls and packaging evidence: no Qore modules, QPP, provider APIs, sandboxed operations or public runtime interfaces changed.

   * - 25. Every action has display_name, short_desc (plain text, <80 chars), desc (markdown)
     - N/A
     - Not applicable to standalone upstream diagnostic controls and packaging evidence: no Qore modules, QPP, provider APIs, sandboxed operations or public runtime interfaces changed.

   * - 26. Every action has options populated via getActionOptionFromFields() — without this, the action shows an empty, unusable form
     - N/A
     - Not applicable to standalone upstream diagnostic controls and packaging evidence: no Qore modules, QPP, provider APIs, sandboxed operations or public runtime interfaces changed.

   * - 27. Every action has output_type set to a typed data type constant (e.g., MyResponseDataType) — not omitted
     - N/A
     - Not applicable to standalone upstream diagnostic controls and packaging evidence: no Qore modules, QPP, provider APIs, sandboxed operations or public runtime interfaces changed.

   * - 28. DPAT_API actions: provider has "supports_request": True and implements doRequestImpl()
     - N/A
     - Not applicable to standalone upstream diagnostic controls and packaging evidence: no Qore modules, QPP, provider APIs, sandboxed operations or public runtime interfaces changed.

   * - 29. DPAT_FIND actions: every option exists in SearchOptions, getRecordTypeImpl() returns *hash<string, AbstractDataField>
     - N/A
     - Not applicable to standalone upstream diagnostic controls and packaging evidence: no Qore modules, QPP, provider APIs, sandboxed operations or public runtime interfaces changed.

   * - 30. Scheme-based apps (with "scheme" in registerApp): actions use "path" and do NOT use "cls" — having both scheme and cls causes a runtime error
     - N/A
     - Not applicable to standalone upstream diagnostic controls and packaging evidence: no Qore modules, QPP, provider APIs, sandboxed operations or public runtime interfaces changed.

   * - 31. Single-key hash slices use trailing comma: Fields{"key",} (without trailing comma, Fields{"key"} returns the value, not a hash)
     - N/A
     - Not applicable to standalone upstream diagnostic controls and packaging evidence: no Qore modules, QPP, provider APIs, sandboxed operations or public runtime interfaces changed.

   * - 32. Typed data type classes exist for request and response types — inherit HashDataType, have const Fields hash, call addQoreFields(Fields) in constructor, export public constant at bottom (e.g., public const MyDataType = new MyDataType();)
     - N/A
     - Not applicable to standalone upstream diagnostic controls and packaging evidence: no Qore modules, QPP, provider APIs, sandboxed operations or public runtime interfaces changed.

   * - 33. Request/input types use public Fields (enables ClassName::Fields in action registration)
     - N/A
     - Not applicable to standalone upstream diagnostic controls and packaging evidence: no Qore modules, QPP, provider APIs, sandboxed operations or public runtime interfaces changed.

   * - 34. Response/output types use private Fields
     - N/A
     - Not applicable to standalone upstream diagnostic controls and packaging evidence: no Qore modules, QPP, provider APIs, sandboxed operations or public runtime interfaces changed.

   * - 35. Each field in data types has display_name, type, and desc (markdown-formatted)
     - N/A
     - Not applicable to standalone upstream diagnostic controls and packaging evidence: no Qore modules, QPP, provider APIs, sandboxed operations or public runtime interfaces changed.

   * - 36. Input fields have example_value where useful (string fields, endpoint URIs, SQL queries, etc.)
     - N/A
     - Not applicable to standalone upstream diagnostic controls and packaging evidence: no Qore modules, QPP, provider APIs, sandboxed operations or public runtime interfaces changed.

   * - 37. Fields with finite allowed values use allowed_values with AllowedValueInfo containing both value and display_name (Title Case, human-readable) — never bare values, never described only in text
     - N/A
     - Not applicable to standalone upstream diagnostic controls and packaging evidence: no Qore modules, QPP, provider APIs, sandboxed operations or public runtime interfaces changed.

   * - 38. Password/secret fields have "sensitive": True
     - N/A
     - Not applicable to standalone upstream diagnostic controls and packaging evidence: no Qore modules, QPP, provider APIs, sandboxed operations or public runtime interfaces changed.

   * - 39. groups uses AppGroup enum values from qlib/DataProvider/AppGroup.qc
     - N/A
     - Not applicable to standalone upstream diagnostic controls and packaging evidence: no Qore modules, QPP, provider APIs, sandboxed operations or public runtime interfaces changed.

   * - 40. App logo stored as separate file, loaded at module level in Priv namespace
     - N/A
     - Not applicable to standalone upstream diagnostic controls and packaging evidence: no Qore modules, QPP, provider APIs, sandboxed operations or public runtime interfaces changed.

   * - 41. App desc uses markdown: bullet list of capabilities, links to project website, business-language explanation of value
     - N/A
     - Not applicable to standalone upstream diagnostic controls and packaging evidence: no Qore modules, QPP, provider APIs, sandboxed operations or public runtime interfaces changed.

   * - 42. display_name is user-friendly ("Apache Avro" not "avro")
     - N/A
     - Not applicable to standalone upstream diagnostic controls and packaging evidence: no Qore modules, QPP, provider APIs, sandboxed operations or public runtime interfaces changed.

   * - 43. short_desc is plain text, under 80 chars, single sentence — no markdown
     - N/A
     - Not applicable to standalone upstream diagnostic controls and packaging evidence: no Qore modules, QPP, provider APIs, sandboxed operations or public runtime interfaces changed.

   * - 44. desc uses markdown: backticks for code/field refs ( field_name ,  True ,  pdf ), \n\n for paragraphs, -  bullet lists for enumerations, bold for caveats
     - N/A
     - Not applicable to standalone upstream diagnostic controls and packaging evidence: no Qore modules, QPP, provider APIs, sandboxed operations or public runtime interfaces changed.

   * - 45. Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use"
     - N/A
     - Not applicable to standalone upstream diagnostic controls and packaging evidence: no Qore modules, QPP, provider APIs, sandboxed operations or public runtime interfaces changed.

   * - 46. No bare True/False/NOTHING — must be backtick-wrapped in desc
     - N/A
     - Not applicable to standalone upstream diagnostic controls and packaging evidence: no Qore modules, QPP, provider APIs, sandboxed operations or public runtime interfaces changed.

   * - 47. No bare field/option names in prose — must use backticks
     - N/A
     - Not applicable to standalone upstream diagnostic controls and packaging evidence: no Qore modules, QPP, provider APIs, sandboxed operations or public runtime interfaces changed.

   * - 48. Long descriptions (>500 chars) use bold section headers and bullet lists
     - N/A
     - Not applicable to standalone upstream diagnostic controls and packaging evidence: no Qore modules, QPP, provider APIs, sandboxed operations or public runtime interfaces changed.

   * - 49. Factory registration in Qore repo: every factory name registered in qlib/DataProvider/DataProvider.qc → FactoryMap (without this, module loads but doesn't appear in Qorus apps)
     - N/A
     - Not applicable to standalone upstream diagnostic controls and packaging evidence: no Qore modules, QPP, provider APIs, sandboxed operations or public runtime interfaces changed.

   * - 50. getRecordTypeImpl() signature: must be private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options) — NOT returning *AbstractDataProviderType
     - N/A
     - Not applicable to standalone upstream diagnostic controls and packaging evidence: no Qore modules, QPP, provider APIs, sandboxed operations or public runtime interfaces changed.

   * - 51. Dependency JARs committed (for JNI modules): JAR files in qlib/*/jar/ may be gitignored — use git add -f to ensure they're tracked, otherwise CI compilation fails
     - N/A
     - Not applicable to standalone upstream diagnostic controls and packaging evidence: no Qore modules, QPP, provider APIs, sandboxed operations or public runtime interfaces changed.

   * - 52. JAR install rules in CMakeLists.txt for all dependency JARs
     - N/A
     - Not applicable to standalone upstream diagnostic controls and packaging evidence: no Qore modules, QPP, provider APIs, sandboxed operations or public runtime interfaces changed.

   * - 53. No workarounds: No TODOs, FIXMEs, stubs, or partially-implemented features
     - Pass
     - Four exact compiler sites are explicitly approved on 2026-10-04; no changed compiler flags, suppression or production workaround.

   * - 54. Exception safety: C++ uses ReferenceHolder for Qore allocations, std::unique_ptr for C++ allocations, *xsink checked after every fallible operation
     - Pass
     - C++ status and sequence resources use upstream RAII; C arenas are checked before use and freed. Assertion failures abort these standalone controls.

   * - 55. Thread safety: All mutable shared state protected by std::lock_guard<std::mutex> or documented as immutable-after-construction
     - Pass
     - Controls are single-threaded; Wakeable counters have no concurrent access.

   * - 56. Type safety: Strongly-typed code<return(args)> instead of untyped code; static_cast instead of C casts; typed hashdecls for results; enums where appropriate
     - Pass
     - C++ typed promises and Wakeable overrides; C uses the upstream generic-message API and explicit conversions.

   * - 57. Performance: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply
     - Pass
     - Bounded linear stress loops; no production-path change.

   * - 58. Error handling: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable
     - Pass
     - Malformed wire rejection and checked arena/parse/clone/serialization results; source arena freed before clone validation.

   * - 59. Documentation: Doxygen @param, @return, @throw on all public methods; @par Example with realistic business scenarios; @note for important caveats
     - Pass
     - Evidence records exact source/flag reproduction, local-vs-OBS limits, linker harness correction and narrow user approval.

   * - 60. QPP flags: [flags=CONSTANT] on methods that never throw; [flags=RET_VALUE_ONLY] on methods that throw but have no side effects
     - N/A
     - Not applicable to standalone upstream diagnostic controls and packaging evidence: no Qore modules, QPP, provider APIs, sandboxed operations or public runtime interfaces changed.

   * - 61. Security: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code
     - Pass
     - Constant wire inputs; compared lengths checked before memcmp. No credentials or uncontrolled formatting.

   * - 62. Correctness: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features)
     - Pass
     - 60000 sequence-state and ownership checks plus 100000 deep clones and two malformed wires. Valgrind zero errors and zero lost allocations; all evidence hashes verified.
