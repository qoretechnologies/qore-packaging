ZeroMQ sandbox and private-library release audit
================================================

Copyright 2026 Qore Technologies, s.r.o.

Scope: work/checkouts/module-zmq-sandbox-20261006, eight changed files. All 62 checks reviewed. Evidence: evidence/zmq-release-diagnostics-20261006.json and the separately accepted Fedora PCRE2 control. Three RPM builds, native hash controls, Debug Qore suites and Valgrind passed.

.. list-table:: Complete audit-changes checklist
   :header-rows: 1

   * - Check
     - Status
     - Evidence

   * - 1. Entry exists in doxygen/lang/120_modules.dox.tmpl (for modules in the Qore repo; N/A for external module repos)
     - N/A
     - No new Qore modules/classes, DataProvider APIs, registrations, or binding changes; checklist item does not apply to this scope.

   * - 2. Entry exists in doxygen/lang/900_release_notes.dox.tmpl (for modules in the Qore repo; external modules have release notes in their .qm)
     - N/A
     - No new Qore modules/classes, DataProvider APIs, registrations, or binding changes; checklist item does not apply to this scope.

   * - 3. qore_user_module() or qore_external_user_module() call in CMakeLists.txt
     - N/A
     - No new Qore modules/classes, DataProvider APIs, registrations, or binding changes; checklist item does not apply to this scope.

   * - 4. Module added to QMOD list in CMakeLists.txt
     - N/A
     - No new Qore modules/classes, DataProvider APIs, registrations, or binding changes; checklist item does not apply to this scope.

   * - 5. .qm file has @section <lowercasemodname>intro as first doc section — must be all lowercase (e.g., avrodataproviderintro, not AvroDataProviderintro)
     - N/A
     - No new Qore modules/classes, DataProvider APIs, registrations, or binding changes; checklist item does not apply to this scope.

   * - 6. %modern in .qm file — no redundant %new-style, %require-types, %strict-args, %enable-all-warnings
     - N/A
     - No new Qore modules/classes, DataProvider APIs, registrations, or binding changes; checklist item does not apply to this scope.

   * - 7. No parse directives (%requires, %modern, %new-style) in separated .qc files (check OUTSIDE of @code blocks only)
     - N/A
     - No new Qore modules/classes, DataProvider APIs, registrations, or binding changes; checklist item does not apply to this scope.

   * - 8. No %include usage (deprecated for modules)
     - N/A
     - No new Qore modules/classes, DataProvider APIs, registrations, or binding changes; checklist item does not apply to this scope.

   * - 9. Copyright 2026 on all new files
     - Pass
     - New fixtures and modified packaging documentation carry 2026 notices.

   * - 10. Directory layout: .qm inside qlib/<ModuleName>/ directory (not at qlib/<ModuleName>.qm for multi-file modules)
     - N/A
     - No new Qore modules/classes, DataProvider APIs, registrations, or binding changes; checklist item does not apply to this scope.

   * - 11. No second .qm for the same module at qlib/<ModuleName>.qm
     - N/A
     - No new Qore modules/classes, DataProvider APIs, registrations, or binding changes; checklist item does not apply to this scope.

   * - 12. ns=Qore::XX matches the QoreNamespace constructor path
     - N/A
     - No new Qore modules/classes, DataProvider APIs, registrations, or binding changes; checklist item does not apply to this scope.

   * - 13. %modern directive present
     - Pass
     - Sandbox regression explicitly uses %modern; its embedded programs do too.

   * - 14. Executable permission set (chmod +x)
     - Pass
     - Sandbox .qtest and its Python runner are executable.

   * - 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus)
     - Pass
     - No source Qore module is imported. The runner explicitly preloads the exact build .qmod with -l before the hard same-repository zmq requirement.

   * - 16. External module dependencies use %try-module — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard %requires
     - Pass
     - zmq belongs to this repository and QUnit belongs to Qore; both are hard requirements.

   * - 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks
     - Pass
     - No new production filesystem operations; archive header mode correction is packaging only.

   * - 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks
     - Pass
     - Existing network policy is retained. Denied IPv4/IPv6/hostname cases and allowed operations are tested.

   * - 19. If filesystem/network ops exist, verify QoreSandboxManagerHelper usage
     - Pass
     - Existing QoreSandboxManager probes still make all network decisions; only temporary rejected-address errors are consumed.

   * - 20. No File::, Dir::, Socket::, HTTPClient:: usage without justification
     - Pass
     - Network access is intentional in local sandbox regression controls.

   * - 21. All for/while loops that could iterate >100 times have qore_check_cancel() checks
     - Pass
     - Existing cancellation check in the message frame loop is retained; native hash loops are standalone bounded tests outside Qore.

   * - 22. Uses qore_check_cancel() (NOT deprecated qore_check_io_interrupt())
     - Pass
     - Existing qore_check_cancel call is unchanged.

   * - 23. Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations
     - Pass
     - Message serialization continues checking cancellation every 100 frames.

   * - 24. No blocking operations without cancellation support
     - Pass
     - No new blocking production calls; package suites retain bounded execution. Local controls terminate after fixed lifetimes.

   * - 25. Every action has display_name, short_desc (plain text, <80 chars), desc (markdown)
     - N/A
     - No new Qore modules/classes, DataProvider APIs, registrations, or binding changes; checklist item does not apply to this scope.

   * - 26. Every action has options populated via getActionOptionFromFields() — without this, the action shows an empty, unusable form
     - N/A
     - No new Qore modules/classes, DataProvider APIs, registrations, or binding changes; checklist item does not apply to this scope.

   * - 27. Every action has output_type set to a typed data type constant (e.g., MyResponseDataType) — not omitted
     - N/A
     - No new Qore modules/classes, DataProvider APIs, registrations, or binding changes; checklist item does not apply to this scope.

   * - 28. DPAT_API actions: provider has "supports_request": True and implements doRequestImpl()
     - N/A
     - No new Qore modules/classes, DataProvider APIs, registrations, or binding changes; checklist item does not apply to this scope.

   * - 29. DPAT_FIND actions: every option exists in SearchOptions, getRecordTypeImpl() returns *hash<string, AbstractDataField>
     - N/A
     - No new Qore modules/classes, DataProvider APIs, registrations, or binding changes; checklist item does not apply to this scope.

   * - 30. Scheme-based apps (with "scheme" in registerApp): actions use "path" and do NOT use "cls" — having both scheme and cls causes a runtime error
     - N/A
     - No new Qore modules/classes, DataProvider APIs, registrations, or binding changes; checklist item does not apply to this scope.

   * - 31. Single-key hash slices use trailing comma: Fields{"key",} (without trailing comma, Fields{"key"} returns the value, not a hash)
     - N/A
     - No new Qore modules/classes, DataProvider APIs, registrations, or binding changes; checklist item does not apply to this scope.

   * - 32. Typed data type classes exist for request and response types — inherit HashDataType, have const Fields hash, call addQoreFields(Fields) in constructor, export public constant at bottom (e.g., public const MyDataType = new MyDataType();)
     - N/A
     - No new Qore modules/classes, DataProvider APIs, registrations, or binding changes; checklist item does not apply to this scope.

   * - 33. Request/input types use public Fields (enables ClassName::Fields in action registration)
     - N/A
     - No new Qore modules/classes, DataProvider APIs, registrations, or binding changes; checklist item does not apply to this scope.

   * - 34. Response/output types use private Fields
     - N/A
     - No new Qore modules/classes, DataProvider APIs, registrations, or binding changes; checklist item does not apply to this scope.

   * - 35. Each field in data types has display_name, type, and desc (markdown-formatted)
     - N/A
     - No new Qore modules/classes, DataProvider APIs, registrations, or binding changes; checklist item does not apply to this scope.

   * - 36. Input fields have example_value where useful (string fields, endpoint URIs, SQL queries, etc.)
     - N/A
     - No new Qore modules/classes, DataProvider APIs, registrations, or binding changes; checklist item does not apply to this scope.

   * - 37. Fields with finite allowed values use allowed_values with AllowedValueInfo containing both value and display_name (Title Case, human-readable) — never bare values, never described only in text
     - N/A
     - No new Qore modules/classes, DataProvider APIs, registrations, or binding changes; checklist item does not apply to this scope.

   * - 38. Password/secret fields have "sensitive": True
     - N/A
     - No new Qore modules/classes, DataProvider APIs, registrations, or binding changes; checklist item does not apply to this scope.

   * - 39. groups uses AppGroup enum values from qlib/DataProvider/AppGroup.qc
     - N/A
     - No new Qore modules/classes, DataProvider APIs, registrations, or binding changes; checklist item does not apply to this scope.

   * - 40. App logo stored as separate file, loaded at module level in Priv namespace
     - N/A
     - No new Qore modules/classes, DataProvider APIs, registrations, or binding changes; checklist item does not apply to this scope.

   * - 41. App desc uses markdown: bullet list of capabilities, links to project website, business-language explanation of value
     - N/A
     - No new Qore modules/classes, DataProvider APIs, registrations, or binding changes; checklist item does not apply to this scope.

   * - 42. display_name is user-friendly ("Apache Avro" not "avro")
     - N/A
     - No new Qore modules/classes, DataProvider APIs, registrations, or binding changes; checklist item does not apply to this scope.

   * - 43. short_desc is plain text, under 80 chars, single sentence — no markdown
     - N/A
     - No new Qore modules/classes, DataProvider APIs, registrations, or binding changes; checklist item does not apply to this scope.

   * - 44. desc uses markdown: backticks for code/field refs ( field_name ,  True ,  pdf ), \n\n for paragraphs, -  bullet lists for enumerations, bold for caveats
     - N/A
     - No new Qore modules/classes, DataProvider APIs, registrations, or binding changes; checklist item does not apply to this scope.

   * - 45. Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use"
     - N/A
     - No new Qore modules/classes, DataProvider APIs, registrations, or binding changes; checklist item does not apply to this scope.

   * - 46. No bare True/False/NOTHING — must be backtick-wrapped in desc
     - N/A
     - No new Qore modules/classes, DataProvider APIs, registrations, or binding changes; checklist item does not apply to this scope.

   * - 47. No bare field/option names in prose — must use backticks
     - N/A
     - No new Qore modules/classes, DataProvider APIs, registrations, or binding changes; checklist item does not apply to this scope.

   * - 48. Long descriptions (>500 chars) use bold section headers and bullet lists
     - N/A
     - No new Qore modules/classes, DataProvider APIs, registrations, or binding changes; checklist item does not apply to this scope.

   * - 49. Factory registration in Qore repo: every factory name registered in qlib/DataProvider/DataProvider.qc → FactoryMap (without this, module loads but doesn't appear in Qorus apps)
     - N/A
     - No new Qore modules/classes, DataProvider APIs, registrations, or binding changes; checklist item does not apply to this scope.

   * - 50. getRecordTypeImpl() signature: must be private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options) — NOT returning *AbstractDataProviderType
     - N/A
     - No new Qore modules/classes, DataProvider APIs, registrations, or binding changes; checklist item does not apply to this scope.

   * - 51. Dependency JARs committed (for JNI modules): JAR files in qlib/*/jar/ may be gitignored — use git add -f to ensure they're tracked, otherwise CI compilation fails
     - N/A
     - No new Qore modules/classes, DataProvider APIs, registrations, or binding changes; checklist item does not apply to this scope.

   * - 52. JAR install rules in CMakeLists.txt for all dependency JARs
     - N/A
     - No new Qore modules/classes, DataProvider APIs, registrations, or binding changes; checklist item does not apply to this scope.

   * - 53. No workarounds: No TODOs, FIXMEs, stubs, or partially-implemented features
     - Pass
     - Private CZMQ assertion policy explicitly approved by user on 2026-10-06. No source-warning suppression or functionality disabling.

   * - 54. Exception safety: C++ uses ReferenceHolder for Qore allocations, std::unique_ptr for C++ allocations, *xsink checked after every fallible operation
     - Pass
     - Temporary ExceptionSink is cleared per failed address; freeaddrinfo and caller-visible final denial remain. Native fixture releases the table on every failure path. Valgrind finds no lost allocations.

   * - 55. Thread safety: All mutable shared state protected by std::lock_guard<std::mutex> or documented as immutable-after-construction
     - Pass
     - No production shared state added; hash callback state is explicitly single-threaded. Tests retain separate Program/socket lifetimes.

   * - 56. Type safety: Strongly-typed code<return(args)> instead of untyped code; static_cast instead of C casts; typed hashdecls for results; enums where appropriate
     - Pass
     - Qore tests use typed parameters and ExceptionInfo; existing socket frame types retained. The native C callback follows the CZMQ API.

   * - 57. Performance: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply
     - Pass
     - Required CZMQ rehashing is restored: 10000 entries grow from 3 to 16349 buckets; unused frame-size arithmetic removed.

   * - 58. Error handling: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable
     - Pass
     - Regression rejects unexpected stderr, missing sandbox denial, duplicate-key replacement, missing rehashes, wrong lookup values and failed deletion.

   * - 59. Documentation: Doxygen @param, @return, @throw on all public methods; @par Example with realistic business scenarios; @note for important caveats
     - Pass
     - RPM release notes and README document network behavior, required assertion expressions and the 10000-key regression.

   * - 60. QPP flags: [flags=CONSTANT] on methods that never throw; [flags=RET_VALUE_ONLY] on methods that throw but have no side effects
     - Pass
     - No QPP API signatures or functional domains changed.

   * - 61. Security: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code
     - Pass
     - Final network denial remains mandatory; numeric/address validation unchanged. No secrets or new external endpoints.

   * - 62. Correctness: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features)
     - Pass
     - All three final builds pass 127 test executions/3958 assertions plus documentation and native growth checks. NDEBUG and old sandbox controls fail as expected; 60000 enum cases and native hash Valgrind controls pass.
