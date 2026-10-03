Process PID-state qualification audit
=====================================

Copyright 2026 Qore Technologies, s.r.o.

Scope: module-process src/processpriv.cpp, test/process-state-fixture.c, test/process-state.qtest, test/run-process-state.py, test/README, release notes and the RPM check invocation. No new module, QPP API or DataProvider. Each of the 62 checks was reviewed. See process-state-qualification-20261003.json for raw result digests.

.. list-table:: Complete audit-changes checklist
   :header-rows: 1

   * - Check
     - Status
     - Evidence

   * - 1. Entry exists in doxygen/lang/120_modules.dox.tmpl (for modules in the Qore repo; N/A for external module repos)
     - N/A
     - Not applicable: this change introduces no module registration, DataProvider/JAR API, network operation, unbounded loop, or QPP method.

   * - 2. Entry exists in doxygen/lang/900_release_notes.dox.tmpl (for modules in the Qore repo; external modules have release notes in their .qm)
     - N/A
     - Not applicable: this change introduces no module registration, DataProvider/JAR API, network operation, unbounded loop, or QPP method.

   * - 3. qore_user_module() or qore_external_user_module() call in CMakeLists.txt
     - N/A
     - Not applicable: this change introduces no module registration, DataProvider/JAR API, network operation, unbounded loop, or QPP method.

   * - 4. Module added to QMOD list in CMakeLists.txt
     - N/A
     - Not applicable: this change introduces no module registration, DataProvider/JAR API, network operation, unbounded loop, or QPP method.

   * - 5. .qm file has @section <lowercasemodname>intro as first doc section — must be all lowercase (e.g., avrodataproviderintro, not AvroDataProviderintro)
     - N/A
     - Not applicable: this change introduces no module registration, DataProvider/JAR API, network operation, unbounded loop, or QPP method.

   * - 6. %modern in .qm file — no redundant %new-style, %require-types, %strict-args, %enable-all-warnings
     - N/A
     - Not applicable: this change introduces no module registration, DataProvider/JAR API, network operation, unbounded loop, or QPP method.

   * - 7. No parse directives (%requires, %modern, %new-style) in separated .qc files (check OUTSIDE of @code blocks only)
     - N/A
     - Not applicable: this change introduces no module registration, DataProvider/JAR API, network operation, unbounded loop, or QPP method.

   * - 8. No %include usage (deprecated for modules)
     - N/A
     - Not applicable: this change introduces no module registration, DataProvider/JAR API, network operation, unbounded loop, or QPP method.

   * - 9. Copyright 2026 on all new files
     - Pass
     - All new files and the changed C++ source carry 2026 copyright.

   * - 10. Directory layout: .qm inside qlib/<ModuleName>/ directory (not at qlib/<ModuleName>.qm for multi-file modules)
     - N/A
     - Not applicable: this change introduces no module registration, DataProvider/JAR API, network operation, unbounded loop, or QPP method.

   * - 11. No second .qm for the same module at qlib/<ModuleName>.qm
     - N/A
     - Not applicable: this change introduces no module registration, DataProvider/JAR API, network operation, unbounded loop, or QPP method.

   * - 12. ns=Qore::XX matches the QoreNamespace constructor path
     - N/A
     - Not applicable: this change introduces no module registration, DataProvider/JAR API, network operation, unbounded loop, or QPP method.

   * - 13. %modern directive present
     - Pass
     - process-state.qtest declares %modern.

   * - 14. Executable permission set (chmod +x)
     - Pass
     - Both qtest and runner have mode 0755.

   * - 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus)
     - N/A
     - Not applicable: this change introduces no module registration, DataProvider/JAR API, network operation, unbounded loop, or QPP method.

   * - 16. External module dependencies use %try-module — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard %requires
     - Pass
     - process is the binary module delivered by this repository; QUnit is the standard Qore test framework.

   * - 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks
     - Pass
     - Existing sandbox_allows_read(path) remains before fopen; permission and unavailable-proc failures remain conservative.

   * - 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks
     - N/A
     - Not applicable: this change introduces no module registration, DataProvider/JAR API, network operation, unbounded loop, or QPP method.

   * - 19. If filesystem/network ops exist, verify QoreSandboxManagerHelper usage
     - Pass
     - The existing sandbox helper is retained; no additional filesystem access is introduced.

   * - 20. No File::, Dir::, Socket::, HTTPClient:: usage without justification
     - N/A
     - Not applicable: this change introduces no module registration, DataProvider/JAR API, network operation, unbounded loop, or QPP method.

   * - 21. All for/while loops that could iterate >100 times have qore_check_cancel() checks
     - N/A
     - Not applicable: this change introduces no module registration, DataProvider/JAR API, network operation, unbounded loop, or QPP method.

   * - 22. Uses qore_check_cancel() (NOT deprecated qore_check_io_interrupt())
     - N/A
     - Not applicable: this change introduces no module registration, DataProvider/JAR API, network operation, unbounded loop, or QPP method.

   * - 23. Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations
     - N/A
     - Not applicable: this change introduces no module registration, DataProvider/JAR API, network operation, unbounded loop, or QPP method.

   * - 24. No blocking operations without cancellation support
     - N/A
     - Not applicable: this change introduces no module registration, DataProvider/JAR API, network operation, unbounded loop, or QPP method.

   * - 25. Every action has display_name, short_desc (plain text, <80 chars), desc (markdown)
     - N/A
     - Not applicable: this change introduces no module registration, DataProvider/JAR API, network operation, unbounded loop, or QPP method.

   * - 26. Every action has options populated via getActionOptionFromFields() — without this, the action shows an empty, unusable form
     - N/A
     - Not applicable: this change introduces no module registration, DataProvider/JAR API, network operation, unbounded loop, or QPP method.

   * - 27. Every action has output_type set to a typed data type constant (e.g., MyResponseDataType) — not omitted
     - N/A
     - Not applicable: this change introduces no module registration, DataProvider/JAR API, network operation, unbounded loop, or QPP method.

   * - 28. DPAT_API actions: provider has "supports_request": True and implements doRequestImpl()
     - N/A
     - Not applicable: this change introduces no module registration, DataProvider/JAR API, network operation, unbounded loop, or QPP method.

   * - 29. DPAT_FIND actions: every option exists in SearchOptions, getRecordTypeImpl() returns *hash<string, AbstractDataField>
     - N/A
     - Not applicable: this change introduces no module registration, DataProvider/JAR API, network operation, unbounded loop, or QPP method.

   * - 30. Scheme-based apps (with "scheme" in registerApp): actions use "path" and do NOT use "cls" — having both scheme and cls causes a runtime error
     - N/A
     - Not applicable: this change introduces no module registration, DataProvider/JAR API, network operation, unbounded loop, or QPP method.

   * - 31. Single-key hash slices use trailing comma: Fields{"key",} (without trailing comma, Fields{"key"} returns the value, not a hash)
     - N/A
     - Not applicable: this change introduces no module registration, DataProvider/JAR API, network operation, unbounded loop, or QPP method.

   * - 32. Typed data type classes exist for request and response types — inherit HashDataType, have const Fields hash, call addQoreFields(Fields) in constructor, export public constant at bottom (e.g., public const MyDataType = new MyDataType();)
     - N/A
     - Not applicable: this change introduces no module registration, DataProvider/JAR API, network operation, unbounded loop, or QPP method.

   * - 33. Request/input types use public Fields (enables ClassName::Fields in action registration)
     - N/A
     - Not applicable: this change introduces no module registration, DataProvider/JAR API, network operation, unbounded loop, or QPP method.

   * - 34. Response/output types use private Fields
     - N/A
     - Not applicable: this change introduces no module registration, DataProvider/JAR API, network operation, unbounded loop, or QPP method.

   * - 35. Each field in data types has display_name, type, and desc (markdown-formatted)
     - N/A
     - Not applicable: this change introduces no module registration, DataProvider/JAR API, network operation, unbounded loop, or QPP method.

   * - 36. Input fields have example_value where useful (string fields, endpoint URIs, SQL queries, etc.)
     - N/A
     - Not applicable: this change introduces no module registration, DataProvider/JAR API, network operation, unbounded loop, or QPP method.

   * - 37. Fields with finite allowed values use allowed_values with AllowedValueInfo containing both value and display_name (Title Case, human-readable) — never bare values, never described only in text
     - N/A
     - Not applicable: this change introduces no module registration, DataProvider/JAR API, network operation, unbounded loop, or QPP method.

   * - 38. Password/secret fields have "sensitive": True
     - N/A
     - Not applicable: this change introduces no module registration, DataProvider/JAR API, network operation, unbounded loop, or QPP method.

   * - 39. groups uses AppGroup enum values from qlib/DataProvider/AppGroup.qc
     - N/A
     - Not applicable: this change introduces no module registration, DataProvider/JAR API, network operation, unbounded loop, or QPP method.

   * - 40. App logo stored as separate file, loaded at module level in Priv namespace
     - N/A
     - Not applicable: this change introduces no module registration, DataProvider/JAR API, network operation, unbounded loop, or QPP method.

   * - 41. App desc uses markdown: bullet list of capabilities, links to project website, business-language explanation of value
     - N/A
     - Not applicable: this change introduces no module registration, DataProvider/JAR API, network operation, unbounded loop, or QPP method.

   * - 42. display_name is user-friendly ("Apache Avro" not "avro")
     - N/A
     - Not applicable: this change introduces no module registration, DataProvider/JAR API, network operation, unbounded loop, or QPP method.

   * - 43. short_desc is plain text, under 80 chars, single sentence — no markdown
     - N/A
     - Not applicable: this change introduces no module registration, DataProvider/JAR API, network operation, unbounded loop, or QPP method.

   * - 44. desc uses markdown: backticks for code/field refs ( field_name ,  True ,  pdf ), \n\n for paragraphs, -  bullet lists for enumerations, bold for caveats
     - N/A
     - Not applicable: this change introduces no module registration, DataProvider/JAR API, network operation, unbounded loop, or QPP method.

   * - 45. Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use"
     - N/A
     - Not applicable: this change introduces no module registration, DataProvider/JAR API, network operation, unbounded loop, or QPP method.

   * - 46. No bare True/False/NOTHING — must be backtick-wrapped in desc
     - N/A
     - Not applicable: this change introduces no module registration, DataProvider/JAR API, network operation, unbounded loop, or QPP method.

   * - 47. No bare field/option names in prose — must use backticks
     - N/A
     - Not applicable: this change introduces no module registration, DataProvider/JAR API, network operation, unbounded loop, or QPP method.

   * - 48. Long descriptions (>500 chars) use bold section headers and bullet lists
     - N/A
     - Not applicable: this change introduces no module registration, DataProvider/JAR API, network operation, unbounded loop, or QPP method.

   * - 49. Factory registration in Qore repo: every factory name registered in qlib/DataProvider/DataProvider.qc → FactoryMap (without this, module loads but doesn't appear in Qorus apps)
     - N/A
     - Not applicable: this change introduces no module registration, DataProvider/JAR API, network operation, unbounded loop, or QPP method.

   * - 50. getRecordTypeImpl() signature: must be private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options) — NOT returning *AbstractDataProviderType
     - N/A
     - Not applicable: this change introduces no module registration, DataProvider/JAR API, network operation, unbounded loop, or QPP method.

   * - 51. Dependency JARs committed (for JNI modules): JAR files in qlib/*/jar/ may be gitignored — use git add -f to ensure they're tracked, otherwise CI compilation fails
     - N/A
     - Not applicable: this change introduces no module registration, DataProvider/JAR API, network operation, unbounded loop, or QPP method.

   * - 52. JAR install rules in CMakeLists.txt for all dependency JARs
     - N/A
     - Not applicable: this change introduces no module registration, DataProvider/JAR API, network operation, unbounded loop, or QPP method.

   * - 53. No workarounds: No TODOs, FIXMEs, stubs, or partially-implemented features
     - Pass
     - Direct fix for the observed PID lifetime race. The exact external close_range diagnostic is approved and recorded, without suppression.

   * - 54. Exception safety: C++ uses ReferenceHolder for Qore allocations, std::unique_ptr for C++ allocations, *xsink checked after every fallible operation
     - Pass
     - Every opened FILE is closed once before return; no throwing C++ operation occurs between fopen and fclose. Test runner uses TemporaryDirectory and checked subprocesses.

   * - 55. Thread safety: All mutable shared state protected by std::lock_guard<std::mutex> or documented as immutable-after-construction
     - Pass
     - Production uses stack state and existing sandbox checks. Interposer disappearance state is thread-local; each scenario runs in a separate process.

   * - 56. Type safety: Strongly-typed code<return(args)> instead of untyped code; static_cast instead of C casts; typed hashdecls for results; enums where appropriate
     - Pass
     - PID and syscall return values retain their native types; Qore expectations use typed bool and string values.

   * - 57. Performance: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply
     - Pass
     - Bounded 511-byte stat read; one additional PID probe only on disappearance errors.

   * - 58. Error handling: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable
     - Pass
     - ENOENT/ESRCH revalidate the PID; EACCES, missing proc mount, malformed/truncated/empty records and live states stay conservative. Invalid PIDs are tested.

   * - 59. Documentation: Doxygen @param, @return, @throw on all public methods; @par Example with realistic business scenarios; @note for important caveats
     - Pass
     - Release notes and test README explain behavior and native/Valgrind commands. No new public API.

   * - 60. QPP flags: [flags=CONSTANT] on methods that never throw; [flags=RET_VALUE_ONLY] on methods that throw but have no side effects
     - N/A
     - Not applicable: this change introduces no module registration, DataProvider/JAR API, network operation, unbounded loop, or QPP method.

   * - 61. Security: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code
     - Pass
     - Read length and terminator remain bounded; no user-controlled format strings. Interposer only matches the test process stat path and signal-zero lookup.

   * - 62. Correctness: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features)
     - Pass
     - Original baseline fails the deterministic disappearance control; 13 cases/39 assertions and full 57 cases/429 assertions pass. All 13 new Valgrind cases are clean; three affected existing cases have no memory errors/losses, with the approved fork-child descriptor diagnostic.
