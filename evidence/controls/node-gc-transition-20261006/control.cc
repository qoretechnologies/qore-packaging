// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
// Unchanged V8 dispatch bodies; typed GC adapters and real ICU transitions.
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cmath>
#include <memory>
#include <optional>
#include <unicode/basictz.h>
#include <unicode/tztrans.h>
#include <unicode/timezone.h>
#include <unicode/uclean.h>
void require(bool v) { if (!v) { std::abort(); } }
#define CHECK(x) require(x)
#define TRACE_GC_NOTE(x) (++preempted)
  enum class SweepingType { kYoung, kFull };
enum class GarbageCollector { SCAVENGER, MARK_COMPACTOR, MINOR_MARK_SWEEPER };
  enum class MarkingType { kAtomic, kIncremental };
struct Event {
    enum class Type {
      SCAVENGER = 0,
      MARK_COMPACTOR = 1,
      INCREMENTAL_MARK_COMPACTOR = 2,
      MINOR_MARK_SWEEPER = 3,
      INCREMENTAL_MINOR_MARK_SWEEPER = 4,
      START = 5,
    };
};
struct Intl {
  enum class Transition { kNext, kPrevious };
};
struct State { bool done=false; bool IsDone() const { return done; } void SetDone() { done=true; } };
struct JobDelegate { unsigned allowance; };
struct SweepControl {
 SweepingType type_; State state_; unsigned young,old,preempted=0;
 unsigned young_calls=0,full_calls=0;
 bool SweepYoung(JobDelegate* d) { ++young_calls; auto n=std::min(young,d->allowance);young-=n;d->allowance-=n;return young==0; }
 bool SweepFull(JobDelegate* d) { ++full_calls; if (!SweepYoung(d)) { return false; } auto n=std::min(old,d->allowance);old-=n;d->allowance-=n;return old==0; }
 __attribute__((noinline)) void Sweep(JobDelegate* delegate) {
  CHECK(!state_.IsDone());
  bool is_finished;
  switch (type_) {
    case SweepingType::kYoung:
      is_finished = SweepYoung(delegate);
      break;
    case SweepingType::kFull:
      is_finished = SweepFull(delegate);
      break;
  }
  if (is_finished) {
    state_.SetDone();
  } else {
    TRACE_GC_NOTE("ArrayBufferSweeper Preempted");
  }
}
};
__attribute__((noinline)) Event::Type EventType(GarbageCollector collector, MarkingType marking) {
  Event::Type type;
  switch (collector) {
    case GarbageCollector::SCAVENGER:
      type = Event::Type::SCAVENGER;
      break;
    case GarbageCollector::MINOR_MARK_SWEEPER:
      type = marking == MarkingType::kIncremental
                 ? Event::Type::INCREMENTAL_MINOR_MARK_SWEEPER
                 : Event::Type::MINOR_MARK_SWEEPER;
      break;
    case GarbageCollector::MARK_COMPACTOR:
      type = marking == MarkingType::kIncremental
                 ? Event::Type::INCREMENTAL_MARK_COMPACTOR
                 : Event::Type::MARK_COMPACTOR;
      break;
  }
return type;
}
enum class Direction { kPast, kFuture };
// Adapter accepts a signed nanosecond count directly; ICU integration is real.
int64_t ApproximateMillisecondEpoch(void*, int64_t ns, Direction direction=Direction::kPast) {
 int64_t ms=ns/1000000; const auto rem=ns%1000000;
 if (direction==Direction::kPast && rem<0) { --ms; }
 if (direction==Direction::kFuture && rem>0) { ++ms; }
 return ms;
}
__attribute__((noinline)) std::optional<double> Transition(const icu::BasicTimeZone* basic_time_zone, int64_t nanosecond_epoch, Intl::Transition transition) {
 void* isolate=nullptr;
  icu::TimeZoneTransition icu_transition;
  UBool has_transition;
  switch (transition) {
    case Intl::Transition::kNext:
      has_transition = basic_time_zone->getNextTransition(
          ApproximateMillisecondEpoch(isolate, nanosecond_epoch), false,
          icu_transition);
      break;
    case Intl::Transition::kPrevious:
      has_transition = basic_time_zone->getPreviousTransition(
          ApproximateMillisecondEpoch(isolate, nanosecond_epoch,
                                      Direction::kFuture),
          false, icu_transition);
      break;
  }
if (!has_transition) { return {}; }
return icu_transition.getTime();
}

