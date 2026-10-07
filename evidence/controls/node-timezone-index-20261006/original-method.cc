std::string Intl::TimeZoneIdFromIndex(int32_t index) {
  if (index == JSTemporalTimeZone::kUTCTimeZoneIndex) {
    return "UTC";
  }
  std::unique_ptr<icu::StringEnumeration> enumeration(
      icu::TimeZone::createEnumeration());
  int32_t curr = 0;
  const char* id;

  UErrorCode status = U_ZERO_ERROR;
  while (U_SUCCESS(status) && curr < index &&
         ((id = enumeration->next(nullptr, status)) != nullptr)) {
    CHECK(U_SUCCESS(status));
    curr++;
  }
  CHECK(U_SUCCESS(status));
  CHECK(id != nullptr);
  return id;
}
