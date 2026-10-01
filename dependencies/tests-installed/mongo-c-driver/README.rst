Installed MongoDB SDK check
==========================

Copyright 2026 Qore Technologies, s.r.o.

Install libbson2, libmongoc2, bson-devel and mongo-c-driver-devel from the tested
RPM build, then compile outside the source tree using the installed pkg-config
metadata::

    cc -Wall -Wextra -Werror main.c $(pkg-config --cflags --libs mongoc2) -o sdk-test
    ./sdk-test
    valgrind --error-exitcode=97 --leak-check=full \
      --errors-for-leak-kinds=definite,indirect,possible ./sdk-test

The consumer checks a BSON subdocument's static view and value, and constructs a
MongoDB client with URI options. It uses the installed shared libraries and
headers; it never opens a connection or needs a running database.