int main() {
 unsigned checks=0;
 for(unsigned repeat=0;repeat<1000;++repeat) {
  for(auto mode:{SweepingType::kYoung,SweepingType::kFull}) {
   for(unsigned young:{0,1,255,256,257,1024}) { for(unsigned old:{0,1,256,1024}) {
    for(unsigned budget:{0,1,255,256,2048}) {
     SweepControl c{mode,{},young,old}; JobDelegate delegate{budget}; c.Sweep(&delegate);
     const unsigned wanted=young+(mode==SweepingType::kFull?old:0),left=std::min(budget,wanted);
     require(c.state_.done==(budget>=wanted));require(c.preempted==unsigned(budget<wanted));
     require(c.young==young-std::min(young,budget));require(c.young+c.old==young+old-left);
     require(c.full_calls==unsigned(mode==SweepingType::kFull));require(c.young_calls==1);
     if(!c.state_.done) { JobDelegate finish{young+old};c.Sweep(&finish);require(c.state_.done);require(c.young==0);require(c.old==(mode==SweepingType::kFull?0:old)); }
     ++checks;
    }
   } }
  }
  const std::array collectors{GarbageCollector::SCAVENGER,GarbageCollector::MARK_COMPACTOR,GarbageCollector::MINOR_MARK_SWEEPER};
  const std::array atomic{Event::Type::SCAVENGER,Event::Type::MARK_COMPACTOR,Event::Type::MINOR_MARK_SWEEPER};
  const std::array incremental{Event::Type::SCAVENGER,Event::Type::INCREMENTAL_MARK_COMPACTOR,Event::Type::INCREMENTAL_MINOR_MARK_SWEEPER};
  for(unsigned i=0;i<collectors.size();++i) { require(EventType(collectors[i],MarkingType::kAtomic)==atomic[i]);require(EventType(collectors[i],MarkingType::kIncremental)==incremental[i]);checks+=2; }
 }
 // Real ICU transition boundaries, including no-DST zones and signed epochs.
 for(const char* name: {"Europe/Prague","America/New_York","Australia/Lord_Howe","Pacific/Apia","Asia/Kathmandu","UTC"}) {
  std::unique_ptr<icu::TimeZone> base(icu::TimeZone::createTimeZone(icu::UnicodeString(name)));
  const auto* zone=dynamic_cast<const icu::BasicTimeZone*>(base.get());require(zone!=nullptr);
  for(int64_t epoch:{INT64_C(-2208988800000000000),INT64_C(-1000001),INT64_C(-1),INT64_C(0),INT64_C(1),INT64_C(1000001),INT64_C(1711846800000000000),INT64_C(1792909200000000000),INT64_C(4102444800000000000)}) {
   for(auto mode:{Intl::Transition::kNext,Intl::Transition::kPrevious}) {
    icu::TimeZoneTransition oracle;const bool next=mode==Intl::Transition::kNext;
    const auto ms=next?std::floor(static_cast<long double>(epoch)/1000000):std::ceil(static_cast<long double>(epoch)/1000000);
    const bool has=next?zone->getNextTransition(ms,false,oracle):zone->getPreviousTransition(ms,false,oracle);
    for(unsigned repeat=0;repeat<100;++repeat) {
     const auto result=Transition(zone,epoch,mode);require(bool(result)==has);
     if(result) {
      require(*result==oracle.getTime());require(next?*result>ms:*result<ms);
      const int64_t boundary=static_cast<int64_t>(*result)*1000000;
      const auto at=Transition(zone,boundary,mode);
      require(!at || (next?*at>*result:*at<*result));
      const auto inside=Transition(zone,boundary+(next?-1:1),mode);
      require(inside && *inside==*result);
     }
     ++checks;
    }
   }
  }
 }
 u_cleanup();
 std::printf("PASS: %u sweep completion, GC event and real ICU transition checks\n",checks);
}
