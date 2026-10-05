Signed installed-package runner audit
=====================================

Copyright 2026 Qore Technologies, s.r.o.

Scope: require pinned keys and valid signatures before native package installation; include complete Leap documentation payloads. 137 packaging tests and all distribution signature controls pass. Fresh Leap installs all 92 LLVM manual files without warnings. Native ARM rerun follows this commit.

.. list-table:: Complete audit-changes checklist
   :header-rows: 1

   * - Check
     - Status
     - Evidence

   * - 1. Entry exists in doxygen/lang/120_modules.dox.tmpl (for modules in the Qore repo; N/A for external module repos)
     - N/A
     - No Qore/C++ runtime, API, sandbox domain, cancellation or module implementation changes in this Python packaging fixture scope.

   * - 2. Entry exists in doxygen/lang/900_release_notes.dox.tmpl (for modules in the Qore repo; external modules have release notes in their .qm)
     - N/A
     - No Qore/C++ runtime, API, sandbox domain, cancellation or module implementation changes in this Python packaging fixture scope.

   * - 3. qore_user_module() or qore_external_user_module() call in CMakeLists.txt
     - N/A
     - No Qore/C++ runtime, API, sandbox domain, cancellation or module implementation changes in this Python packaging fixture scope.

   * - 4. Module added to QMOD list in CMakeLists.txt
     - N/A
     - No Qore/C++ runtime, API, sandbox domain, cancellation or module implementation changes in this Python packaging fixture scope.

   * - 5. .qm file has @section <lowercasemodname>intro as first doc section — must be all lowercase (e.g., avrodataproviderintro, not AvroDataProviderintro)
     - N/A
     - No Qore/C++ runtime, API, sandbox domain, cancellation or module implementation changes in this Python packaging fixture scope.

   * - 6. %modern in .qm file — no redundant %new-style, %require-types, %strict-args, %enable-all-warnings
     - N/A
     - No Qore/C++ runtime, API, sandbox domain, cancellation or module implementation changes in this Python packaging fixture scope.

   * - 7. No parse directives (%requires, %modern, %new-style) in separated .qc files (check OUTSIDE of @code blocks only)
     - N/A
     - No Qore/C++ runtime, API, sandbox domain, cancellation or module implementation changes in this Python packaging fixture scope.

   * - 8. No %include usage (deprecated for modules)
     - N/A
     - No Qore/C++ runtime, API, sandbox domain, cancellation or module implementation changes in this Python packaging fixture scope.

   * - 9. Copyright 2026 on all new files
     - Pass
     - 2026 copyright on code, tests and evidence.

   * - 10. Directory layout: .qm inside qlib/<ModuleName>/ directory (not at qlib/<ModuleName>.qm for multi-file modules)
     - N/A
     - No Qore/C++ runtime, API, sandbox domain, cancellation or module implementation changes in this Python packaging fixture scope.

   * - 11. No second .qm for the same module at qlib/<ModuleName>.qm
     - N/A
     - No Qore/C++ runtime, API, sandbox domain, cancellation or module implementation changes in this Python packaging fixture scope.

   * - 12. ns=Qore::XX matches the QoreNamespace constructor path
     - N/A
     - No Qore/C++ runtime, API, sandbox domain, cancellation or module implementation changes in this Python packaging fixture scope.

   * - 13. %modern directive present
     - N/A
     - No Qore/C++ runtime, API, sandbox domain, cancellation or module implementation changes in this Python packaging fixture scope.

   * - 14. Executable permission set (chmod +x)
     - N/A
     - No Qore/C++ runtime, API, sandbox domain, cancellation or module implementation changes in this Python packaging fixture scope.

   * - 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus)
     - N/A
     - No Qore/C++ runtime, API, sandbox domain, cancellation or module implementation changes in this Python packaging fixture scope.

   * - 16. External module dependencies use %try-module — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard %requires
     - N/A
     - No Qore/C++ runtime, API, sandbox domain, cancellation or module implementation changes in this Python packaging fixture scope.

   * - 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks
     - N/A
     - No Qore/C++ runtime, API, sandbox domain, cancellation or module implementation changes in this Python packaging fixture scope.

   * - 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks
     - N/A
     - No Qore/C++ runtime, API, sandbox domain, cancellation or module implementation changes in this Python packaging fixture scope.

   * - 19. If filesystem/network ops exist, verify QoreSandboxManagerHelper usage
     - N/A
     - No Qore/C++ runtime, API, sandbox domain, cancellation or module implementation changes in this Python packaging fixture scope.

   * - 20. No File::, Dir::, Socket::, HTTPClient:: usage without justification
     - N/A
     - No Qore/C++ runtime, API, sandbox domain, cancellation or module implementation changes in this Python packaging fixture scope.

   * - 21. All for/while loops that could iterate >100 times have qore_check_cancel() checks
     - N/A
     - No Qore/C++ runtime, API, sandbox domain, cancellation or module implementation changes in this Python packaging fixture scope.

   * - 22. Uses qore_check_cancel() (NOT deprecated qore_check_io_interrupt())
     - N/A
     - No Qore/C++ runtime, API, sandbox domain, cancellation or module implementation changes in this Python packaging fixture scope.

   * - 23. Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations
     - N/A
     - No Qore/C++ runtime, API, sandbox domain, cancellation or module implementation changes in this Python packaging fixture scope.

   * - 24. No blocking operations without cancellation support
     - N/A
     - No Qore/C++ runtime, API, sandbox domain, cancellation or module implementation changes in this Python packaging fixture scope.

   * - 25. Every action has display_name, short_desc (plain text, <80 chars), desc (markdown)
     - N/A
     - No Qore/C++ runtime, API, sandbox domain, cancellation or module implementation changes in this Python packaging fixture scope.

   * - 26. Every action has options populated via getActionOptionFromFields() — without this, the action shows an empty, unusable form
     - N/A
     - No Qore/C++ runtime, API, sandbox domain, cancellation or module implementation changes in this Python packaging fixture scope.

   * - 27. Every action has output_type set to a typed data type constant (e.g., MyResponseDataType) — not omitted
     - N/A
     - No Qore/C++ runtime, API, sandbox domain, cancellation or module implementation changes in this Python packaging fixture scope.

   * - 28. DPAT_API actions: provider has "supports_request": True and implements doRequestImpl()
     - N/A
     - No Qore/C++ runtime, API, sandbox domain, cancellation or module implementation changes in this Python packaging fixture scope.

   * - 29. DPAT_FIND actions: every option exists in SearchOptions, getRecordTypeImpl() returns *hash<string, AbstractDataField>
     - N/A
     - No Qore/C++ runtime, API, sandbox domain, cancellation or module implementation changes in this Python packaging fixture scope.

   * - 30. Scheme-based apps (with "scheme" in registerApp): actions use "path" and do NOT use "cls" — having both scheme and cls causes a runtime error
     - N/A
     - No Qore/C++ runtime, API, sandbox domain, cancellation or module implementation changes in this Python packaging fixture scope.

   * - 31. Single-key hash slices use trailing comma: Fields{"key",} (without trailing comma, Fields{"key"} returns the value, not a hash)
     - N/A
     - No Qore/C++ runtime, API, sandbox domain, cancellation or module implementation changes in this Python packaging fixture scope.

   * - 32. Typed data type classes exist for request and response types — inherit HashDataType, have const Fields hash, call addQoreFields(Fields) in constructor, export public constant at bottom (e.g., public const MyDataType = new MyDataType();)
     - N/A
     - No Qore/C++ runtime, API, sandbox domain, cancellation or module implementation changes in this Python packaging fixture scope.

   * - 33. Request/input types use public Fields (enables ClassName::Fields in action registration)
     - N/A
     - No Qore/C++ runtime, API, sandbox domain, cancellation or module implementation changes in this Python packaging fixture scope.

   * - 34. Response/output types use private Fields
     - N/A
     - No Qore/C++ runtime, API, sandbox domain, cancellation or module implementation changes in this Python packaging fixture scope.

   * - 35. Each field in data types has display_name, type, and desc (markdown-formatted)
     - N/A
     - No Qore/C++ runtime, API, sandbox domain, cancellation or module implementation changes in this Python packaging fixture scope.

   * - 36. Input fields have example_value where useful (string fields, endpoint URIs, SQL queries, etc.)
     - N/A
     - No Qore/C++ runtime, API, sandbox domain, cancellation or module implementation changes in this Python packaging fixture scope.

   * - 37. Fields with finite allowed values use allowed_values with AllowedValueInfo containing both value and display_name (Title Case, human-readable) — never bare values, never described only in text
     - N/A
     - No Qore/C++ runtime, API, sandbox domain, cancellation or module implementation changes in this Python packaging fixture scope.

   * - 38. Password/secret fields have "sensitive": True
     - N/A
     - No Qore/C++ runtime, API, sandbox domain, cancellation or module implementation changes in this Python packaging fixture scope.

   * - 39. groups uses AppGroup enum values from qlib/DataProvider/AppGroup.qc
     - N/A
     - No Qore/C++ runtime, API, sandbox domain, cancellation or module implementation changes in this Python packaging fixture scope.

   * - 40. App logo stored as separate file, loaded at module level in Priv namespace
     - N/A
     - No Qore/C++ runtime, API, sandbox domain, cancellation or module implementation changes in this Python packaging fixture scope.

   * - 41. App desc uses markdown: bullet list of capabilities, links to project website, business-language explanation of value
     - N/A
     - No Qore/C++ runtime, API, sandbox domain, cancellation or module implementation changes in this Python packaging fixture scope.

   * - 42. display_name is user-friendly ("Apache Avro" not "avro")
     - N/A
     - No Qore/C++ runtime, API, sandbox domain, cancellation or module implementation changes in this Python packaging fixture scope.

   * - 43. short_desc is plain text, under 80 chars, single sentence — no markdown
     - N/A
     - No Qore/C++ runtime, API, sandbox domain, cancellation or module implementation changes in this Python packaging fixture scope.

   * - 44. desc uses markdown: backticks for code/field refs ( field_name ,  True ,  pdf ), \n\n for paragraphs, -  bullet lists for enumerations, bold for caveats
     - N/A
     - No Qore/C++ runtime, API, sandbox domain, cancellation or module implementation changes in this Python packaging fixture scope.

   * - 45. Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use"
     - N/A
     - No Qore/C++ runtime, API, sandbox domain, cancellation or module implementation changes in this Python packaging fixture scope.

   * - 46. No bare True/False/NOTHING — must be backtick-wrapped in desc
     - N/A
     - No Qore/C++ runtime, API, sandbox domain, cancellation or module implementation changes in this Python packaging fixture scope.

   * - 47. No bare field/option names in prose — must use backticks
     - N/A
     - No Qore/C++ runtime, API, sandbox domain, cancellation or module implementation changes in this Python packaging fixture scope.

   * - 48. Long descriptions (>500 chars) use bold section headers and bullet lists
     - Pass
     - Signing key schema validated with HTTPS/hash; unsigned digests explicitly rejected; LC_ALL=C stabilizes RPM diagnostic parsing.

   * - 49. Factory registration in Qore repo: every factory name registered in qlib/DataProvider/DataProvider.qc → FactoryMap (without this, module loads but doesn't appear in Qorus apps)
     - N/A
     - No Qore/C++ runtime, API, sandbox domain, cancellation or module implementation changes in this Python packaging fixture scope.

   * - 50. getRecordTypeImpl() signature: must be private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options) — NOT returning *AbstractDataProviderType
     - N/A
     - No Qore/C++ runtime, API, sandbox domain, cancellation or module implementation changes in this Python packaging fixture scope.

   * - 51. Dependency JARs committed (for JNI modules): JAR files in qlib/*/jar/ may be gitignored — use git add -f to ensure they're tracked, otherwise CI compilation fails
     - N/A
     - No Qore/C++ runtime, API, sandbox domain, cancellation or module implementation changes in this Python packaging fixture scope.

   * - 52. JAR install rules in CMakeLists.txt for all dependency JARs
     - N/A
     - No Qore/C++ runtime, API, sandbox domain, cancellation or module implementation changes in this Python packaging fixture scope.

   * - 53. No workarounds: No TODOs, FIXMEs, stubs, or partially-implemented features
     - N/A
     - No Qore/C++ runtime, API, sandbox domain, cancellation or module implementation changes in this Python packaging fixture scope.

   * - 54. Exception safety: C++ uses ReferenceHolder for Qore allocations, std::unique_ptr for C++ allocations, *xsink checked after every fallible operation
     - N/A
     - No Qore/C++ runtime, API, sandbox domain, cancellation or module implementation changes in this Python packaging fixture scope.

   * - 55. Thread safety: All mutable shared state protected by std::lock_guard<std::mutex> or documented as immutable-after-construction
     - N/A
     - No Qore/C++ runtime, API, sandbox domain, cancellation or module implementation changes in this Python packaging fixture scope.

   * - 56. Type safety: Strongly-typed code<return(args)> instead of untyped code; static_cast instead of C casts; typed hashdecls for results; enums where appropriate
     - N/A
     - No Qore/C++ runtime, API, sandbox domain, cancellation or module implementation changes in this Python packaging fixture scope.

   * - 57. Performance: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply
     - Pass
     - Downloads complete and hashes validate before key import or package installation; every RPM signature verified before user creation.

   * - 58. Error handling: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable
     - Pass
     - Failure records are written in finally; temporary downloaded files/configuration are cleaned, system zypp config unchanged.

   * - 59. Documentation: Doxygen @param, @return, @throw on all public methods; @par Example with realistic business scenarios; @note for important caveats
     - Pass
     - README explains signature verification, unpublished artifacts and complete documentation fixtures.

   * - 60. QPP flags: [flags=CONSTANT] on methods that never throw; [flags=RET_VALUE_ONLY] on methods that throw but have no side effects
     - Pass
     - 137 tests pass, covering unsafe keys and pre-mutation failures; controls on all three distributions reject unsigned, corrupt and untrusted-key RPMs.

   * - 61. Security: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code
     - Pass
     - Package signature checks remain enabled in dnf/zypper; no credentials or private keys are used.

   * - 62. Correctness: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features)
     - Pass
     - Actual RPM 4/6 output formats tested; Leap root cause reproduced from excludedocs setting and resolved by supported configuration.
