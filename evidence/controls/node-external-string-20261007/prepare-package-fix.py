# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import difflib,json,shutil
base=Path('work/node-obs-diagnostic-20261006/node-v24.18.1/deps/v8/src/api/api.cc');s=base.read_text();old='''      if (!is_one_byte) {
        expected = reinterpret_cast<const ExternalStringResource*>(resource);
      }''';new='''      expected = is_one_byte
                     ? nullptr
                     : reinterpret_cast<const ExternalStringResource*>(resource);''';assert s.count(old)==1
patch=Path('dependencies/nodejs24-external-string-resource.patch');patch.write_text('# Copyright 2026 Qore Technologies, s.r.o.; BSD-3-Clause.\n# Match the two-byte getter when a forwarded external resource is one-byte.\n'+''.join(difflib.unified_diff(s.splitlines(True),s.replace(old,new).splitlines(True),fromfile='a/deps/v8/src/api/api.cc',tofile='b/deps/v8/src/api/api.cc')))
test=Path('dependencies/nodejs24-external-string-resource-test.cc');shutil.copy2('work/node-external-string-native-20261007/regression7.cc',test)
p=Path('dependencies/nodejs24-libnode.spec');s=p.read_text();assert patch.name not in s
s=s.replace('Source20: nodejs24-timezone-index-test.py\n','Source20: nodejs24-timezone-index-test.py\nSource21: '+test.name+'\n')
s=s.replace('Patch16: nodejs24-timezone-index.patch\n','Patch16: nodejs24-timezone-index.patch\nPatch17: '+patch.name+'\n')
s=s.replace('%check\n','''%check
# Verify actual external resources and their forwarded one-byte representation.
g++ %{optflags} -std=c++20 -Wall -Werror=return-type -Ideps/v8/include \\
    %{SOURCE21} -Lout/Release -Wl,-rpath,"$PWD/out/Release" \\
    -lnode -licuuc -lcrypto -ldl -pthread -o out/external-string-resource-control
out/external-string-resource-control ordinary
out/external-string-resource-control shared
python3 - <<'EXTERNALCHECK'
import resource, subprocess
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
for mode in ('ordinary', 'shared'):
    result = subprocess.run(['out/external-string-resource-control', mode, 'negative'],
                            capture_output=True, text=True)
    if result.returncode >= 0 or 'expected == value' not in result.stderr:
        raise AssertionError((mode, result.returncode, result.stderr))
    print('Incorrect external string resource rejected:', mode)
EXTERNALCHECK
''',1)
s=s.replace('%changelog\n','''%changelog
* Wed Oct 07 2026 David Nichols <david@qore.org> - 24.18.1-1.qore
- Initialize the V8 verifier result for forwarded one-byte external resources.
- Test both resource encodings, normal/shared storage and wrong-resource rejection.

''',1);p.write_text(s)
p=Path('dependencies/sources.json');d=json.loads(p.read_text());n=d['nodejs24-libnode'];key=next(k for k,v in n.items() if isinstance(v,list) and 'nodejs24-timezone-index.patch' in v);n[key].extend([patch.name,test.name]);p.write_text(json.dumps(d,indent=2)+'\n')
p=Path('dependencies/nodejs24-libnode.rst');s=p.read_text();anchor="Leap's resolver checker mistakes";idx=s.index(anchor);s=s[:idx]+'''The next candidate also fixes a missing pointer assignment in V8's external
string verifier. For a forwarded one-byte resource, the two-byte getter returns
null; the verifier now agrees with that result. The packaged baseline aborts
for this valid input. Native controls cover both encodings, ordinary and shared
storage, complete resource disposal and deliberate wrong-resource rejection.
Focused qualification and the full updated RPM remain required before this
additional patch can be published.

'''+s[idx:];p.write_text(s)
print('Prepared external-string fix and native package regression; qualification pending.')
