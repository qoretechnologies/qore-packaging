Encoded hash lookup and exception output audit
==============================================

Copyright 2026 Qore Technologies, s.r.o.

Scope: lib/QoreHashNode.cpp, include/qore/QoreHashNode.h, CMakeLists.txt, release notes and the hash lookup native regression. All 62 audit-changes entries were reviewed; 19 Pass, 43 N/A, 0 code-review failures. Configuration diagnostic approval remains pending as recorded below.

Qualification on 2026-10-08
---------------------------

Debug and Release builds use /usr, matching the installed Qore prefix. Each
passes 348 native checks, normally and under Valgrind, and 15 Qore cases with
302 assertions across hash-lookup-native, hash and hashdecl. Valgrind reports
zero errors and zero definite, indirect or possible lost allocations; no
suppression is used. Each native failure group rejects the original library.
The account example extracted from the header compiles with -Wall -Werror
and prints the expected balance in both modes. All seven qualified source
files are bound by SHA-256 in the packaging evidence.

The initial build command loaded the old generated Makefile before CMake
regenerated its target graph, so the new target was unknown to that process.
The corrected driver explicitly configured before building. It changed no
source, flags or assertions. The full successful qualification supersedes
that initial harness attempt.

The only Valgrind warning is the exact previously approved GCC thread-local
wrapper DW_AT_abstract_origin diagnostic, already recorded in
qore-packaging/evidence/core-close-rpm-qualification-20261002.json.
Functional tests and native compilation emit no diagnostics.

Two bundled ngtcp2 configuration warnings concern the unavailable alternative
quictls/LibreSSL backends. The required ossl library builds and is linked into
libqore in both modes. An independent three-backend CMake control validates
selection and the exact warnings. Acceptance is pending in
qore-packaging/evidence/ngtcp2-backend-diagnostics-20261008.json; no commit is
qualified until that scope is approved or the configure issue is fixed.
RPMs require system ngtcp2 and do not use this bundled dependency path.

Raw results: qore-packaging/results/core-hash-lookup-final-20261008,
core-hash-lookup-original-20261008 and core-hash-docs-20261008. The initial
harness failure is retained in core-hash-lookup-20261008. Full updated RPM
builds and installed-package qualification remain separate gates.

