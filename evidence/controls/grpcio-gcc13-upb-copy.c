// Copyright 2026 Qore Technologies, s.r.o.; Apache-2.0.
#include "google/protobuf/struct.upb.h"
#include "upb/message/copy.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define CHECK(expr) do { if (!(expr)) { fprintf(stderr, "line %d: %s\n", __LINE__, #expr); abort(); } } while (0)
struct Wire { const char* bytes; size_t size; };
#define WIRE(s) {s, sizeof(s)-1}
int main(void) {
  const struct Wire inputs[] = {
    WIRE(""), WIRE("\x08\x00"), WIRE("\x11\x00\x00\x00\x00\x00\x00\xf8\x3f"),
    WIRE("\x1a\x03" "abc"), WIRE("\x20\x01"), WIRE("\x2a\x00"), WIRE("\x32\x00"),
    WIRE("\x32\x04\x0a\x02\x20\x01"),
    WIRE("\x2a\x09\x0a\x07\x0a\x01" "x" "\x12\x02\x20\x01"),
    WIRE("\x32\x09\x0a\x07\x32\x05\x0a\x03\x1a\x01" "x"),
  };
  size_t count = 0;
  for (int round = 0; round < 10000; ++round) {
    for (size_t n = 0; n < sizeof(inputs)/sizeof(inputs[0]); ++n) {
      upb_Arena* source = upb_Arena_New();
      upb_Arena* destination = upb_Arena_New();
      CHECK(source && destination);
      google_protobuf_Value* original = google_protobuf_Value_parse(inputs[n].bytes, inputs[n].size, source);
      CHECK(original);
      google_protobuf_Value* cloned = (google_protobuf_Value*)upb_Message_DeepClone(
          (const upb_Message*)original, &google__protobuf__Value_msg_init, destination);
      CHECK(cloned && cloned != original);
      upb_Arena_Free(source);
      size_t size = 0;
      const char* wire = google_protobuf_Value_serialize(cloned, destination, &size);
      CHECK(wire && size == inputs[n].size);
      CHECK(memcmp(wire, inputs[n].bytes, size) == 0);
      upb_Arena_Free(destination);
      ++count;
    }
  }
  const struct Wire invalid[] = {WIRE("\x2a\xff"), WIRE("\x32\x04\x0a")};
  for (size_t n = 0; n < sizeof(invalid)/sizeof(invalid[0]); ++n) {
    upb_Arena* arena = upb_Arena_New(); CHECK(arena);
    CHECK(!google_protobuf_Value_parse(invalid[n].bytes, invalid[n].size, arena));
    upb_Arena_Free(arena);
  }
  printf("%zu deep clones preserve scalar, oneof, nested-message, map and repeated fields after freeing the source arena; 2 malformed wires rejected\n", count);
  return 0;
}
