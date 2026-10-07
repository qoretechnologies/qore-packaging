# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json,subprocess,os,importlib.util,shlex
w=Path('/fixture');src=w/'node-v24.18.1'
loader=importlib.util.spec_from_file_location('flags','/build-flags.py');flags=importlib.util.module_from_spec(loader);loader.loader.exec_module(flags)
def macro(name):return subprocess.check_output(['rpm','--eval',name],text=True).strip()
env=flags.build_environment(macro('%{optflags}'),macro('%{?build_ldflags}'))
(w/'environment.json').write_text(json.dumps(env,indent=2)+'\n')
cmd=['python3','configure',*shlex.split(env['NODE_LTO_OPTION']),'--shared','--prefix=/usr','--libdir=lib64','--without-npm','--without-corepack','--shared-openssl','--shared-zlib','--shared-cares','--shared-nghttp2','--shared-brotli','--shared-zstd','--with-intl=system-icu','--openssl-use-def-ca-store']
r=subprocess.run(cmd,cwd=src,env={**os.environ,**env},capture_output=True,text=True);(w/'configure.log').write_text(r.stdout+r.stderr);assert r.returncode==0,r.stderr
# Inspect actual generated compile commands for both the assembly-containing
# V8 target and an ordinary Node object; neither compiles the full runtime.
commands={}
for name in ['v8_base_without_compiler/deps/v8/src/heap/base/asm/x64/push_registers_asm.o','libnode/src/node.o']:
 target=str(src/'out/Release/obj.target'/name)
 r=subprocess.run(['make','-n','-C',str(src/'out'),'BUILDTYPE=Release',target],env={**os.environ,**env},capture_output=True,text=True)
 (w/(name.split('/')[0]+'-dry-run.log')).write_text(r.stdout+r.stderr);assert r.returncode==0,r.stderr
 lines=[line for line in r.stdout.splitlines() if line.startswith('g++ -o '+target+' ')]
 assert len(lines)==1,(name,lines)
 tokens=shlex.split(lines[0]);lto=[x for x in tokens if x in ('-flto','-fno-lto') or x.startswith('-flto=')]
 assert lto,(name,lines)
 assert (lto[-1]=='-fno-lto') == name.startswith('v8_base_without_compiler/'),(name,lto)
 for flag in ['-D_FORTIFY_SOURCE=3','-fstack-protector-strong','-fstack-clash-protection','-Werror=return-type','-Wno-error=return-type','-g']:assert flag in tokens,(name,flag)
 commands[name]={'command':tokens,'lto_order':lto}
(w/'generated-commands.json').write_text(json.dumps(commands,indent=2)+'\n')
print('Native assembly target and LTO-enabled Node target generated with all distribution hardening flags')
