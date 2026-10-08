# Copyright 2026 Qore Technologies, s.r.o.
function(add_subdirectory directory)
  message(STATUS "SELECTED:${directory}")
endfunction()
set(ENABLE_OPENSSL TRUE)
set(HAVE_CRYPTO TRUE)
set(HAVE_LIBRESSL TRUE)
include("/home/david/src/qore/git/qore-packaging/evidence/controls/ngtcp2-backend-diagnostics-20261008/crypto-CMakeLists.txt")
