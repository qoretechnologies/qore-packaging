RPM qualification follow-up review
==================================

Copyright 2026 Qore Technologies, s.r.o.

Scope: Qore e840e786c; ncurses bafa758; Kalman cfeea66 and 4fd90f0;
packaging 8045668; tested hardlink BuildRequires updates in thirteen modules.
Additional reviewed scope: Qore b089f733a engine cleanup, packaging f98fd1d
source completeness, Process 1c80192ca, MongoDB 66e15a5, and nghttp2 timezone
requirements baf8299. Native OBS rebuilds remain a separate gate. Method: the complete audit-changes skill
checklist at /home/david/.codex/skills/audit-changes/SKILL.md.

Native target RPM parsing/provider checks passed on Fedora, EL10 and Leap.
ONNX's initialized environment baseline reproduces exactly the user-approved
512-byte cpuinfo allocation on EL; Leap reports no lost bytes. Both report zero
other memory errors. Compiled ncurses requires magic; removal protection is tested.
Fedora build 9 passes installed SDK and minimal runtime checks. Its module
rebuilds, remaining target/architecture builds and release gates remain required
before publication. Existing
Qore build/documentation warnings and the optional qjar notice are not represented
as a warning-free core build. Local Source0 archive policy warnings are retained.

.. list-table:: Complete skill checklist
   :header-rows: 1
   :widths: 48 8 44

   * - Check
     - Status
     - Evidence

   * - Entry exists in doxygen/lang/120_modules.dox.tmpl (for modules in the Qore repo; N/A for external module repos)
     - N/A
     - No new Qore module, QPP class, runtime method, DataProvider registration or Qore test file in this documentation, build and packaging change set.

   * - Entry exists in doxygen/lang/900_release_notes.dox.tmpl (for modules in the Qore repo; external modules have release notes in their .qm)
     - Pass
     - Qore b089f733a documents modern OpenSSL cleanup. The AMQP mainpage release notes document corrected cross-module documentation. No new public runtime API is added.

   * - qore_user_module() or qore_external_user_module() call in CMakeLists.txt
     - N/A
     - No new Qore module, QPP class, runtime method, DataProvider registration or Qore test file in this documentation, build and packaging change set.

   * - Module added to QMOD list in CMakeLists.txt
     - N/A
     - No new Qore module, QPP class, runtime method, DataProvider registration or Qore test file in this documentation, build and packaging change set.

   * - .qm file has @section <lowercasemodname>intro as first doc section — must be all lowercase (e.g., avrodataproviderintro, not AvroDataProviderintro)
     - N/A
     - No new Qore module, QPP class, runtime method, DataProvider registration or Qore test file in this documentation, build and packaging change set.

   * - %modern in .qm file — no redundant %new-style, %require-types, %strict-args, %enable-all-warnings
     - N/A
     - No new Qore module, QPP class, runtime method, DataProvider registration or Qore test file in this documentation, build and packaging change set.

   * - No parse directives (%requires, %modern, %new-style) in separated .qc files (check OUTSIDE of @code blocks only)
     - N/A
     - No new Qore module, QPP class, runtime method, DataProvider registration or Qore test file in this documentation, build and packaging change set.

   * - No %include usage (deprecated for modules)
     - N/A
     - No new Qore module, QPP class, runtime method, DataProvider registration or Qore test file in this documentation, build and packaging change set.

   * - Copyright 2026 on all new files
     - Pass
     - New uninstall, test and packaging files carry 2026 notices.

   * - Directory layout: .qm inside qlib/<ModuleName>/ directory (not at qlib/<ModuleName>.qm for multi-file modules)
     - N/A
     - No new Qore module, QPP class, runtime method, DataProvider registration or Qore test file in this documentation, build and packaging change set.

   * - No second .qm for the same module at qlib/<ModuleName>.qm
     - N/A
     - No new Qore module, QPP class, runtime method, DataProvider registration or Qore test file in this documentation, build and packaging change set.

   * - ns=Qore::XX matches the QoreNamespace constructor path
     - N/A
     - No new Qore module, QPP class, runtime method, DataProvider registration or Qore test file in this documentation, build and packaging change set.

   * - %modern directive present
     - N/A
     - No new Qore module, QPP class, runtime method, DataProvider registration or Qore test file in this documentation, build and packaging change set.

   * - Executable permission set (chmod +x)
     - N/A
     - No new Qore module, QPP class, runtime method, DataProvider registration or Qore test file in this documentation, build and packaging change set.

   * - Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus)
     - N/A
     - No new Qore module, QPP class, runtime method, DataProvider registration or Qore test file in this documentation, build and packaging change set.

   * - External module dependencies use %try-module — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard %requires
     - N/A
     - No new Qore module, QPP class, runtime method, DataProvider registration or Qore test file in this documentation, build and packaging change set.

   * - No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks
     - N/A
     - No new Qore module, QPP class, runtime method, DataProvider registration or Qore test file in this documentation, build and packaging change set.

   * - No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks
     - N/A
     - No new Qore module, QPP class, runtime method, DataProvider registration or Qore test file in this documentation, build and packaging change set.

   * - If filesystem/network ops exist, verify QoreSandboxManagerHelper usage
     - N/A
     - No new Qore module, QPP class, runtime method, DataProvider registration or Qore test file in this documentation, build and packaging change set.

   * - No File::, Dir::, Socket::, HTTPClient:: usage without justification
     - N/A
     - No new Qore module, QPP class, runtime method, DataProvider registration or Qore test file in this documentation, build and packaging change set.

   * - All for/while loops that could iterate >100 times have qore_check_cancel() checks
     - N/A
     - No new Qore module, QPP class, runtime method, DataProvider registration or Qore test file in this documentation, build and packaging change set.

   * - Uses qore_check_cancel() (NOT deprecated qore_check_io_interrupt())
     - N/A
     - No new Qore module, QPP class, runtime method, DataProvider registration or Qore test file in this documentation, build and packaging change set.

   * - Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations
     - N/A
     - No new Qore module, QPP class, runtime method, DataProvider registration or Qore test file in this documentation, build and packaging change set.

   * - No blocking operations without cancellation support
     - N/A
     - No new Qore module, QPP class, runtime method, DataProvider registration or Qore test file in this documentation, build and packaging change set.

   * - Every action has display_name, short_desc (plain text, <80 chars), desc (markdown)
     - N/A
     - No new Qore module, QPP class, runtime method, DataProvider registration or Qore test file in this documentation, build and packaging change set.

   * - Every action has options populated via getActionOptionFromFields() — without this, the action shows an empty, unusable form
     - N/A
     - No new Qore module, QPP class, runtime method, DataProvider registration or Qore test file in this documentation, build and packaging change set.

   * - Every action has output_type set to a typed data type constant (e.g., MyResponseDataType) — not omitted
     - N/A
     - No new Qore module, QPP class, runtime method, DataProvider registration or Qore test file in this documentation, build and packaging change set.

   * - DPAT_API actions: provider has "supports_request": True and implements doRequestImpl()
     - N/A
     - No new Qore module, QPP class, runtime method, DataProvider registration or Qore test file in this documentation, build and packaging change set.

   * - DPAT_FIND actions: every option exists in SearchOptions, getRecordTypeImpl() returns *hash<string, AbstractDataField>
     - N/A
     - No new Qore module, QPP class, runtime method, DataProvider registration or Qore test file in this documentation, build and packaging change set.

   * - Scheme-based apps (with "scheme" in registerApp): actions use "path" and do NOT use "cls" — having both scheme and cls causes a runtime error
     - N/A
     - No new Qore module, QPP class, runtime method, DataProvider registration or Qore test file in this documentation, build and packaging change set.

   * - Single-key hash slices use trailing comma: Fields{"key",} (without trailing comma, Fields{"key"} returns the value, not a hash)
     - N/A
     - No new Qore module, QPP class, runtime method, DataProvider registration or Qore test file in this documentation, build and packaging change set.

   * - Typed data type classes exist for request and response types — inherit HashDataType, have const Fields hash, call addQoreFields(Fields) in constructor, export public constant at bottom (e.g., public const MyDataType = new MyDataType();)
     - N/A
     - No new Qore module, QPP class, runtime method, DataProvider registration or Qore test file in this documentation, build and packaging change set.

   * - Request/input types use public Fields (enables ClassName::Fields in action registration)
     - N/A
     - No new Qore module, QPP class, runtime method, DataProvider registration or Qore test file in this documentation, build and packaging change set.

   * - Response/output types use private Fields
     - N/A
     - No new Qore module, QPP class, runtime method, DataProvider registration or Qore test file in this documentation, build and packaging change set.

   * - Each field in data types has display_name, type, and desc (markdown-formatted)
     - N/A
     - No new Qore module, QPP class, runtime method, DataProvider registration or Qore test file in this documentation, build and packaging change set.

   * - Input fields have example_value where useful (string fields, endpoint URIs, SQL queries, etc.)
     - N/A
     - No new Qore module, QPP class, runtime method, DataProvider registration or Qore test file in this documentation, build and packaging change set.

   * - Fields with finite allowed values use allowed_values with AllowedValueInfo containing both value and display_name (Title Case, human-readable) — never bare values, never described only in text
     - N/A
     - No new Qore module, QPP class, runtime method, DataProvider registration or Qore test file in this documentation, build and packaging change set.

   * - Password/secret fields have "sensitive": True
     - N/A
     - No new Qore module, QPP class, runtime method, DataProvider registration or Qore test file in this documentation, build and packaging change set.

   * - groups uses AppGroup enum values from qlib/DataProvider/AppGroup.qc
     - N/A
     - No new Qore module, QPP class, runtime method, DataProvider registration or Qore test file in this documentation, build and packaging change set.

   * - App logo stored as separate file, loaded at module level in Priv namespace
     - N/A
     - No new Qore module, QPP class, runtime method, DataProvider registration or Qore test file in this documentation, build and packaging change set.

   * - App desc uses markdown: bullet list of capabilities, links to project website, business-language explanation of value
     - N/A
     - No new Qore module, QPP class, runtime method, DataProvider registration or Qore test file in this documentation, build and packaging change set.

   * - display_name is user-friendly ("Apache Avro" not "avro")
     - N/A
     - No new Qore module, QPP class, runtime method, DataProvider registration or Qore test file in this documentation, build and packaging change set.

   * - short_desc is plain text, under 80 chars, single sentence — no markdown
     - N/A
     - No new Qore module, QPP class, runtime method, DataProvider registration or Qore test file in this documentation, build and packaging change set.

   * - desc uses markdown: backticks for code/field refs ( field_name ,  True ,  pdf ), \n\n for paragraphs, -  bullet lists for enumerations, bold for caveats
     - N/A
     - No new Qore module, QPP class, runtime method, DataProvider registration or Qore test file in this documentation, build and packaging change set.

   * - Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use"
     - N/A
     - No new Qore module, QPP class, runtime method, DataProvider registration or Qore test file in this documentation, build and packaging change set.

   * - No bare True/False/NOTHING — must be backtick-wrapped in desc
     - N/A
     - No new Qore module, QPP class, runtime method, DataProvider registration or Qore test file in this documentation, build and packaging change set.

   * - No bare field/option names in prose — must use backticks
     - N/A
     - No new Qore module, QPP class, runtime method, DataProvider registration or Qore test file in this documentation, build and packaging change set.

   * - Long descriptions (>500 chars) use bold section headers and bullet lists
     - N/A
     - No new Qore module, QPP class, runtime method, DataProvider registration or Qore test file in this documentation, build and packaging change set.

   * - Factory registration in Qore repo: every factory name registered in qlib/DataProvider/DataProvider.qc → FactoryMap (without this, module loads but doesn't appear in Qorus apps)
     - N/A
     - No new Qore module, QPP class, runtime method, DataProvider registration or Qore test file in this documentation, build and packaging change set.

   * - getRecordTypeImpl() signature: must be private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options) — NOT returning *AbstractDataProviderType
     - N/A
     - No new Qore module, QPP class, runtime method, DataProvider registration or Qore test file in this documentation, build and packaging change set.

   * - Dependency JARs committed (for JNI modules): JAR files in qlib/*/jar/ may be gitignored — use git add -f to ensure they're tracked, otherwise CI compilation fails
     - N/A
     - No new Qore module, QPP class, runtime method, DataProvider registration or Qore test file in this documentation, build and packaging change set.

   * - JAR install rules in CMakeLists.txt for all dependency JARs
     - N/A
     - No new Qore module, QPP class, runtime method, DataProvider registration or Qore test file in this documentation, build and packaging change set.

   * - No workarounds: No TODOs, FIXMEs, stubs, or partially-implemented features
     - Pass
     - OBS failures were traced to declared build prerequisites; ncurses requires the library referenced by its compiled code. No tests disabled or new suppressions added.

   * - Exception safety: C++ uses ReferenceHolder for Qore allocations, std::unique_ptr for C++ allocations, *xsink checked after every fallible operation
     - Pass
     - ONNX fixture uses stack-owned Ort::Env and RAII session values, with a top-level exception handler. Uninstall stops on missing manifests, directories and removal failures.

   * - Thread safety: All mutable shared state protected by std::lock_guard<std::mutex> or documented as immutable-after-construction
     - Pass
     - No runtime concurrency changes. ONNX baseline creates one environment in a single test process; approved upstream cpuinfo exception remains documented.

   * - Type safety: Strongly-typed code<return(args)> instead of untyped code; static_cast instead of C casts; typed hashdecls for results; enums where appropriate
     - Pass
     - No API types changed; ONNX argument handling uses std::string and its existing typed API.

   * - Performance: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply
     - Pass
     - Documentation-only Qore edits preserve executable tokens. Test helpers process files and manifests linearly.

   * - Error handling: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable
     - Pass
     - Uninstall tests cover missing manifests, directories, dangling symlinks, spaces, DESTDIR and repeated removal. ONNX inference retains invalid-name and missing-model tests.

   * - Documentation: Doxygen @param, @return, @throw on all public methods; @par Example with realistic business scenarios; @note for important caveats
     - Pass
     - Widget comments now belong to classes; public pages, cross-module links and helper examples have three HTML regression checks. Release notes and RPM build/install examples updated.

   * - QPP flags: [flags=CONSTANT] on methods that never throw; [flags=RET_VALUE_ONLY] on methods that throw but have no side effects
     - N/A
     - No new Qore module, QPP class, runtime method, DataProvider registration or Qore test file in this documentation, build and packaging change set.

   * - Security: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code
     - Pass
     - No credentials added. Uninstall invokes CMake without a shell and refuses directories; dependency downloads remain pinned and checksum verified.

   * - Correctness: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features)
     - Pass
     - ncurses: 372 cases/1585 assertions and three HTML tests; Kalman: 34 cases/190 assertions and three uninstall tests; 26 Qore RPM helper tests per target; 63 packaging tests; ONNX CMake/pkg-config and Valgrind on EL/Leap.

Additional verification
-----------------------

The source-bundle validator passes 71 tests locally and in GitLab pipeline 58328.
The ZIP upload was repaired and all remote source checksums were verified.
Five OpenSSL header/API configurations and the actual EL10 empty engine header
compile successfully. Qore's 61 CMake tests pass; the 42 crypto cases (635
assertions) pass under Valgrind with no lost bytes or memory errors. PCRE2 JIT
stays enabled with upstream's supported Valgrind instrumentation; the initial
uninstrumented JIT trace is retained and is not treated as a Qore memory defect.

The BSON alias annotation changes no layout or ABI. Existing static assertions
remain active. GCC 13 with the OBS optimization/LTO flags passes all enabled
MongoDB tests: 1290 run, 1743 upstream live-service skips. The Debug BSON suite
passes 439 cases under Valgrind (two upstream skips), and an independently
compiled installed shared-SDK consumer reports zero memory errors or lost bytes.
Three fixture-publication tests cover complete atomic writes and preservation
of the prior result on write/rename errors. No additional filesystem or network
operations are introduced into Qore runtime code, and the cleanup guard adds no
allocation, shared state, loops, blocking operations or public API.

Process packaging passes the 57-case suite with both system and bundled Boost
headers, strict documentation, all three target spec parses, RPM lint with no
errors, and an installed minimal-runtime run. Its native source changes are
build/documentation changes only. The committed source retains patched private
Boost.Process; no unrelated user files are included in the archive.

AMQP source build/documentation changes 467a381 pass two HTML tests, strict final
Doxygen passes, 72 offline cases (195 assertions) and 612 translations. Two
broker-dependent suites are explicitly deferred to connected qualification.
Its RPM and installed checks are tracked separately while packaging is prepared.
