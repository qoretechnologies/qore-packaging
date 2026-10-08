# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import difflib, hashlib, json, subprocess
root = Path.cwd()
output = root / 'results/node-obs-fixtures-20261008'
output.mkdir()
build = root / 'results/leap-nodejs24-canonical-final-20261007'
source = build / 'rpmbuild/BUILD/nodejs24-libnode-24.18.1-build/node-v24.18.1'
image = json.loads((build / 'build.json').read_text())['image']
url = '/source/openSUSE:Factory/netcfg/hosts?rev=89c9098512a0677f528d0686f588b96a'
hosts = subprocess.check_output(['osc','--setopt','http_retries=1','-A','https://api.opensuse.org','api',url],text=True)
(output / 'netcfg-hosts').write_text(hosts)
original = (source / 'test/parallel/test-process-euid-egid.js').read_text()
old = "  }, /^Error: (?:EPERM, .+|User identifier does not exist: nobody)$/);"
new = """  }, {
    code: /^(?:EPERM|ERR_UNKNOWN_CREDENTIAL)$/,
    message: /^(?:EPERM, .+|User identifier does not exist: nobody)$/
  });"""
assert original.count(old) == 1
fixed = '// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT\n' + original.replace(old,new)
(output / 'original.js').write_text(original)
(output / 'fixed.js').write_text(fixed)
patch = ''.join(difflib.unified_diff(original.splitlines(True),fixed.splitlines(True),fromfile='a/test/parallel/test-process-euid-egid.js',tofile='b/test/parallel/test-process-euid-egid.js'))
(output / 'nodejs24-credential-test-error.patch').write_text('# Copyright 2026 Qore Technologies, s.r.o.; MIT.\n# Match the structured error independently of Error.toString formatting.\n'+patch)
tests=['parallel/test-http2-invalid-last-stream-id','parallel/test-http2-premature-close','parallel/test-net-socket-connect-without-cb','parallel/test-tcp-wrap-listen','parallel/test-process-euid-egid','report/test-report-exclude-network']
results=[]
for name,has_ipv6,nobody,patched in [('original-minimal',False,False,False),('original-netcfg',True,False,False),('original-complete',True,True,False),('fixed-missing-user',True,False,True),('fixed-existing-user',True,True,True)]:
    script='''from pathlib import Path
import os
hosts = Path('/control/netcfg-hosts').read_text() if HAS_IPV6 else '127.0.0.1 localhost\\n'
Path('/etc/hosts').write_text('127.0.0.1 obs-fixture\\n' + hosts)
if not NOBODY:
    for filename in ['/etc/passwd','/etc/group']:
        p = Path(filename)
        p.write_text(''.join(line for line in p.read_text().splitlines(True) if not line.startswith('nobody:')))
print('HOSTS:', Path('/etc/hosts').read_text(), flush=True)
print('NOBODY:', [line for line in Path('/etc/passwd').read_text().splitlines() if line.startswith('nobody:')], flush=True)
os.execvp('setpriv', ['setpriv','--reuid=1019','--regid=100','--clear-groups','python3','tools/test.py','-j','2','-p','tap','--mode=release','--flaky-tests=run'] + TESTS)
'''.replace('HAS_IPV6',repr(has_ipv6)).replace('NOBODY',repr(nobody)).replace('TESTS',repr(tests))
    # All account and hosts changes are confined to the throwaway container.
    cmd=['docker','run','--rm','--init','--network','none','-v',str(source)+':/source','-v',str(output)+':/control:ro','-v',str(output/('fixed.js' if patched else 'original.js'))+':/source/test/parallel/test-process-euid-egid.js:ro','-w','/source','-e','LD_LIBRARY_PATH=/source/out/Release',image,'python3','-c',script]
    with (output/(name+'.log')).open('x') as log:
        result=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
    results.append({'name':name,'exit_code':result.returncode,'ipv6_hosts':has_ipv6,'nobody_account':nobody,'patched_assertion':patched,'command':cmd})
    (output/'status.json').write_text(json.dumps(results,indent=2)+'\n')
    print(name,result.returncode,flush=True)
