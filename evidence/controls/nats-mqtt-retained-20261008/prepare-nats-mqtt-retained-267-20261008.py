# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json,subprocess
root=Path.cwd()
prior=root/'work/nats-mqtt-retained-266-20261008/control.go'
out=root/'work/nats-mqtt-retained-267-20261008'
out.mkdir()
s=prior.read_text()
a='''	var valid mqttRetainedMsg
	require_NoError(t, json.Unmarshal(stored.Data, &valid))
	require_Equal(t, valid.Subject, "foo.ok")
	require_Equal(t, string(valid.Msg), "ok")'''
assert s.count(a)==1
s=s.replace(a,'''	// Current MQTT records store the raw payload; only the deliberately
	// injected legacy invalid record above is a JSON mqttRetainedMsg.
	require_Equal(t, stored.Subject, mqttRetainedMsgsStreamSubject+"foo.ok")
	require_Equal(t, string(stored.Data), "ok")''')
(out/'control.go').write_text(s)
subprocess.run(['gofmt','-w',str(out/'control.go')],check=True)
base=json.loads((root/'work/nats-mqtt-retained-266.json').read_text())
base['cases']=[c for c in base['cases'] if c['name'].endswith('-control')]
for c in base['cases']:
 c['name']=c['name'].replace('266','267')
 c['overlays']={str((out/'control.go').relative_to(root)):'server/mqtt_test.go'}
(root/'work/nats-mqtt-retained-267.json').write_text(json.dumps(base,indent=2)+'\n')
