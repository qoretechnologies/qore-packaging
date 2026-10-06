# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import hashlib,json,shutil,subprocess
root=Path.cwd();src=root/'work/node-obs-diagnostic-20261006/node-v24.18.1';out=root/'work/node-gc-transition-controls2-20261006';out.mkdir();extracts=[]
def take(path,start,end,after=None):
 s=(src/path).read_text();a=s.index(start,s.index(after) if after else 0);b=s.index(end,a);body=s[a:b].rstrip();extracts.append({'file':path,'line':s[:a].count('\n')+1,'body':body,'sha256':hashlib.sha256(body.encode()).hexdigest()});return body
def enum(path,start,after=None):return take(path,start,';',after)+';'
sweeper='deps/v8/src/heap/array-buffer-sweeper';gc='deps/v8/src/heap/gc-tracer';intl='deps/v8/src/objects/intl-objects'
sweepenum=enum(sweeper+'.h','  enum class SweepingType');sweepbody=take(sweeper+'.cc','  CHECK(!state_.IsDone());','\n}', 'void ArrayBufferSweeper::SweepingState::SweepingJob::Sweep(')
gcenum=enum('deps/v8/src/common/globals.h','enum class GarbageCollector');markenum=enum(gc+'.h','  enum class MarkingType');eventenum=enum(gc+'.h','    enum class Type','  class Event')
gcbody=take(gc+'.cc','  Event::Type type;','\n\n  DCHECK_IMPLIES','void GCTracer::StartCycle')
trenum=enum(intl+'.h','  enum class Transition');trbody=take(intl+'.cc','  icu::TimeZoneTransition icu_transition;','\n  if (!has_transition)','DirectHandle<Object> Intl::GetTimeZoneOffsetTransitionNanoseconds')
header='''// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
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
'''+sweepenum+'\n'+gcenum+'\n'+markenum+'\nstruct Event {\n'+eventenum+'\n};\nstruct Intl {\n'+trenum+'\n};\n'
header+='''struct State { bool done=false; bool IsDone() const { return done; } void SetDone() { done=true; } };
struct JobDelegate { unsigned allowance; };
struct SweepControl {
 SweepingType type_; State state_; unsigned young,old,preempted=0;
 unsigned young_calls=0,full_calls=0;
 bool SweepYoung(JobDelegate* d) { ++young_calls; auto n=std::min(young,d->allowance);young-=n;d->allowance-=n;return young==0; }
 bool SweepFull(JobDelegate* d) { ++full_calls; if (!SweepYoung(d)) { return false; } auto n=std::min(old,d->allowance);old-=n;d->allowance-=n;return old==0; }
 __attribute__((noinline)) void Sweep(JobDelegate* delegate) {
'''+sweepbody+'\n}\n};\n'
functions='__attribute__((noinline)) Event::Type EventType(GarbageCollector collector, MarkingType marking) {\n'+gcbody+'\nreturn type;\n}\n'
functions+='''enum class Direction { kPast, kFuture };
// Adapter accepts a signed nanosecond count directly; ICU integration is real.
int64_t ApproximateMillisecondEpoch(void*, int64_t ns, Direction direction=Direction::kPast) {
 int64_t ms=ns/1000000; const auto rem=ns%1000000;
 if (direction==Direction::kPast && rem<0) { --ms; }
 if (direction==Direction::kFuture && rem>0) { ++ms; }
 return ms;
}
__attribute__((noinline)) std::optional<double> Transition(const icu::BasicTimeZone* basic_time_zone, int64_t nanosecond_epoch, Intl::Transition transition) {
 void* isolate=nullptr;
'''+trbody+'\nif (!has_transition) { return {}; }\nreturn icu_transition.getTime();\n}\n'
tests=r'''
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
'''
(out/'control.cc').write_text(header+functions+tests);(out/'source-extracts.json').write_text(json.dumps(extracts,indent=2)+'\n');shutil.copy2(src/'deps/v8/LICENSE',out/'V8-LICENSE')
runner=r'''# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json,shlex,subprocess
out=Path('/work');results=[]
flags=shlex.split(subprocess.check_output(['pkg-config','--cflags','--libs','icu-i18n','icu-uc'],text=True))
for mode in ('release','debug'):
 commands=[['g++','-std=c++20','-O2','-g','-Wall','-Wextra']+(['-DDEBUG'] if mode=='debug' else [])+['/work/control.cc',*flags,'-o','/work/control-'+mode],['/work/control-'+mode],['valgrind','--error-exitcode=99','--leak-check=full','--errors-for-leak-kinds=all','--log-file=/work/'+mode+'-valgrind.log','/work/control-'+mode]]
 for name,command in zip(('compile','normal','memory'),commands):
  with (out/(mode+'-'+name+'.log')).open('w') as log:r=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
  results.append({'name':mode+'-'+name,'command':command,'exit_code':r.returncode});(out/'status.json').write_text(json.dumps(results,indent=2)+'\n');r.check_returncode()
'''
(out/'run.py').write_text(runner)
cmd=['docker','run','--rm','--init','--network','none','--user','1019:100','-v',str(out)+':/work','sha256:471fb347e0308caa05f79e41ca4813767c6a7a687f03cc823a78b2a8e81a3414','python3','-B','-W','error','/work/run.py'];(out/'command.json').write_text(json.dumps(cmd,indent=2)+'\n')
with (out/'run.log').open('x') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
