# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json, os, subprocess

root = Path('/control')
out = Path('/output')
epoch = int((root/'pgsql-timestamp').read_text().strip())
environment = {key:value for key,value in os.environ.items()
               if key not in ('SOURCE_DATE_EPOCH', 'SOURCE_DATE_EPOCH_MTIME')}
results = []
for name, extra, expected, warning_count in [
    ('no-changes', 'BUILD_RELEASE=2.1\n', 'unset unset\n', 2),
    ('missing-release', f'BUILD_CHANGELOG_TIMESTAMP={epoch}\n', 'unset unset\n', 1),
    ('complete', f'BUILD_RELEASE=2.1\nBUILD_CHANGELOG_TIMESTAMP={epoch}\n', f'{epoch} {epoch+1}\n', 0),
    ('invalid-counter', f'BUILD_RELEASE=2.0\nBUILD_CHANGELOG_TIMESTAMP={epoch}\n', f'{epoch} {epoch}\n', 1),
]:
    Path('/.buildenv').write_text('TOPDIR=/nonexistent\n'+extra)
    command = ['bash','--noprofile','--norc','-c',
               '. /control/suse-buildsystem.sh; printf "%s %s\\n" "${SOURCE_DATE_EPOCH-unset}" "${SOURCE_DATE_EPOCH_MTIME-unset}"']
    result = subprocess.run(command, capture_output=True, text=True, env=environment)
    (out/(name+'.stdout')).write_text(result.stdout)
    (out/(name+'.stderr')).write_text(result.stderr)
    assert result.returncode == 0 and result.stdout == expected, (name,result)
    assert result.stderr.count('WARNING') == warning_count, (name,result.stderr)
    if name == 'complete':
        assert result.stderr == f'setting SOURCE_DATE_EPOCH_MTIME to {epoch+1}\n'
    results.append({'name':name,'environment':extra,'exit_code':result.returncode,
                    'expected_warning_count':warning_count,'epoch_result':result.stdout.strip()})
(out/'checks.json').write_text(json.dumps(results,indent=2)+'\n')
print('Four unchanged Leap profile controls pass; complete metadata has no warnings')
