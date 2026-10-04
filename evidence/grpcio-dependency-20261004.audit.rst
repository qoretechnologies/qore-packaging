Leap gRPC dependency review (2026-10-04)
========================================

Copyright 2026 Qore Technologies, s.r.o.

Scope: python-grpcio.spec and its pinned recipe sources, source registry entry, OBS package metadata, README/dependency documentation and the three approval/evidence updates. All 62 skill checks are evaluated below. Validation: results/grpcio-final-source-review-20261004.json and the candidate14b/native qualification records. Native OBS/ARM and repository publication are subsequent gates. The final dependency/OBS tool checks pass 25 tests without warnings (results/grpcio-final-dependency-tests-20261004.log and results/grpcio-final-obs-tests-20261004.log). Authored source whitespace is clean; verbatim patch context/mail trailers and upstream license bytes are preserved.

.. list-table:: Complete audit-changes checklist
   :header-rows: 1

   * - Check
     - Status
     - Evidence

   * - 1. Entry exists in doxygen/lang/120_modules.dox.tmpl (for modules in the Qore repo; N/A for external module repos)
     - N/A
     - No Qore module, QPP class, DataProvider, JNI JAR or qtest changes. External Python gRPC internals and standalone native controls do not use Qore sandbox/cancellation APIs; existing Qore boundaries are unchanged.

   * - 2. Entry exists in doxygen/lang/900_release_notes.dox.tmpl (for modules in the Qore repo; external modules have release notes in their .qm)
     - N/A
     - No Qore module, QPP class, DataProvider, JNI JAR or qtest changes. External Python gRPC internals and standalone native controls do not use Qore sandbox/cancellation APIs; existing Qore boundaries are unchanged.

   * - 3. qore_user_module() or qore_external_user_module() call in CMakeLists.txt
     - N/A
     - No Qore module, QPP class, DataProvider, JNI JAR or qtest changes. External Python gRPC internals and standalone native controls do not use Qore sandbox/cancellation APIs; existing Qore boundaries are unchanged.

   * - 4. Module added to QMOD list in CMakeLists.txt
     - N/A
     - No Qore module, QPP class, DataProvider, JNI JAR or qtest changes. External Python gRPC internals and standalone native controls do not use Qore sandbox/cancellation APIs; existing Qore boundaries are unchanged.

   * - 5. .qm file has @section <lowercasemodname>intro as first doc section — must be all lowercase (e.g., avrodataproviderintro, not AvroDataProviderintro)
     - N/A
     - No Qore module, QPP class, DataProvider, JNI JAR or qtest changes. External Python gRPC internals and standalone native controls do not use Qore sandbox/cancellation APIs; existing Qore boundaries are unchanged.

   * - 6. %modern in .qm file — no redundant %new-style, %require-types, %strict-args, %enable-all-warnings
     - N/A
     - No Qore module, QPP class, DataProvider, JNI JAR or qtest changes. External Python gRPC internals and standalone native controls do not use Qore sandbox/cancellation APIs; existing Qore boundaries are unchanged.

   * - 7. No parse directives (%requires, %modern, %new-style) in separated .qc files (check OUTSIDE of @code blocks only)
     - N/A
     - No Qore module, QPP class, DataProvider, JNI JAR or qtest changes. External Python gRPC internals and standalone native controls do not use Qore sandbox/cancellation APIs; existing Qore boundaries are unchanged.

   * - 8. No %include usage (deprecated for modules)
     - N/A
     - No Qore module, QPP class, DataProvider, JNI JAR or qtest changes. External Python gRPC internals and standalone native controls do not use Qore sandbox/cancellation APIs; existing Qore boundaries are unchanged.

   * - 9. Copyright 2026 on all new files
     - Pass
     - 2026 headers on Qore-authored recipes, controls, patches, documentation and metadata; verbatim upstream notices retain their original copyright attribution.

   * - 10. Directory layout: .qm inside qlib/<ModuleName>/ directory (not at qlib/<ModuleName>.qm for multi-file modules)
     - N/A
     - No Qore module, QPP class, DataProvider, JNI JAR or qtest changes. External Python gRPC internals and standalone native controls do not use Qore sandbox/cancellation APIs; existing Qore boundaries are unchanged.

   * - 11. No second .qm for the same module at qlib/<ModuleName>.qm
     - N/A
     - No Qore module, QPP class, DataProvider, JNI JAR or qtest changes. External Python gRPC internals and standalone native controls do not use Qore sandbox/cancellation APIs; existing Qore boundaries are unchanged.

   * - 12. ns=Qore::XX matches the QoreNamespace constructor path
     - N/A
     - No Qore module, QPP class, DataProvider, JNI JAR or qtest changes. External Python gRPC internals and standalone native controls do not use Qore sandbox/cancellation APIs; existing Qore boundaries are unchanged.

   * - 13. %modern directive present
     - N/A
     - No Qore module, QPP class, DataProvider, JNI JAR or qtest changes. External Python gRPC internals and standalone native controls do not use Qore sandbox/cancellation APIs; existing Qore boundaries are unchanged.

   * - 14. Executable permission set (chmod +x)
     - N/A
     - No Qore module, QPP class, DataProvider, JNI JAR or qtest changes. External Python gRPC internals and standalone native controls do not use Qore sandbox/cancellation APIs; existing Qore boundaries are unchanged.

   * - 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus)
     - N/A
     - No Qore module, QPP class, DataProvider, JNI JAR or qtest changes. External Python gRPC internals and standalone native controls do not use Qore sandbox/cancellation APIs; existing Qore boundaries are unchanged.

   * - 16. External module dependencies use %try-module — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard %requires
     - N/A
     - No Qore module, QPP class, DataProvider, JNI JAR or qtest changes. External Python gRPC internals and standalone native controls do not use Qore sandbox/cancellation APIs; existing Qore boundaries are unchanged.

   * - 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks
     - N/A
     - No Qore module, QPP class, DataProvider, JNI JAR or qtest changes. External Python gRPC internals and standalone native controls do not use Qore sandbox/cancellation APIs; existing Qore boundaries are unchanged.

   * - 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks
     - N/A
     - No Qore module, QPP class, DataProvider, JNI JAR or qtest changes. External Python gRPC internals and standalone native controls do not use Qore sandbox/cancellation APIs; existing Qore boundaries are unchanged.

   * - 19. If filesystem/network ops exist, verify QoreSandboxManagerHelper usage
     - N/A
     - No Qore module, QPP class, DataProvider, JNI JAR or qtest changes. External Python gRPC internals and standalone native controls do not use Qore sandbox/cancellation APIs; existing Qore boundaries are unchanged.

   * - 20. No File::, Dir::, Socket::, HTTPClient:: usage without justification
     - N/A
     - No Qore module, QPP class, DataProvider, JNI JAR or qtest changes. External Python gRPC internals and standalone native controls do not use Qore sandbox/cancellation APIs; existing Qore boundaries are unchanged.

   * - 21. All for/while loops that could iterate >100 times have qore_check_cancel() checks
     - N/A
     - No Qore module, QPP class, DataProvider, JNI JAR or qtest changes. External Python gRPC internals and standalone native controls do not use Qore sandbox/cancellation APIs; existing Qore boundaries are unchanged.

   * - 22. Uses qore_check_cancel() (NOT deprecated qore_check_io_interrupt())
     - N/A
     - No Qore module, QPP class, DataProvider, JNI JAR or qtest changes. External Python gRPC internals and standalone native controls do not use Qore sandbox/cancellation APIs; existing Qore boundaries are unchanged.

   * - 23. Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations
     - N/A
     - No Qore module, QPP class, DataProvider, JNI JAR or qtest changes. External Python gRPC internals and standalone native controls do not use Qore sandbox/cancellation APIs; existing Qore boundaries are unchanged.

   * - 24. No blocking operations without cancellation support
     - N/A
     - No Qore module, QPP class, DataProvider, JNI JAR or qtest changes. External Python gRPC internals and standalone native controls do not use Qore sandbox/cancellation APIs; existing Qore boundaries are unchanged.

   * - 25. Every action has display_name, short_desc (plain text, <80 chars), desc (markdown)
     - N/A
     - No Qore module, QPP class, DataProvider, JNI JAR or qtest changes. External Python gRPC internals and standalone native controls do not use Qore sandbox/cancellation APIs; existing Qore boundaries are unchanged.

   * - 26. Every action has options populated via getActionOptionFromFields() — without this, the action shows an empty, unusable form
     - N/A
     - No Qore module, QPP class, DataProvider, JNI JAR or qtest changes. External Python gRPC internals and standalone native controls do not use Qore sandbox/cancellation APIs; existing Qore boundaries are unchanged.

   * - 27. Every action has output_type set to a typed data type constant (e.g., MyResponseDataType) — not omitted
     - N/A
     - No Qore module, QPP class, DataProvider, JNI JAR or qtest changes. External Python gRPC internals and standalone native controls do not use Qore sandbox/cancellation APIs; existing Qore boundaries are unchanged.

   * - 28. DPAT_API actions: provider has "supports_request": True and implements doRequestImpl()
     - N/A
     - No Qore module, QPP class, DataProvider, JNI JAR or qtest changes. External Python gRPC internals and standalone native controls do not use Qore sandbox/cancellation APIs; existing Qore boundaries are unchanged.

   * - 29. DPAT_FIND actions: every option exists in SearchOptions, getRecordTypeImpl() returns *hash<string, AbstractDataField>
     - N/A
     - No Qore module, QPP class, DataProvider, JNI JAR or qtest changes. External Python gRPC internals and standalone native controls do not use Qore sandbox/cancellation APIs; existing Qore boundaries are unchanged.

   * - 30. Scheme-based apps (with "scheme" in registerApp): actions use "path" and do NOT use "cls" — having both scheme and cls causes a runtime error
     - N/A
     - No Qore module, QPP class, DataProvider, JNI JAR or qtest changes. External Python gRPC internals and standalone native controls do not use Qore sandbox/cancellation APIs; existing Qore boundaries are unchanged.

   * - 31. Single-key hash slices use trailing comma: Fields{"key",} (without trailing comma, Fields{"key"} returns the value, not a hash)
     - N/A
     - No Qore module, QPP class, DataProvider, JNI JAR or qtest changes. External Python gRPC internals and standalone native controls do not use Qore sandbox/cancellation APIs; existing Qore boundaries are unchanged.

   * - 32. Typed data type classes exist for request and response types — inherit HashDataType, have const Fields hash, call addQoreFields(Fields) in constructor, export public constant at bottom (e.g., public const MyDataType = new MyDataType();)
     - N/A
     - No Qore module, QPP class, DataProvider, JNI JAR or qtest changes. External Python gRPC internals and standalone native controls do not use Qore sandbox/cancellation APIs; existing Qore boundaries are unchanged.

   * - 33. Request/input types use public Fields (enables ClassName::Fields in action registration)
     - N/A
     - No Qore module, QPP class, DataProvider, JNI JAR or qtest changes. External Python gRPC internals and standalone native controls do not use Qore sandbox/cancellation APIs; existing Qore boundaries are unchanged.

   * - 34. Response/output types use private Fields
     - N/A
     - No Qore module, QPP class, DataProvider, JNI JAR or qtest changes. External Python gRPC internals and standalone native controls do not use Qore sandbox/cancellation APIs; existing Qore boundaries are unchanged.

   * - 35. Each field in data types has display_name, type, and desc (markdown-formatted)
     - N/A
     - No Qore module, QPP class, DataProvider, JNI JAR or qtest changes. External Python gRPC internals and standalone native controls do not use Qore sandbox/cancellation APIs; existing Qore boundaries are unchanged.

   * - 36. Input fields have example_value where useful (string fields, endpoint URIs, SQL queries, etc.)
     - N/A
     - No Qore module, QPP class, DataProvider, JNI JAR or qtest changes. External Python gRPC internals and standalone native controls do not use Qore sandbox/cancellation APIs; existing Qore boundaries are unchanged.

   * - 37. Fields with finite allowed values use allowed_values with AllowedValueInfo containing both value and display_name (Title Case, human-readable) — never bare values, never described only in text
     - N/A
     - No Qore module, QPP class, DataProvider, JNI JAR or qtest changes. External Python gRPC internals and standalone native controls do not use Qore sandbox/cancellation APIs; existing Qore boundaries are unchanged.

   * - 38. Password/secret fields have "sensitive": True
     - N/A
     - No Qore module, QPP class, DataProvider, JNI JAR or qtest changes. External Python gRPC internals and standalone native controls do not use Qore sandbox/cancellation APIs; existing Qore boundaries are unchanged.

   * - 39. groups uses AppGroup enum values from qlib/DataProvider/AppGroup.qc
     - N/A
     - No Qore module, QPP class, DataProvider, JNI JAR or qtest changes. External Python gRPC internals and standalone native controls do not use Qore sandbox/cancellation APIs; existing Qore boundaries are unchanged.

   * - 40. App logo stored as separate file, loaded at module level in Priv namespace
     - N/A
     - No Qore module, QPP class, DataProvider, JNI JAR or qtest changes. External Python gRPC internals and standalone native controls do not use Qore sandbox/cancellation APIs; existing Qore boundaries are unchanged.

   * - 41. App desc uses markdown: bullet list of capabilities, links to project website, business-language explanation of value
     - N/A
     - No Qore module, QPP class, DataProvider, JNI JAR or qtest changes. External Python gRPC internals and standalone native controls do not use Qore sandbox/cancellation APIs; existing Qore boundaries are unchanged.

   * - 42. display_name is user-friendly ("Apache Avro" not "avro")
     - N/A
     - No Qore module, QPP class, DataProvider, JNI JAR or qtest changes. External Python gRPC internals and standalone native controls do not use Qore sandbox/cancellation APIs; existing Qore boundaries are unchanged.

   * - 43. short_desc is plain text, under 80 chars, single sentence — no markdown
     - N/A
     - No Qore module, QPP class, DataProvider, JNI JAR or qtest changes. External Python gRPC internals and standalone native controls do not use Qore sandbox/cancellation APIs; existing Qore boundaries are unchanged.

   * - 44. desc uses markdown: backticks for code/field refs ( field_name ,  True ,  pdf ), \n\n for paragraphs, -  bullet lists for enumerations, bold for caveats
     - N/A
     - No Qore module, QPP class, DataProvider, JNI JAR or qtest changes. External Python gRPC internals and standalone native controls do not use Qore sandbox/cancellation APIs; existing Qore boundaries are unchanged.

   * - 45. Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use"
     - N/A
     - No Qore module, QPP class, DataProvider, JNI JAR or qtest changes. External Python gRPC internals and standalone native controls do not use Qore sandbox/cancellation APIs; existing Qore boundaries are unchanged.

   * - 46. No bare True/False/NOTHING — must be backtick-wrapped in desc
     - N/A
     - No Qore module, QPP class, DataProvider, JNI JAR or qtest changes. External Python gRPC internals and standalone native controls do not use Qore sandbox/cancellation APIs; existing Qore boundaries are unchanged.

   * - 47. No bare field/option names in prose — must use backticks
     - N/A
     - No Qore module, QPP class, DataProvider, JNI JAR or qtest changes. External Python gRPC internals and standalone native controls do not use Qore sandbox/cancellation APIs; existing Qore boundaries are unchanged.

   * - 48. Long descriptions (>500 chars) use bold section headers and bullet lists
     - N/A
     - No Qore module, QPP class, DataProvider, JNI JAR or qtest changes. External Python gRPC internals and standalone native controls do not use Qore sandbox/cancellation APIs; existing Qore boundaries are unchanged.

   * - 49. Factory registration in Qore repo: every factory name registered in qlib/DataProvider/DataProvider.qc → FactoryMap (without this, module loads but doesn't appear in Qorus apps)
     - N/A
     - No Qore module, QPP class, DataProvider, JNI JAR or qtest changes. External Python gRPC internals and standalone native controls do not use Qore sandbox/cancellation APIs; existing Qore boundaries are unchanged.

   * - 50. getRecordTypeImpl() signature: must be private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options) — NOT returning *AbstractDataProviderType
     - N/A
     - No Qore module, QPP class, DataProvider, JNI JAR or qtest changes. External Python gRPC internals and standalone native controls do not use Qore sandbox/cancellation APIs; existing Qore boundaries are unchanged.

   * - 51. Dependency JARs committed (for JNI modules): JAR files in qlib/*/jar/ may be gitignored — use git add -f to ensure they're tracked, otherwise CI compilation fails
     - N/A
     - No Qore module, QPP class, DataProvider, JNI JAR or qtest changes. External Python gRPC internals and standalone native controls do not use Qore sandbox/cancellation APIs; existing Qore boundaries are unchanged.

   * - 52. JAR install rules in CMakeLists.txt for all dependency JARs
     - N/A
     - No Qore module, QPP class, DataProvider, JNI JAR or qtest changes. External Python gRPC internals and standalone native controls do not use Qore sandbox/cancellation APIs; existing Qore boundaries are unchanged.

   * - 53. No workarounds: No TODOs, FIXMEs, stubs, or partially-implemented features
     - Pass
     - Runtime defects have root-cause fixes and negative/lifecycle tests. Upstream compiler/API/manifest and bounded allocation diagnostics are explicitly accepted in linked evidence. No new suppression or stub. NATS approval update is documentation only.

   * - 54. Exception safety: C++ uses ReferenceHolder for Qore allocations, std::unique_ptr for C++ allocations, *xsink checked after every fallible operation
     - Pass
     - Native batch ownership follows Core completion; rejection/cancellation and conversion exceptions release buffers in finally blocks. Channel arguments validate before acquiring C resources. Server, TLS, queue and poll failure cleanup tested; native Valgrind results exclude additional gRPC losses.

   * - 55. Thread safety: All mutable shared state protected by std::lock_guard<std::mutex> or documented as immutable-after-construction
     - Pass
     - Core completion owns async buffers until callback; event queue retains its mutex and bound-loop dispatch. Injection counters use C atomics. Fork and concurrent async controls pass. Standalone native controls are single-threaded where globals are mutable.

   * - 56. Type safety: Strongly-typed code<return(args)> instead of untyped code; static_cast instead of C casts; typed hashdecls for results; enums where appropriate
     - Pass
     - Address class uses value initialization; Huffman masks are uint64_t; worker pointers initialize to nullptr. New C++ controls use static_cast/reinterpret_cast and typed containers; the C injector uses C casts as required by C.

   * - 57. Performance: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply
     - Pass
     - No new quadratic production loops. Callback cleanup traverses only the bounded batch; upstream shutdown fix yields through the existing work signal and backoff. Dead priority lookup removed.

   * - 58. Error handling: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable
     - Pass
     - Tests cover empty/invalid arguments, empty TLS credentials, rejected batches, cancellation, EINTR, EBADF, EAGAIN, zero-byte notification, failed allocation initialization and successful reuse. Wakeup fallback dispatches through existing event loops.

   * - 59. Documentation: Doxygen @param, @return, @throw on all public methods; @par Example with realistic business scenarios; @note for important caveats
     - Pass
     - dependencies/grpcio.rst explains package purpose, source preparation, installation examples, fixes, test scope and accepted diagnostics; recipe changelog documents behavior. No new Qore public API.

   * - 60. QPP flags: [flags=CONSTANT] on methods that never throw; [flags=RET_VALUE_ONLY] on methods that throw but have no side effects
     - N/A
     - No Qore module, QPP class, DataProvider, JNI JAR or qtest changes. External Python gRPC internals and standalone native controls do not use Qore sandbox/cancellation APIs; existing Qore boundaries are unchanged.

   * - 61. Security: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code
     - Pass
     - Pinned archives and five notices verified; 29 source inputs match candidate14b. No credentials added. Tests bind loopback and inject only into isolated processes. RPM uses system TLS/DNS/RE2/zlib; both embedded and shared gRPC import orders pass.

   * - 62. Correctness: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features)
     - Pass
     - 13 packaging tests, 101 upstream passes plus one skip, native codec/address controls, 300 fault-injected RPCs and 200 poll initializations pass. Installed Qore runtime/SDK each pass 13 suites/1768 assertions. Exact native extension matches Valgrind-qualified candidate13. Source/manifest/license and stale-binary negative checks pass.
