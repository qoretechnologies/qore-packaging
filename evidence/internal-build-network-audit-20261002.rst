Isolated build-interface audit
==============================

Copyright 2026 Qore Technologies, s.r.o.

Scope: opt-in Docker network lifecycle, unit and real RPM integration fixtures, and usage documentation. NATS dependency source changes are not part of this audit.

.. list-table:: Complete audit-changes checklist
   :header-rows: 1

   * - Check
     - Status
     - Evidence

   * - 1. Entry exists in doxygen/lang/120_modules.dox.tmpl (for modules in the Qore repo; N/A for external module repos)
     - N/A
     - No Qore module, QPP class, C++ runtime, DataProvider, JAR dependency or public Qore API changes.

   * - 2. Entry exists in doxygen/lang/900_release_notes.dox.tmpl (for modules in the Qore repo; external modules have release notes in their .qm)
     - N/A
     - No Qore module, QPP class, C++ runtime, DataProvider, JAR dependency or public Qore API changes.

   * - 3. qore_user_module() or qore_external_user_module() call in CMakeLists.txt
     - N/A
     - No Qore module, QPP class, C++ runtime, DataProvider, JAR dependency or public Qore API changes.

   * - 4. Module added to QMOD list in CMakeLists.txt
     - N/A
     - No Qore module, QPP class, C++ runtime, DataProvider, JAR dependency or public Qore API changes.

   * - 5. .qm file has @section <lowercasemodname>intro as first doc section — must be all lowercase (e.g., avrodataproviderintro, not AvroDataProviderintro)
     - N/A
     - No Qore module, QPP class, C++ runtime, DataProvider, JAR dependency or public Qore API changes.

   * - 6. %modern in .qm file — no redundant %new-style, %require-types, %strict-args, %enable-all-warnings
     - N/A
     - No Qore module, QPP class, C++ runtime, DataProvider, JAR dependency or public Qore API changes.

   * - 7. No parse directives (%requires, %modern, %new-style) in separated .qc files (check OUTSIDE of @code blocks only)
     - N/A
     - No Qore module, QPP class, C++ runtime, DataProvider, JAR dependency or public Qore API changes.

   * - 8. No %include usage (deprecated for modules)
     - N/A
     - No Qore module, QPP class, C++ runtime, DataProvider, JAR dependency or public Qore API changes.

   * - 9. Copyright 2026 on all new files
     - Pass
     - All changed/new scripts, fixtures and documentation carry 2026 copyright.

   * - 10. Directory layout: .qm inside qlib/<ModuleName>/ directory (not at qlib/<ModuleName>.qm for multi-file modules)
     - N/A
     - No Qore module, QPP class, C++ runtime, DataProvider, JAR dependency or public Qore API changes.

   * - 11. No second .qm for the same module at qlib/<ModuleName>.qm
     - N/A
     - No Qore module, QPP class, C++ runtime, DataProvider, JAR dependency or public Qore API changes.

   * - 12. ns=Qore::XX matches the QoreNamespace constructor path
     - N/A
     - No Qore module, QPP class, C++ runtime, DataProvider, JAR dependency or public Qore API changes.

   * - 13. %modern directive present
     - N/A
     - No Qore module, QPP class, C++ runtime, DataProvider, JAR dependency or public Qore API changes.

   * - 14. Executable permission set (chmod +x)
     - N/A
     - No Qore module, QPP class, C++ runtime, DataProvider, JAR dependency or public Qore API changes.

   * - 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus)
     - N/A
     - No Qore module, QPP class, C++ runtime, DataProvider, JAR dependency or public Qore API changes.

   * - 16. External module dependencies use %try-module — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard %requires
     - N/A
     - No Qore module, QPP class, C++ runtime, DataProvider, JAR dependency or public Qore API changes.

   * - 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks
     - Pass
     - Python temporary source fixture uses a scoped TemporaryDirectory; native Qore sandbox checks are not applicable.

   * - 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks
     - Pass
     - The Docker build network is private/internal with both gateway modes isolated; effective metadata is verified before use. The regression tests local bind/connect and immediate external ENETUNREACH.

   * - 19. If filesystem/network ops exist, verify QoreSandboxManagerHelper usage
     - N/A
     - No Qore module, QPP class, C++ runtime, DataProvider, JAR dependency or public Qore API changes.

   * - 20. No File::, Dir::, Socket::, HTTPClient:: usage without justification
     - Pass
     - No Qore filesystem or socket API is changed.

   * - 21. All for/while loops that could iterate >100 times have qore_check_cancel() checks
     - N/A
     - No Qore module, QPP class, C++ runtime, DataProvider, JAR dependency or public Qore API changes.

   * - 22. Uses qore_check_cancel() (NOT deprecated qore_check_io_interrupt())
     - N/A
     - No Qore module, QPP class, C++ runtime, DataProvider, JAR dependency or public Qore API changes.

   * - 23. Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations
     - N/A
     - No Qore module, QPP class, C++ runtime, DataProvider, JAR dependency or public Qore API changes.

   * - 24. No blocking operations without cancellation support
     - Pass
     - No sleeps or polling added. Socket regressions have bounded I/O; detached test completion uses waitpid.

   * - 25. Every action has display_name, short_desc (plain text, <80 chars), desc (markdown)
     - N/A
     - No Qore module, QPP class, C++ runtime, DataProvider, JAR dependency or public Qore API changes.

   * - 26. Every action has options populated via getActionOptionFromFields() — without this, the action shows an empty, unusable form
     - N/A
     - No Qore module, QPP class, C++ runtime, DataProvider, JAR dependency or public Qore API changes.

   * - 27. Every action has output_type set to a typed data type constant (e.g., MyResponseDataType) — not omitted
     - N/A
     - No Qore module, QPP class, C++ runtime, DataProvider, JAR dependency or public Qore API changes.

   * - 28. DPAT_API actions: provider has "supports_request": True and implements doRequestImpl()
     - N/A
     - No Qore module, QPP class, C++ runtime, DataProvider, JAR dependency or public Qore API changes.

   * - 29. DPAT_FIND actions: every option exists in SearchOptions, getRecordTypeImpl() returns *hash<string, AbstractDataField>
     - N/A
     - No Qore module, QPP class, C++ runtime, DataProvider, JAR dependency or public Qore API changes.

   * - 30. Scheme-based apps (with "scheme" in registerApp): actions use "path" and do NOT use "cls" — having both scheme and cls causes a runtime error
     - N/A
     - No Qore module, QPP class, C++ runtime, DataProvider, JAR dependency or public Qore API changes.

   * - 31. Single-key hash slices use trailing comma: Fields{"key",} (without trailing comma, Fields{"key"} returns the value, not a hash)
     - N/A
     - No Qore module, QPP class, C++ runtime, DataProvider, JAR dependency or public Qore API changes.

   * - 32. Typed data type classes exist for request and response types — inherit HashDataType, have const Fields hash, call addQoreFields(Fields) in constructor, export public constant at bottom (e.g., public const MyDataType = new MyDataType();)
     - N/A
     - No Qore module, QPP class, C++ runtime, DataProvider, JAR dependency or public Qore API changes.

   * - 33. Request/input types use public Fields (enables ClassName::Fields in action registration)
     - N/A
     - No Qore module, QPP class, C++ runtime, DataProvider, JAR dependency or public Qore API changes.

   * - 34. Response/output types use private Fields
     - N/A
     - No Qore module, QPP class, C++ runtime, DataProvider, JAR dependency or public Qore API changes.

   * - 35. Each field in data types has display_name, type, and desc (markdown-formatted)
     - N/A
     - No Qore module, QPP class, C++ runtime, DataProvider, JAR dependency or public Qore API changes.

   * - 36. Input fields have example_value where useful (string fields, endpoint URIs, SQL queries, etc.)
     - N/A
     - No Qore module, QPP class, C++ runtime, DataProvider, JAR dependency or public Qore API changes.

   * - 37. Fields with finite allowed values use allowed_values with AllowedValueInfo containing both value and display_name (Title Case, human-readable) — never bare values, never described only in text
     - N/A
     - No Qore module, QPP class, C++ runtime, DataProvider, JAR dependency or public Qore API changes.

   * - 38. Password/secret fields have "sensitive": True
     - N/A
     - No Qore module, QPP class, C++ runtime, DataProvider, JAR dependency or public Qore API changes.

   * - 39. groups uses AppGroup enum values from qlib/DataProvider/AppGroup.qc
     - N/A
     - No Qore module, QPP class, C++ runtime, DataProvider, JAR dependency or public Qore API changes.

   * - 40. App logo stored as separate file, loaded at module level in Priv namespace
     - N/A
     - No Qore module, QPP class, C++ runtime, DataProvider, JAR dependency or public Qore API changes.

   * - 41. App desc uses markdown: bullet list of capabilities, links to project website, business-language explanation of value
     - N/A
     - No Qore module, QPP class, C++ runtime, DataProvider, JAR dependency or public Qore API changes.

   * - 42. display_name is user-friendly ("Apache Avro" not "avro")
     - N/A
     - No Qore module, QPP class, C++ runtime, DataProvider, JAR dependency or public Qore API changes.

   * - 43. short_desc is plain text, under 80 chars, single sentence — no markdown
     - N/A
     - No Qore module, QPP class, C++ runtime, DataProvider, JAR dependency or public Qore API changes.

   * - 44. desc uses markdown: backticks for code/field refs ( field_name ,  True ,  pdf ), \n\n for paragraphs, -  bullet lists for enumerations, bold for caveats
     - N/A
     - No Qore module, QPP class, C++ runtime, DataProvider, JAR dependency or public Qore API changes.

   * - 45. Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use"
     - N/A
     - No Qore module, QPP class, C++ runtime, DataProvider, JAR dependency or public Qore API changes.

   * - 46. No bare True/False/NOTHING — must be backtick-wrapped in desc
     - N/A
     - No Qore module, QPP class, C++ runtime, DataProvider, JAR dependency or public Qore API changes.

   * - 47. No bare field/option names in prose — must use backticks
     - N/A
     - No Qore module, QPP class, C++ runtime, DataProvider, JAR dependency or public Qore API changes.

   * - 48. Long descriptions (>500 chars) use bold section headers and bullet lists
     - N/A
     - No Qore module, QPP class, C++ runtime, DataProvider, JAR dependency or public Qore API changes.

   * - 49. Factory registration in Qore repo: every factory name registered in qlib/DataProvider/DataProvider.qc → FactoryMap (without this, module loads but doesn't appear in Qorus apps)
     - N/A
     - No Qore module, QPP class, C++ runtime, DataProvider, JAR dependency or public Qore API changes.

   * - 50. getRecordTypeImpl() signature: must be private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options) — NOT returning *AbstractDataProviderType
     - N/A
     - No Qore module, QPP class, C++ runtime, DataProvider, JAR dependency or public Qore API changes.

   * - 51. Dependency JARs committed (for JNI modules): JAR files in qlib/*/jar/ may be gitignored — use git add -f to ensure they're tracked, otherwise CI compilation fails
     - N/A
     - No Qore module, QPP class, C++ runtime, DataProvider, JAR dependency or public Qore API changes.

   * - 52. JAR install rules in CMakeLists.txt for all dependency JARs
     - N/A
     - No Qore module, QPP class, C++ runtime, DataProvider, JAR dependency or public Qore API changes.

   * - 53. No workarounds: No TODOs, FIXMEs, stubs, or partially-implemented features
     - Pass
     - This supplies the non-loopback interface required by unchanged NATS assertions. No external network, host route, test skip or error suppression is introduced.

   * - 54. Exception safety: C++ uses ReferenceHolder for Qore allocations, std::unique_ptr for C++ allocations, *xsink checked after every fallible operation
     - Pass
     - The context manager removes its uniquely named network after normal completion, test failure, rejected metadata or inspection errors. Temporary source files are context-owned.

   * - 55. Thread safety: All mutable shared state protected by std::lock_guard<std::mutex> or documented as immutable-after-construction
     - Pass
     - Each invocation gets a unique network and uses its immutable ID. No shared mutable process state.

   * - 56. Type safety: Strongly-typed code<return(args)> instead of untyped code; static_cast instead of C casts; typed hashdecls for results; enums where appropriate
     - Pass
     - Configuration is checked against exact boolean/string values before a build is started. Commands are argument lists, not interpolated shell text.

   * - 57. Performance: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply
     - Pass
     - One create/inspect/remove lifecycle per opted-in build; default builds allocate no network resource.

   * - 58. Error handling: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable
     - Pass
     - Tests reject non-internal or non-bridge networks, mismatched IDs/names, attached containers, missing gateway settings, malformed create output and failed inspection. Background drivers propagate the opt-in.

   * - 59. Documentation: Doxygen @param, @return, @throw on all public methods; @par Example with realistic business scenarios; @note for important caveats
     - Pass
     - README documents purpose, offline behavior, Docker-only support, cleanup, usage and a runnable integration command, with the primary Docker gateway-mode reference.

   * - 60. QPP flags: [flags=CONSTANT] on methods that never throw; [flags=RET_VALUE_ONLY] on methods that throw but have no side effects
     - N/A
     - No Qore module, QPP class, C++ runtime, DataProvider, JAR dependency or public Qore API changes.

   * - 61. Security: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code
     - Pass
     - No published ports, host network, privileges, host bridge address or external route. The immutable network ID/configuration is recorded for review.

   * - 62. Correctness: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features)
     - Pass
     - 76 unit tests pass. Live Docker probe verifies bind/connect and immediate external ENETUNREACH; the real RPM integration fixture verifies produced artifacts and network removal. Both affected NATS tests pass three repetitions under the race detector.