.. list-table:: Complete audit-changes checklist
   :header-rows: 1

   * - Check
     - Status
     - Evidence

   * - 1. Entry exists in doxygen/lang/120_modules.dox.tmpl (for modules in the Qore repo; N/A for external module repos)
     - N/A
     - No corresponding new module, QPP, DataProvider, JNI, sandbox helper or cancellation-point change in this bounded lookup scope.

   * - 2. Entry exists in doxygen/lang/900_release_notes.dox.tmpl (for modules in the Qore repo; external modules have release notes in their .qm)
     - N/A
     - No corresponding new module, QPP, DataProvider, JNI, sandbox helper or cancellation-point change in this bounded lookup scope.

   * - 3. qore_user_module() or qore_external_user_module() call in CMakeLists.txt
     - N/A
     - No corresponding new module, QPP, DataProvider, JNI, sandbox helper or cancellation-point change in this bounded lookup scope.

   * - 4. Module added to QMOD list in CMakeLists.txt
     - N/A
     - No corresponding new module, QPP, DataProvider, JNI, sandbox helper or cancellation-point change in this bounded lookup scope.

   * - 5. .qm file has @section <lowercasemodname>intro as first doc section — must be all lowercase (e.g., avrodataproviderintro, not AvroDataProviderintro)
     - N/A
     - No corresponding new module, QPP, DataProvider, JNI, sandbox helper or cancellation-point change in this bounded lookup scope.

   * - 6. %modern in .qm file — no redundant %new-style, %require-types, %strict-args, %enable-all-warnings
     - N/A
     - No corresponding new module, QPP, DataProvider, JNI, sandbox helper or cancellation-point change in this bounded lookup scope.

   * - 7. No parse directives (%requires, %modern, %new-style) in separated .qc files (check OUTSIDE of @code blocks only)
     - N/A
     - No corresponding new module, QPP, DataProvider, JNI, sandbox helper or cancellation-point change in this bounded lookup scope.

   * - 8. No %include usage (deprecated for modules)
     - N/A
     - No corresponding new module, QPP, DataProvider, JNI, sandbox helper or cancellation-point change in this bounded lookup scope.

   * - 9. Copyright 2026 on all new files
     - Pass
     - The new native test, Qore wrapper, test guide and audit carry Copyright 2026.

   * - 10. Directory layout: .qm inside qlib/<ModuleName>/ directory (not at qlib/<ModuleName>.qm for multi-file modules)
     - N/A
     - No corresponding new module, QPP, DataProvider, JNI, sandbox helper or cancellation-point change in this bounded lookup scope.

   * - 11. No second .qm for the same module at qlib/<ModuleName>.qm
     - N/A
     - No corresponding new module, QPP, DataProvider, JNI, sandbox helper or cancellation-point change in this bounded lookup scope.

   * - 12. ns=Qore::XX matches the QoreNamespace constructor path
     - N/A
     - No corresponding new module, QPP, DataProvider, JNI, sandbox helper or cancellation-point change in this bounded lookup scope.

   * - 13. %modern directive present
     - Pass
     - hash-lookup-native.qtest uses %modern.

   * - 14. Executable permission set (chmod +x)
     - Pass
     - The Qore wrapper is executable (0755).

   * - 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus)
     - Pass
     - The local qlib path is prepended before the relative ../../../../qlib/QUnit.qm requirement.

   * - 16. External module dependencies use %try-module — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard %requires
     - Pass
     - QUnit is delivered by Qore and uses a hard relative requirement; no external module is added.

   * - 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks
     - Pass
     - Production lookup changes have no filesystem operations; the native fixture only writes its test result.

   * - 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks
     - Pass
     - No networking is introduced.

   * - 19. If filesystem/network ops exist, verify QoreSandboxManagerHelper usage
     - N/A
     - No corresponding new module, QPP, DataProvider, JNI, sandbox helper or cancellation-point change in this bounded lookup scope.

   * - 20. No File::, Dir::, Socket::, HTTPClient:: usage without justification
     - Pass
     - The test wrapper checks for and executes its local native fixture using existing runtime APIs; no production I/O is added.

   * - 21. All for/while loops that could iterate >100 times have qore_check_cancel() checks
     - Pass
     - Production changes add no loops; native fixture loops are fixed at at most four iterations per level and are outside interpreter execution.

   * - 22. Uses qore_check_cancel() (NOT deprecated qore_check_io_interrupt())
     - N/A
     - No corresponding new module, QPP, DataProvider, JNI, sandbox helper or cancellation-point change in this bounded lookup scope.

   * - 23. Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations
     - N/A
     - No corresponding new module, QPP, DataProvider, JNI, sandbox helper or cancellation-point change in this bounded lookup scope.

   * - 24. No blocking operations without cancellation support
     - Pass
     - No blocking operation is added to the runtime. The wrapper waits for its finite native child through the existing process API.

   * - 25. Every action has display_name, short_desc (plain text, <80 chars), desc (markdown)
     - N/A
     - No corresponding new module, QPP, DataProvider, JNI, sandbox helper or cancellation-point change in this bounded lookup scope.

   * - 26. Every action has options populated via getActionOptionFromFields() — without this, the action shows an empty, unusable form
     - N/A
     - No corresponding new module, QPP, DataProvider, JNI, sandbox helper or cancellation-point change in this bounded lookup scope.

   * - 27. Every action has output_type set to a typed data type constant (e.g., MyResponseDataType) — not omitted
     - N/A
     - No corresponding new module, QPP, DataProvider, JNI, sandbox helper or cancellation-point change in this bounded lookup scope.

   * - 28. DPAT_API actions: provider has "supports_request": True and implements doRequestImpl()
     - N/A
     - No corresponding new module, QPP, DataProvider, JNI, sandbox helper or cancellation-point change in this bounded lookup scope.

   * - 29. DPAT_FIND actions: every option exists in SearchOptions, getRecordTypeImpl() returns *hash<string, AbstractDataField>
     - N/A
     - No corresponding new module, QPP, DataProvider, JNI, sandbox helper or cancellation-point change in this bounded lookup scope.

   * - 30. Scheme-based apps (with "scheme" in registerApp): actions use "path" and do NOT use "cls" — having both scheme and cls causes a runtime error
     - N/A
     - No corresponding new module, QPP, DataProvider, JNI, sandbox helper or cancellation-point change in this bounded lookup scope.

   * - 31. Single-key hash slices use trailing comma: Fields{"key",} (without trailing comma, Fields{"key"} returns the value, not a hash)
     - N/A
     - No corresponding new module, QPP, DataProvider, JNI, sandbox helper or cancellation-point change in this bounded lookup scope.

   * - 32. Typed data type classes exist for request and response types — inherit HashDataType, have const Fields hash, call addQoreFields(Fields) in constructor, export public constant at bottom (e.g., public const MyDataType = new MyDataType();)
     - N/A
     - No corresponding new module, QPP, DataProvider, JNI, sandbox helper or cancellation-point change in this bounded lookup scope.

   * - 33. Request/input types use public Fields (enables ClassName::Fields in action registration)
     - N/A
     - No corresponding new module, QPP, DataProvider, JNI, sandbox helper or cancellation-point change in this bounded lookup scope.

   * - 34. Response/output types use private Fields
     - N/A
     - No corresponding new module, QPP, DataProvider, JNI, sandbox helper or cancellation-point change in this bounded lookup scope.

   * - 35. Each field in data types has display_name, type, and desc (markdown-formatted)
     - N/A
     - No corresponding new module, QPP, DataProvider, JNI, sandbox helper or cancellation-point change in this bounded lookup scope.

   * - 36. Input fields have example_value where useful (string fields, endpoint URIs, SQL queries, etc.)
     - N/A
     - No corresponding new module, QPP, DataProvider, JNI, sandbox helper or cancellation-point change in this bounded lookup scope.

   * - 37. Fields with finite allowed values use allowed_values with AllowedValueInfo containing both value and display_name (Title Case, human-readable) — never bare values, never described only in text
     - N/A
     - No corresponding new module, QPP, DataProvider, JNI, sandbox helper or cancellation-point change in this bounded lookup scope.

   * - 38. Password/secret fields have "sensitive": True
     - N/A
     - No corresponding new module, QPP, DataProvider, JNI, sandbox helper or cancellation-point change in this bounded lookup scope.

   * - 39. groups uses AppGroup enum values from qlib/DataProvider/AppGroup.qc
     - N/A
     - No corresponding new module, QPP, DataProvider, JNI, sandbox helper or cancellation-point change in this bounded lookup scope.

   * - 40. App logo stored as separate file, loaded at module level in Priv namespace
     - N/A
     - No corresponding new module, QPP, DataProvider, JNI, sandbox helper or cancellation-point change in this bounded lookup scope.

   * - 41. App desc uses markdown: bullet list of capabilities, links to project website, business-language explanation of value
     - N/A
     - No corresponding new module, QPP, DataProvider, JNI, sandbox helper or cancellation-point change in this bounded lookup scope.

   * - 42. display_name is user-friendly ("Apache Avro" not "avro")
     - N/A
     - No corresponding new module, QPP, DataProvider, JNI, sandbox helper or cancellation-point change in this bounded lookup scope.

   * - 43. short_desc is plain text, under 80 chars, single sentence — no markdown
     - N/A
     - No corresponding new module, QPP, DataProvider, JNI, sandbox helper or cancellation-point change in this bounded lookup scope.

   * - 44. desc uses markdown: backticks for code/field refs ( field_name ,  True ,  pdf ), \n\n for paragraphs, -  bullet lists for enumerations, bold for caveats
     - N/A
     - No corresponding new module, QPP, DataProvider, JNI, sandbox helper or cancellation-point change in this bounded lookup scope.

   * - 45. Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use"
     - N/A
     - No corresponding new module, QPP, DataProvider, JNI, sandbox helper or cancellation-point change in this bounded lookup scope.

   * - 46. No bare True/False/NOTHING — must be backtick-wrapped in desc
     - N/A
     - No corresponding new module, QPP, DataProvider, JNI, sandbox helper or cancellation-point change in this bounded lookup scope.

   * - 47. No bare field/option names in prose — must use backticks
     - N/A
     - No corresponding new module, QPP, DataProvider, JNI, sandbox helper or cancellation-point change in this bounded lookup scope.

   * - 48. Long descriptions (>500 chars) use bold section headers and bullet lists
     - N/A
     - No corresponding new module, QPP, DataProvider, JNI, sandbox helper or cancellation-point change in this bounded lookup scope.

   * - 49. Factory registration in Qore repo: every factory name registered in qlib/DataProvider/DataProvider.qc → FactoryMap (without this, module loads but doesn't appear in Qorus apps)
     - N/A
     - No corresponding new module, QPP, DataProvider, JNI, sandbox helper or cancellation-point change in this bounded lookup scope.

   * - 50. getRecordTypeImpl() signature: must be private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options) — NOT returning *AbstractDataProviderType
     - N/A
     - No corresponding new module, QPP, DataProvider, JNI, sandbox helper or cancellation-point change in this bounded lookup scope.

   * - 51. Dependency JARs committed (for JNI modules): JAR files in qlib/*/jar/ may be gitignored — use git add -f to ensure they're tracked, otherwise CI compilation fails
     - N/A
     - No corresponding new module, QPP, DataProvider, JNI, sandbox helper or cancellation-point change in this bounded lookup scope.

   * - 52. JAR install rules in CMakeLists.txt for all dependency JARs
     - N/A
     - No corresponding new module, QPP, DataProvider, JNI, sandbox helper or cancellation-point change in this bounded lookup scope.

   * - 53. No workarounds: No TODOs, FIXMEs, stubs, or partially-implemented features
     - Pass
     - Both defects are corrected directly: use the already-converted key and assign the existence output on each error path. No suppression or runtime workaround.

   * - 54. Exception safety: C++ uses ReferenceHolder for Qore allocations, std::unique_ptr for C++ allocations, *xsink checked after every fallible operation
     - Pass
     - TempEncodingHelper owns conversion storage until lookup completes; conversion errors return before dereferencing it. Native tests use ReferenceHolder, unique_ptr and TypedHashDeclHolder with exception sinks checked after fallible calls.

   * - 55. Thread safety: All mutable shared state protected by std::lock_guard<std::mutex> or documented as immutable-after-construction
     - Pass
     - No shared state is added. Lookups retain existing const/read-only and caller synchronization contracts; fixture counters are single-threaded.

   * - 56. Type safety: Strongly-typed code<return(args)> instead of untyped code; static_cast instead of C casts; typed hashdecls for results; enums where appropriate
     - Pass
     - Existing typed QoreString, QoreValue, bool-reference and ExceptionSink APIs remain intact. Test values and encoding pointers are explicit types.

   * - 57. Performance: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply
     - Pass
     - The conversion already occurred before the fix; its result is now used. No additional copy, traversal or asymptotic cost.

   * - 58. Error handling: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable
     - Pass
     - Both initial existence states, malformed encoding, missing keys, invalid hashdecl members, empty keys and recovery after errors are exercised.

   * - 59. Documentation: Doxygen @param, @return, @throw on all public methods; @par Example with realistic business scenarios; @note for important caveats
     - Pass
     - Public API parameter/result/exception-sink contracts describe converted keys and false error outputs; the realistic account example compiles and runs with both libraries. Release notes and the fixture guide are updated.

   * - 60. QPP flags: [flags=CONSTANT] on methods that never throw; [flags=RET_VALUE_ONLY] on methods that throw but have no side effects
     - N/A
     - No corresponding new module, QPP, DataProvider, JNI, sandbox helper or cancellation-point change in this bounded lookup scope.

   * - 61. Security: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code
     - Pass
     - Converted bytes remain live through the lookup; malformed UTF-16 is rejected. Fixture shell quoting escapes apostrophes, format strings are literal, and no credentials are present.

   * - 62. Correctness: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features)
     - Pass
     - Each mode passes 348 native checks, including Valgrind, plus 15 Qore cases / 302 assertions. Each of the three original-defect groups fails against the original library. Documentation examples produce the expected balance.
