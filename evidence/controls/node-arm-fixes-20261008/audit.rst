Node ARM declaration fixes audit
================================

Copyright 2026 Qore Technologies, s.r.o.

Scope: two private upstream source fixes, native RPM regressions, package recipe and retained qualification. All 62 checks: 13 Pass, 49 N/A, 0 Fail. Native ARM build and installed-package execution remain required.

.. list-table:: Complete audit-changes checklist
   :header-rows: 1

   * - Check
     - Status
     - Evidence

   * - 1. Entry exists in doxygen/lang/120_modules.dox.tmpl (for modules in the Qore repo; N/A for external module repos)
     - N/A
     - No corresponding Qore module, QPP, DataProvider, JNI or Qore-language test change. Production changes add no iteration or cancellation point; bounded standalone controls do not execute inside a Qore program.

   * - 2. Entry exists in doxygen/lang/900_release_notes.dox.tmpl (for modules in the Qore repo; external modules have release notes in their .qm)
     - N/A
     - No corresponding Qore module, QPP, DataProvider, JNI or Qore-language test change. Production changes add no iteration or cancellation point; bounded standalone controls do not execute inside a Qore program.

   * - 3. qore_user_module() or qore_external_user_module() call in CMakeLists.txt
     - N/A
     - No corresponding Qore module, QPP, DataProvider, JNI or Qore-language test change. Production changes add no iteration or cancellation point; bounded standalone controls do not execute inside a Qore program.

   * - 4. Module added to QMOD list in CMakeLists.txt
     - N/A
     - No corresponding Qore module, QPP, DataProvider, JNI or Qore-language test change. Production changes add no iteration or cancellation point; bounded standalone controls do not execute inside a Qore program.

   * - 5. .qm file has @section <lowercasemodname>intro as first doc section — must be all lowercase (e.g., avrodataproviderintro, not AvroDataProviderintro)
     - N/A
     - No corresponding Qore module, QPP, DataProvider, JNI or Qore-language test change. Production changes add no iteration or cancellation point; bounded standalone controls do not execute inside a Qore program.

   * - 6. %modern in .qm file — no redundant %new-style, %require-types, %strict-args, %enable-all-warnings
     - N/A
     - No corresponding Qore module, QPP, DataProvider, JNI or Qore-language test change. Production changes add no iteration or cancellation point; bounded standalone controls do not execute inside a Qore program.

   * - 7. No parse directives (%requires, %modern, %new-style) in separated .qc files (check OUTSIDE of @code blocks only)
     - N/A
     - No corresponding Qore module, QPP, DataProvider, JNI or Qore-language test change. Production changes add no iteration or cancellation point; bounded standalone controls do not execute inside a Qore program.

   * - 8. No %include usage (deprecated for modules)
     - N/A
     - No corresponding Qore module, QPP, DataProvider, JNI or Qore-language test change. Production changes add no iteration or cancellation point; bounded standalone controls do not execute inside a Qore program.

   * - 9. Copyright 2026 on all new files
     - Pass
     - All new package controls, patches and evidence scripts carry 2026 copyright; verbatim upstream material retains its license.

   * - 10. Directory layout: .qm inside qlib/<ModuleName>/ directory (not at qlib/<ModuleName>.qm for multi-file modules)
     - N/A
     - No corresponding Qore module, QPP, DataProvider, JNI or Qore-language test change. Production changes add no iteration or cancellation point; bounded standalone controls do not execute inside a Qore program.

   * - 11. No second .qm for the same module at qlib/<ModuleName>.qm
     - N/A
     - No corresponding Qore module, QPP, DataProvider, JNI or Qore-language test change. Production changes add no iteration or cancellation point; bounded standalone controls do not execute inside a Qore program.

   * - 12. ns=Qore::XX matches the QoreNamespace constructor path
     - N/A
     - No corresponding Qore module, QPP, DataProvider, JNI or Qore-language test change. Production changes add no iteration or cancellation point; bounded standalone controls do not execute inside a Qore program.

   * - 13. %modern directive present
     - N/A
     - No corresponding Qore module, QPP, DataProvider, JNI or Qore-language test change. Production changes add no iteration or cancellation point; bounded standalone controls do not execute inside a Qore program.

   * - 14. Executable permission set (chmod +x)
     - N/A
     - No corresponding Qore module, QPP, DataProvider, JNI or Qore-language test change. Production changes add no iteration or cancellation point; bounded standalone controls do not execute inside a Qore program.

   * - 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus)
     - N/A
     - No corresponding Qore module, QPP, DataProvider, JNI or Qore-language test change. Production changes add no iteration or cancellation point; bounded standalone controls do not execute inside a Qore program.

   * - 16. External module dependencies use %try-module — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard %requires
     - N/A
     - No corresponding Qore module, QPP, DataProvider, JNI or Qore-language test change. Production changes add no iteration or cancellation point; bounded standalone controls do not execute inside a Qore program.

   * - 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks
     - Pass
     - The production C/C++ patches add no filesystem operations. The Python test writes only explicit build-output paths.

   * - 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks
     - Pass
     - The production patches and controls add no network access; local controls run in network-disabled containers.

   * - 19. If filesystem/network ops exist, verify QoreSandboxManagerHelper usage
     - N/A
     - No corresponding Qore module, QPP, DataProvider, JNI or Qore-language test change. Production changes add no iteration or cancellation point; bounded standalone controls do not execute inside a Qore program.

   * - 20. No File::, Dir::, Socket::, HTTPClient:: usage without justification
     - N/A
     - No corresponding Qore module, QPP, DataProvider, JNI or Qore-language test change. Production changes add no iteration or cancellation point; bounded standalone controls do not execute inside a Qore program.

   * - 21. All for/while loops that could iterate >100 times have qore_check_cancel() checks
     - N/A
     - No corresponding Qore module, QPP, DataProvider, JNI or Qore-language test change. Production changes add no iteration or cancellation point; bounded standalone controls do not execute inside a Qore program.

   * - 22. Uses qore_check_cancel() (NOT deprecated qore_check_io_interrupt())
     - N/A
     - No corresponding Qore module, QPP, DataProvider, JNI or Qore-language test change. Production changes add no iteration or cancellation point; bounded standalone controls do not execute inside a Qore program.

   * - 23. Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations
     - N/A
     - No corresponding Qore module, QPP, DataProvider, JNI or Qore-language test change. Production changes add no iteration or cancellation point; bounded standalone controls do not execute inside a Qore program.

   * - 24. No blocking operations without cancellation support
     - Pass
     - Both production changes select existing expressions/declarations and add no blocking operation.

   * - 25. Every action has display_name, short_desc (plain text, <80 chars), desc (markdown)
     - N/A
     - No corresponding Qore module, QPP, DataProvider, JNI or Qore-language test change. Production changes add no iteration or cancellation point; bounded standalone controls do not execute inside a Qore program.

   * - 26. Every action has options populated via getActionOptionFromFields() — without this, the action shows an empty, unusable form
     - N/A
     - No corresponding Qore module, QPP, DataProvider, JNI or Qore-language test change. Production changes add no iteration or cancellation point; bounded standalone controls do not execute inside a Qore program.

   * - 27. Every action has output_type set to a typed data type constant (e.g., MyResponseDataType) — not omitted
     - N/A
     - No corresponding Qore module, QPP, DataProvider, JNI or Qore-language test change. Production changes add no iteration or cancellation point; bounded standalone controls do not execute inside a Qore program.

   * - 28. DPAT_API actions: provider has "supports_request": True and implements doRequestImpl()
     - N/A
     - No corresponding Qore module, QPP, DataProvider, JNI or Qore-language test change. Production changes add no iteration or cancellation point; bounded standalone controls do not execute inside a Qore program.

   * - 29. DPAT_FIND actions: every option exists in SearchOptions, getRecordTypeImpl() returns *hash<string, AbstractDataField>
     - N/A
     - No corresponding Qore module, QPP, DataProvider, JNI or Qore-language test change. Production changes add no iteration or cancellation point; bounded standalone controls do not execute inside a Qore program.

   * - 30. Scheme-based apps (with "scheme" in registerApp): actions use "path" and do NOT use "cls" — having both scheme and cls causes a runtime error
     - N/A
     - No corresponding Qore module, QPP, DataProvider, JNI or Qore-language test change. Production changes add no iteration or cancellation point; bounded standalone controls do not execute inside a Qore program.

   * - 31. Single-key hash slices use trailing comma: Fields{"key",} (without trailing comma, Fields{"key"} returns the value, not a hash)
     - N/A
     - No corresponding Qore module, QPP, DataProvider, JNI or Qore-language test change. Production changes add no iteration or cancellation point; bounded standalone controls do not execute inside a Qore program.

   * - 32. Typed data type classes exist for request and response types — inherit HashDataType, have const Fields hash, call addQoreFields(Fields) in constructor, export public constant at bottom (e.g., public const MyDataType = new MyDataType();)
     - N/A
     - No corresponding Qore module, QPP, DataProvider, JNI or Qore-language test change. Production changes add no iteration or cancellation point; bounded standalone controls do not execute inside a Qore program.

   * - 33. Request/input types use public Fields (enables ClassName::Fields in action registration)
     - N/A
     - No corresponding Qore module, QPP, DataProvider, JNI or Qore-language test change. Production changes add no iteration or cancellation point; bounded standalone controls do not execute inside a Qore program.

   * - 34. Response/output types use private Fields
     - N/A
     - No corresponding Qore module, QPP, DataProvider, JNI or Qore-language test change. Production changes add no iteration or cancellation point; bounded standalone controls do not execute inside a Qore program.

   * - 35. Each field in data types has display_name, type, and desc (markdown-formatted)
     - N/A
     - No corresponding Qore module, QPP, DataProvider, JNI or Qore-language test change. Production changes add no iteration or cancellation point; bounded standalone controls do not execute inside a Qore program.

   * - 36. Input fields have example_value where useful (string fields, endpoint URIs, SQL queries, etc.)
     - N/A
     - No corresponding Qore module, QPP, DataProvider, JNI or Qore-language test change. Production changes add no iteration or cancellation point; bounded standalone controls do not execute inside a Qore program.

   * - 37. Fields with finite allowed values use allowed_values with AllowedValueInfo containing both value and display_name (Title Case, human-readable) — never bare values, never described only in text
     - N/A
     - No corresponding Qore module, QPP, DataProvider, JNI or Qore-language test change. Production changes add no iteration or cancellation point; bounded standalone controls do not execute inside a Qore program.

   * - 38. Password/secret fields have "sensitive": True
     - N/A
     - No corresponding Qore module, QPP, DataProvider, JNI or Qore-language test change. Production changes add no iteration or cancellation point; bounded standalone controls do not execute inside a Qore program.

   * - 39. groups uses AppGroup enum values from qlib/DataProvider/AppGroup.qc
     - N/A
     - No corresponding Qore module, QPP, DataProvider, JNI or Qore-language test change. Production changes add no iteration or cancellation point; bounded standalone controls do not execute inside a Qore program.

   * - 40. App logo stored as separate file, loaded at module level in Priv namespace
     - N/A
     - No corresponding Qore module, QPP, DataProvider, JNI or Qore-language test change. Production changes add no iteration or cancellation point; bounded standalone controls do not execute inside a Qore program.

   * - 41. App desc uses markdown: bullet list of capabilities, links to project website, business-language explanation of value
     - N/A
     - No corresponding Qore module, QPP, DataProvider, JNI or Qore-language test change. Production changes add no iteration or cancellation point; bounded standalone controls do not execute inside a Qore program.

   * - 42. display_name is user-friendly ("Apache Avro" not "avro")
     - N/A
     - No corresponding Qore module, QPP, DataProvider, JNI or Qore-language test change. Production changes add no iteration or cancellation point; bounded standalone controls do not execute inside a Qore program.

   * - 43. short_desc is plain text, under 80 chars, single sentence — no markdown
     - N/A
     - No corresponding Qore module, QPP, DataProvider, JNI or Qore-language test change. Production changes add no iteration or cancellation point; bounded standalone controls do not execute inside a Qore program.

   * - 44. desc uses markdown: backticks for code/field refs ( field_name ,  True ,  pdf ), \n\n for paragraphs, -  bullet lists for enumerations, bold for caveats
     - N/A
     - No corresponding Qore module, QPP, DataProvider, JNI or Qore-language test change. Production changes add no iteration or cancellation point; bounded standalone controls do not execute inside a Qore program.

   * - 45. Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use"
     - N/A
     - No corresponding Qore module, QPP, DataProvider, JNI or Qore-language test change. Production changes add no iteration or cancellation point; bounded standalone controls do not execute inside a Qore program.

   * - 46. No bare True/False/NOTHING — must be backtick-wrapped in desc
     - N/A
     - No corresponding Qore module, QPP, DataProvider, JNI or Qore-language test change. Production changes add no iteration or cancellation point; bounded standalone controls do not execute inside a Qore program.

   * - 47. No bare field/option names in prose — must use backticks
     - N/A
     - No corresponding Qore module, QPP, DataProvider, JNI or Qore-language test change. Production changes add no iteration or cancellation point; bounded standalone controls do not execute inside a Qore program.

   * - 48. Long descriptions (>500 chars) use bold section headers and bullet lists
     - N/A
     - No corresponding Qore module, QPP, DataProvider, JNI or Qore-language test change. Production changes add no iteration or cancellation point; bounded standalone controls do not execute inside a Qore program.

   * - 49. Factory registration in Qore repo: every factory name registered in qlib/DataProvider/DataProvider.qc → FactoryMap (without this, module loads but doesn't appear in Qorus apps)
     - N/A
     - No corresponding Qore module, QPP, DataProvider, JNI or Qore-language test change. Production changes add no iteration or cancellation point; bounded standalone controls do not execute inside a Qore program.

   * - 50. getRecordTypeImpl() signature: must be private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options) — NOT returning *AbstractDataProviderType
     - N/A
     - No corresponding Qore module, QPP, DataProvider, JNI or Qore-language test change. Production changes add no iteration or cancellation point; bounded standalone controls do not execute inside a Qore program.

   * - 51. Dependency JARs committed (for JNI modules): JAR files in qlib/*/jar/ may be gitignored — use git add -f to ensure they're tracked, otherwise CI compilation fails
     - N/A
     - No corresponding Qore module, QPP, DataProvider, JNI or Qore-language test change. Production changes add no iteration or cancellation point; bounded standalone controls do not execute inside a Qore program.

   * - 52. JAR install rules in CMakeLists.txt for all dependency JARs
     - N/A
     - No corresponding Qore module, QPP, DataProvider, JNI or Qore-language test change. Production changes add no iteration or cancellation point; bounded standalone controls do not execute inside a Qore program.

   * - 53. No workarounds: No TODOs, FIXMEs, stubs, or partially-implemented features
     - Pass
     - Root causes are fixed at the unavailable inline default argument and the missing platform guard. No runtime flags, retry, suppression or fallback changes. The unchanged exhaustive-enum diagnostic is reviewed under the existing approved policy.

   * - 54. Exception safety: C++ uses ReferenceHolder for Qore allocations, std::unique_ptr for C++ allocations, *xsink checked after every fallible operation
     - Pass
     - Operand values have automatic storage; changes add no owned allocations. Python subprocess failures terminate qualification. Both final native control runs free every allocation under Valgrind.

   * - 55. Thread safety: All mutable shared state protected by std::lock_guard<std::mutex> or documented as immutable-after-construction
     - Pass
     - No mutable production state or synchronization changes. Controls run single-threaded in separate disposable containers with read-only source overlays.

   * - 56. Type safety: Strongly-typed code<return(args)> instead of untyped code; static_cast instead of C casts; typed hashdecls for results; enums where appropriate
     - Pass
     - The explicit call uses the same int Operand constructor as the former default. Real Operand accessors verify tags before variant fields; compiler receipt validation rejects other architectures and malformed commands.

   * - 57. Performance: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply
     - Pass
     - The complete ARM-target regexp object and seven CPU-feature objects remain byte-identical after removing non-runtime metadata. No production work is added.

   * - 58. Error handling: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable
     - Pass
     - Original-header negative control fails exactly at the missing inline definition. Both generic NEON spellings reproduce the unused helper. New helper rejects malformed and foreign-architecture receipts; subprocess exit codes are enforced.

   * - 59. Documentation: Doxygen @param, @return, @throw on all public methods; @par Example with realistic business scenarios; @note for important caveats
     - Pass
     - Dependency guide and spec changelog explain both fixes, native per-build checks and host/SDK qualification limits. No public API changes.

   * - 60. QPP flags: [flags=CONSTANT] on methods that never throw; [flags=RET_VALUE_ONLY] on methods that throw but have no side effects
     - N/A
     - No corresponding Qore module, QPP, DataProvider, JNI or Qore-language test change. Production changes add no iteration or cancellation point; bounded standalone controls do not execute inside a Qore program.

   * - 61. Security: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code
     - Pass
     - Compiler commands are tokenized and passed directly without a shell. Negative tests preserve literal shell characters and reject unexpected command shapes. No credentials, user input or new production buffer accesses.

   * - 62. Correctness: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features)
     - Pass
     - 4491 actual Operand checks pass normally and under Valgrind. Seven code/data identities, 48 preprocessing identities, 223 tool tests, complete 24-patch source verification and both recipe architectures pass. Native ARM execution remains an explicit open delivery gate.
