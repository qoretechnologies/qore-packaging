Installing Qore from an RPM repository
=====================================

Copyright 2026 Qore Technologies, s.r.o.

Publication status
------------------

The testing project is ``home:davidnichols:qore:testing``. Publication remains
disabled while final module, upgrade and repository checks are completed.
There is no public installation endpoint qualified by this document yet.

The commands below have been exercised with core release 21 in fresh native
x86_64 and aarch64 containers on Fedora 44, AlmaLinux 10 and openSUSE Leap 16.0.
Their repositories contain
the exact OBS-signed RPMs recorded in
``evidence/core21-upgrade-baseline-20261008.json``. Local test metadata is signed
with a separate, temporary qualification key. These checks establish package
discovery, dependency resolution and installed behavior; they do not establish
publication or trust in a future production signing key.

Runtime and development packages
--------------------------------

After configuring the reviewed repository and verifying its published signing
key, install the runtime by package name. On Fedora and AlmaLinux::

    sudo dnf --setopt=install_weak_deps=False install qore

On openSUSE Leap::

    sudo zypper install --allow-vendor-change --no-recommends qore

Leap's runtime requires the Qore repository's newer ``libnghttp2-14``. The
qualified transaction upgrades that package from SUSE's 1.64.0 build to the
project's 1.70.0 build. Review the proposed vendor change before accepting the
transaction. The command permits this transaction's vendor changes; it does
not change the system-wide solver policy. The option is documented in the
`official zypper manual <https://manpages.opensuse.org/Tumbleweed/zypper/zypper.8.en.html>`_.

AlmaLinux qualification enables EPEL and CRB in addition to the distribution's
base repositories. Repository definitions must match the operating system
release and architecture.

The runtime includes the standard library and ML with ONNX Runtime support.
Qualification executes ONNX inference and the ONNX session pool before any
compiler or Qore development package is installed. A runtime-only installation
with the commands above does not pull in ``qore-devel``, ``gcc`` or ``gcc-c++``.

To add the SDK and development tools on Fedora or AlmaLinux::

    sudo dnf --setopt=install_weak_deps=False install qore-devel qore-debug-tools qore-misc-tools qore-rpm-macros cmake

On openSUSE Leap::

    sudo zypper install --allow-vendor-change --no-recommends qore-devel qore-debug-tools qore-misc-tools qore-rpm-macros cmake

The SDK checks compile and run a C++ embedding consumer, use CMake to discover
Qore, compile AOT programs and modules, and exercise compiler metadata, tools
and remote debuggers. The runtime checks run again after SDK installation.

Signature and transaction checks
--------------------------------

Repository definitions keep both metadata and package signature verification
enabled. The qualification fixture pins both public-key files by SHA-256,
checks each RPM's checksum and signature, and requests packages by name through
DNF or Zypper. It verifies that the solver selects the recorded core builds
and that ``rpm -V`` succeeds after both installation phases.

Each package manager must reject a deliberately modified ``repomd.xml`` with
its original signature before it refreshes and installs from the valid
repository. Six prepared repository sets, covering both x86_64 and aarch64,
also pass direct metadata signature and tamper checks. The reusable runner
passes package-manager discovery, signature rejection and runtime/SDK checks
on all six native distribution/architecture combinations. ARM jobs run on
``linux/arm64`` runners and verify the selected RPM identities independently.

The reusable removal/reinstallation runner passes on all six native targets.
These checks prove that dependency protection
rejects removal of the Qore library while consumers remain installed, that
removing the core packages removes their recorded payloads, and that
reinstallation restores the package inventory and runtime/SDK behavior. These
are same-version checks. Cross-version upgrades and the complete module
combination still require their own qualification before publication.

Evidence:

* ``evidence/core21-solver-20261008.json``: exact package-name transactions,
  signing controls, selected versions and installed test logs.
* ``evidence/repository-runner-20261008.json`` and
  ``evidence/repository-runner-arm-20261008.json``: the reusable runner's unit
  tests, x86_64 qualification and three native ARM jobs.
* ``evidence/core21-removal-20261008.json``: initial dependency rejection, removal
  and reinstallation controls.
* ``evidence/core-lifecycle-20261008.json`` and
  ``evidence/core-lifecycle-arm-20261008.json``: reusable lifecycle runner, 245
  unit tests and all six native removal/reinstall/runtime/SDK sequences.
* ``evidence/core21-upgrade-baseline-20261008.json``: frozen signed packages and
  immutable test fixtures for subsequent upgrade checks.
