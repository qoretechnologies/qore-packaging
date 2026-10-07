# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import hashlib
import json
import os
import re
import subprocess
import tempfile

root=Path.cwd(); repo=root/'work/checkouts/qore-documentation-sdk-20261006'
main=root.parent/'qore'; out=root/'results/core-date-backport-20261007'; out.mkdir()
commit='298fdb595c982b6c621cdabeed163198639dd696'
files=['lib/DateTime.cpp','include/qore/DateTime.h','include/qore/intern/qore_date_private.h',
       'examples/test/qore/vars/date_add.cpp','examples/test/qore/vars/date-add-native.qtest']
for name in files:
    assert (repo/name).read_bytes()==subprocess.check_output(['git','show',commit+':'+name],cwd=main),name
cmake=(repo/'CMakeLists.txt').read_text()
a=cmake.index('add_executable(qore-date-add-test ')
b=cmake.index('target_link_libraries(qore-date-add-test PRIVATE libqore)',a)
block=cmake[a:b]+ 'target_link_libraries(qore-date-add-test PRIVATE libqore)\n'
assert '<<<<<<<' not in cmake
# Exercise the exact target declaration using the qualified, identical date implementation.
# This focused check does not claim a rebuilt full RPM or unchanged unrelated core code.
with tempfile.TemporaryDirectory(prefix='qore date backport ') as temporary:
    source=Path(temporary); build=source/'build'; build.mkdir()
    (source/'examples').symlink_to(repo/'examples',target_is_directory=True)
    (source/'include').symlink_to(repo/'include',target_is_directory=True)
    (build/'include').symlink_to(main/'build/include',target_is_directory=True)
    (source/'CMakeLists.txt').write_text('cmake_minimum_required(VERSION 3.20)\nproject(DateBackport LANGUAGES CXX)\nset(CMAKE_CXX_STANDARD 20)\nadd_library(libqore SHARED IMPORTED)\nset_target_properties(libqore PROPERTIES IMPORTED_LOCATION "'+str(main/'build/libqore.so')+'")\n'+block)
    env=os.environ.copy();env['LD_LIBRARY_PATH']=str(main/'build');env['QORE_DATE_ADD_TEST']=str(build/'qore-date-add-test')
    env['QORE_BINARY']=str(main/'build/qore');env['QORE_MODULE_DIR_ONLY']='1'
    env['QORE_MODULE_DIR']=':'.join([str(repo/'qlib'),*(str(p) for p in (main/'build/modules').iterdir() if p.is_dir()),str(main.parent/'module-xml/build')])
    rows=[]
    commands=[('configure',['cmake','-S',str(source),'-B',str(build),'-DCMAKE_BUILD_TYPE=Release','-DCMAKE_INSTALL_PREFIX=/usr']),
              ('build',['cmake','--build',str(build),'--target','qore-date-add-test','-j2']),
              ('native',[str(build/'qore-date-add-test')]),
              ('qore',[str(main/'build/qore'),'-b','--enable-debug',str(repo/'examples/test/qore/vars/date-add-native.qtest')])]
    for name,command in commands:
        r=subprocess.run(command,cwd=repo,env=env,capture_output=True,text=True,timeout=180)
        text=r.stdout+r.stderr;(out/(name+'.log')).write_text(text)
        rows.append({'name':name,'command':command,'exit_code':r.returncode})
        assert r.returncode==0 and not re.search(r'(?i)warning:|error:|FAIL|Skipped:',text),text
        if name=='native':assert text=='PASS: 1836 DateTime addition cases\n'
        if name=='qore':assert 'Ran 2 test cases, 2 succeeded (29 assertions)' in text
(out/'status.json').write_text(json.dumps({'source_commit':commit,'identical_sources':files,'steps':rows,'limits':'Exact new target and identical date implementation verified; full RPM rebuild remains required.'},indent=2)+'\n')
print('PASS: backport source identity, CMake target, 1836 native cases and 2 Qore cases / 29 assertions')
