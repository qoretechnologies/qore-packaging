AOT RPM runtime identity audit
==============================

Copyright 2026 Qore Technologies, s.r.o.

Scope: the two C++ identity-section changes; the upstream CMake fingerprint-before-identity ordering fix (1369d1bd5); qore.spec-multi; RPM generator, attributes, macros and tests; durable design, packaging documentation and release notes. The checklist applies to this delta on published develop 4460f705b. Other-session local commits are excluded.

Static review: 16 Pass, 46 N/A, 0 Fail. Release and Debug builds, loader/CSE regressions, actual qcc RPM tests, six compile/load Valgrind controls and four cross-mode loads pass on the published develop base. Commit qualification still awaits the separately documented local Debug dependency diagnostics decision.

.. list-table:: Full audit-changes checklist
   :header-rows: 1

   * - Check
     - Status
     - Evidence

   * - 1. Entry exists in doxygen/lang/120_modules.dox.tmpl (for modules in the Qore repo; N/A for external module repos)
     - N/A
     - No new production .qm module or QPP class; this change adds ELF identity metadata and RPM build helpers.

   * - 2. Entry exists in doxygen/lang/900_release_notes.dox.tmpl (for modules in the Qore repo; external modules have release notes in their .qm)
     - Pass
     - Release notes explain exact RPM identity requirements and paired runtime/module upgrades.

   * - 3. qore_user_module() or qore_external_user_module() call in CMakeLists.txt
     - N/A
     - No new production .qm module or QPP class; this change adds ELF identity metadata and RPM build helpers.

   * - 4. Module added to QMOD list in CMakeLists.txt
     - N/A
     - No new production .qm module or QPP class; this change adds ELF identity metadata and RPM build helpers.

   * - 5. .qm file has @section <lowercasemodname>intro as first doc section — must be all lowercase (e.g., avrodataproviderintro, not AvroDataProviderintro)
     - N/A
     - No new production .qm module or QPP class; this change adds ELF identity metadata and RPM build helpers.

   * - 6. %modern in .qm file — no redundant %new-style, %require-types, %strict-args, %enable-all-warnings
     - N/A
     - No new production .qm module or QPP class; this change adds ELF identity metadata and RPM build helpers.

   * - 7. No parse directives (%requires, %modern, %new-style) in separated .qc files (check OUTSIDE of @code blocks only)
     - N/A
     - No new production .qm module or QPP class; this change adds ELF identity metadata and RPM build helpers.

   * - 8. No %include usage (deprecated for modules)
     - N/A
     - No new production .qm module or QPP class; this change adds ELF identity metadata and RPM build helpers.

   * - 9. Copyright 2026 on all new files
     - Pass
     - All four new helper/attribute/test files carry Qore Technologies copyright 2026 and MIT identifiers.

   * - 10. Directory layout: .qm inside qlib/<ModuleName>/ directory (not at qlib/<ModuleName>.qm for multi-file modules)
     - N/A
     - No new production .qm module or QPP class; this change adds ELF identity metadata and RPM build helpers.

   * - 11. No second .qm for the same module at qlib/<ModuleName>.qm
     - N/A
     - No new production .qm module or QPP class; this change adds ELF identity metadata and RPM build helpers.

   * - 12. ns=Qore::XX matches the QoreNamespace constructor path
     - N/A
     - No new production .qm module or QPP class; this change adds ELF identity metadata and RPM build helpers.

   * - 13. %modern directive present
     - Pass
     - The generated real-qcc Probe module explicitly uses %modern; existing AOT QUnit regression runs with --enable-debug.

   * - 14. Executable permission set (chmod +x)
     - N/A
     - No .qtest added or modified and no new Qore import. Existing in-tree AOT loader regressions are reused; generated Probe has no dependencies.

   * - 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus)
     - N/A
     - No .qtest added or modified and no new Qore import. Existing in-tree AOT loader regressions are reused; generated Probe has no dependencies.

   * - 16. External module dependencies use %try-module — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard %requires
     - N/A
     - No .qtest added or modified and no new Qore import. Existing in-tree AOT loader regressions are reused; generated Probe has no dependencies.

   * - 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks
     - Pass
     - The C++ delta contains only static data and LLVM global section/alignment attributes; no filesystem operations added.

   * - 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks
     - Pass
     - No network operations added. Python reads ELF only during package building, outside the Qore runtime.

   * - 19. If filesystem/network ops exist, verify QoreSandboxManagerHelper usage
     - N/A
     - No C++ filesystem or network operations added, so no new sandbox helper is needed.

   * - 20. No File::, Dir::, Socket::, HTTPClient:: usage without justification
     - N/A
     - No production Qore-language code changes or File/Dir/Socket/HTTPClient operations.

   * - 21. All for/while loops that could iterate >100 times have qore_check_cancel() checks
     - Pass
     - No C++ loops added; global lookup and attribute assignment do not introduce an unbounded Qore operation.

   * - 22. Uses qore_check_cancel() (NOT deprecated qore_check_io_interrupt())
     - N/A
     - No C++ loop or blocking operation added; existing cancellation behavior remains unchanged.

   * - 23. Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations
     - N/A
     - No C++ loop or blocking operation added; existing cancellation behavior remains unchanged.

   * - 24. No blocking operations without cancellation support
     - Pass
     - No blocking C++ operation added.

   * - 25. Every action has display_name, short_desc (plain text, <80 chars), desc (markdown)
     - N/A
     - No DataProvider, app/action registration, typed provider metadata, factory registration, JNI or JAR changes.

   * - 26. Every action has options populated via getActionOptionFromFields() — without this, the action shows an empty, unusable form
     - N/A
     - No DataProvider, app/action registration, typed provider metadata, factory registration, JNI or JAR changes.

   * - 27. Every action has output_type set to a typed data type constant (e.g., MyResponseDataType) — not omitted
     - N/A
     - No DataProvider, app/action registration, typed provider metadata, factory registration, JNI or JAR changes.

   * - 28. DPAT_API actions: provider has "supports_request": True and implements doRequestImpl()
     - N/A
     - No DataProvider, app/action registration, typed provider metadata, factory registration, JNI or JAR changes.

   * - 29. DPAT_FIND actions: every option exists in SearchOptions, getRecordTypeImpl() returns *hash<string, AbstractDataField>
     - N/A
     - No DataProvider, app/action registration, typed provider metadata, factory registration, JNI or JAR changes.

   * - 30. Scheme-based apps (with "scheme" in registerApp): actions use "path" and do NOT use "cls" — having both scheme and cls causes a runtime error
     - N/A
     - No DataProvider, app/action registration, typed provider metadata, factory registration, JNI or JAR changes.

   * - 31. Single-key hash slices use trailing comma: Fields{"key",} (without trailing comma, Fields{"key"} returns the value, not a hash)
     - N/A
     - No DataProvider, app/action registration, typed provider metadata, factory registration, JNI or JAR changes.

   * - 32. Typed data type classes exist for request and response types — inherit HashDataType, have const Fields hash, call addQoreFields(Fields) in constructor, export public constant at bottom (e.g., public const MyDataType = new MyDataType();)
     - N/A
     - No DataProvider, app/action registration, typed provider metadata, factory registration, JNI or JAR changes.

   * - 33. Request/input types use public Fields (enables ClassName::Fields in action registration)
     - N/A
     - No DataProvider, app/action registration, typed provider metadata, factory registration, JNI or JAR changes.

   * - 34. Response/output types use private Fields
     - N/A
     - No DataProvider, app/action registration, typed provider metadata, factory registration, JNI or JAR changes.

   * - 35. Each field in data types has display_name, type, and desc (markdown-formatted)
     - N/A
     - No DataProvider, app/action registration, typed provider metadata, factory registration, JNI or JAR changes.

   * - 36. Input fields have example_value where useful (string fields, endpoint URIs, SQL queries, etc.)
     - N/A
     - No DataProvider, app/action registration, typed provider metadata, factory registration, JNI or JAR changes.

   * - 37. Fields with finite allowed values use allowed_values with AllowedValueInfo containing both value and display_name (Title Case, human-readable) — never bare values, never described only in text
     - N/A
     - No DataProvider, app/action registration, typed provider metadata, factory registration, JNI or JAR changes.

   * - 38. Password/secret fields have "sensitive": True
     - N/A
     - No DataProvider, app/action registration, typed provider metadata, factory registration, JNI or JAR changes.

   * - 39. groups uses AppGroup enum values from qlib/DataProvider/AppGroup.qc
     - N/A
     - No DataProvider, app/action registration, typed provider metadata, factory registration, JNI or JAR changes.

   * - 40. App logo stored as separate file, loaded at module level in Priv namespace
     - N/A
     - No DataProvider, app/action registration, typed provider metadata, factory registration, JNI or JAR changes.

   * - 41. App desc uses markdown: bullet list of capabilities, links to project website, business-language explanation of value
     - N/A
     - No DataProvider, app/action registration, typed provider metadata, factory registration, JNI or JAR changes.

   * - 42. display_name is user-friendly ("Apache Avro" not "avro")
     - N/A
     - No DataProvider, app/action registration, typed provider metadata, factory registration, JNI or JAR changes.

   * - 43. short_desc is plain text, under 80 chars, single sentence — no markdown
     - N/A
     - No DataProvider, app/action registration, typed provider metadata, factory registration, JNI or JAR changes.

   * - 44. desc uses markdown: backticks for code/field refs ( field_name ,  True ,  pdf ), \n\n for paragraphs, -  bullet lists for enumerations, bold for caveats
     - N/A
     - No DataProvider, app/action registration, typed provider metadata, factory registration, JNI or JAR changes.

   * - 45. Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use"
     - N/A
     - No DataProvider, app/action registration, typed provider metadata, factory registration, JNI or JAR changes.

   * - 46. No bare True/False/NOTHING — must be backtick-wrapped in desc
     - N/A
     - No DataProvider, app/action registration, typed provider metadata, factory registration, JNI or JAR changes.

   * - 47. No bare field/option names in prose — must use backticks
     - N/A
     - No DataProvider, app/action registration, typed provider metadata, factory registration, JNI or JAR changes.

   * - 48. Long descriptions (>500 chars) use bold section headers and bullet lists
     - N/A
     - No DataProvider, app/action registration, typed provider metadata, factory registration, JNI or JAR changes.

   * - 49. Factory registration in Qore repo: every factory name registered in qlib/DataProvider/DataProvider.qc → FactoryMap (without this, module loads but doesn't appear in Qorus apps)
     - N/A
     - No DataProvider, app/action registration, typed provider metadata, factory registration, JNI or JAR changes.

   * - 50. getRecordTypeImpl() signature: must be private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options) — NOT returning *AbstractDataProviderType
     - N/A
     - No DataProvider, app/action registration, typed provider metadata, factory registration, JNI or JAR changes.

   * - 51. Dependency JARs committed (for JNI modules): JAR files in qlib/*/jar/ may be gitignored — use git add -f to ensure they're tracked, otherwise CI compilation fails
     - N/A
     - No DataProvider, app/action registration, typed provider metadata, factory registration, JNI or JAR changes.

   * - 52. JAR install rules in CMakeLists.txt for all dependency JARs
     - N/A
     - No DataProvider, app/action registration, typed provider metadata, factory registration, JNI or JAR changes.

   * - 53. No workarounds: No TODOs, FIXMEs, stubs, or partially-implemented features
     - Pass
     - No stubs, TODOs, filters or policy bypasses. RPM intentionally ignores generator failures; the same parser also runs as a mandatory checked build command. Real malformed/legacy RPM tests prove failure before output packages exist.

   * - 54. Exception safety: C++ uses ReferenceHolder for Qore allocations, std::unique_ptr for C++ allocations, *xsink checked after every fallible operation
     - Pass
     - Static const storage owns the runtime string; the existing exported pointer references it. LLVM Module owns the GlobalVariable. No new Qore allocation, raw ownership transfer, ExceptionSink or manual cleanup. Python files and temporary fixture roots use context managers.

   * - 55. Thread safety: All mutable shared state protected by std::lock_guard<std::mutex> or documented as immutable-after-construction
     - Pass
     - Identity bytes are immutable static storage. Compiler modifications affect its existing per-compilation Module only. Parser state is local; no mutable global caches.

   * - 56. Type safety: Strongly-typed code<return(args)> instead of untyped code; static_cast instead of C casts; typed hashdecls for results; enums where appropriate
     - Pass
     - C++ uses the existing typed GlobalVariable API and llvm::Align. Python exposes typed BinaryIO/Path, role/digest tuples and dependency lists, with explicit ELF class/byte-order/ISA validation.

   * - 57. Performance: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply
     - Pass
     - Section table traversal is linear, with constant-size comparisons of relevant section names. Overlapping name suffixes cannot cause quadratic scans. Linked identity records are checked one at a time; data reads are bounded by file size.

   * - 58. Error handling: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable
     - Pass
     - Rejects truncated files, invalid ELF tables, unsupported/duplicate identity sections, inconsistent merged records, invalid role/path combinations and legacy AOT metadata. CLI accumulates before output so an error cannot emit partial requirements. Missing files and mandatory validation fail normally.

   * - 59. Documentation: Doxygen @param, @return, @throw on all public methods; @par Example with realistic business scenarios; @note for important caveats
     - Pass
     - Durable AOT design and RPM README document ELF layout, exact capability names, native-only behavior, bootstrap, strip safety and why a checked validation phase is required. Release notes explain upgrade implications. No new public Qore method.

   * - 60. QPP flags: [flags=CONSTANT] on methods that never throw; [flags=RET_VALUE_ONLY] on methods that throw but have no side effects
     - N/A
     - No QPP method or flags changed.

   * - 61. Security: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code
     - Pass
     - ELF parsing never loads or executes the target artifact. Explicit bounds and format checks cover all reads. ISA/digest validation excludes capability syntax injection. RPM transaction tests use a private database, never the host package database.

   * - 62. Correctness: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features)
     - Pass
     - Four ELF width/endian combinations, extended tables, every truncated prefix, bad metadata, symlink behavior, exact digest comparison, actual stripped runtime source, real qcc reproducibility/load/debug sources and real RPM install/upgrade/removal transactions are covered. The final 51-method matrix covers all three targets, with four installed-dependency checks enabled separately. Refreshed Release/Debug builds pass actual qcc RPM integration, 26 AOT loader cases/134 assertions, both CSE regressions and six Valgrind controls with zero errors or lost memory. Four cross-mode loads pass. The two actual generated build graphs now order fingerprint generation before identity generation; changed/restored input controls and the five existing fingerprint tests pass.
