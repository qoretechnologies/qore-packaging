import os, pathlib, re, shlex, subprocess
out=pathlib.Path('/work')
expanded=subprocess.check_output(['rpmspec','-P','/sources/qore.spec'],text=True)
match=re.search(r'^cmake -S \. -B build .*?(?=\ncmake --build)',expanded,re.M|re.S)
assert match, 'recipe configure command missing'
args=shlex.split(match.group().replace('\\\n',' '));assert '-DQORE_REQUIRE_SYSTEM_DEPENDENCIES=ON' in args
assert not any(a.startswith('-DFETCHCONTENT_') for a in args)
args[args.index('-B')+1]='/work/build'
normal=subprocess.run(args,cwd='/source',capture_output=True,text=True)
(out/'configure.log').write_text(normal.stdout+normal.stderr)
assert normal.returncode==0,normal.stderr
assert 'CMake Warning' not in normal.stdout+normal.stderr,normal.stderr
assert (out/'build/include/qore/intern/git-revision.h').read_text()=='#define BUILD "unknown"\n'
print('PASS: real recipe configure, no CMake warning, unresolved candidate revision is explicit',flush=True)
# Hide only c-ares through the normal discovery API; other package probes are forwarded.
wrapper=out/'pkg-config-without-cares'
wrapper.write_text('#!/bin/sh\nfor argument in "$@"; do\n    case "$argument" in *libcares*) exit 1 ;; esac\ndone\nexec /usr/bin/pkg-config "$@"\n')
wrapper.chmod(0o755)
negative=list(args);negative[negative.index('-B')+1]='/work/negative/build';negative+=['-DPKG_CONFIG_EXECUTABLE='+str(wrapper), '-DCARES_INCLUDE_DIR=/nonexistent/cares', '-DCARES_LIBRARY=/nonexistent/libcares.so']
missing=subprocess.run(negative,cwd='/source',capture_output=True,text=True)
(out/'missing-cares.log').write_text(missing.stdout+missing.stderr)
assert missing.returncode!=0
assert 'c-ares' in missing.stderr and 'system' in missing.stderr.lower(),missing.stderr
assert not list((out/'negative/build').glob('_deps/*-src'))
assert not re.search(r'(Downloading|Cloning|Performing download)',missing.stdout+missing.stderr)
print('PASS: missing required c-ares fails before any fallback download',flush=True)
