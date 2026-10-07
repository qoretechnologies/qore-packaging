# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json,subprocess
root=Path.cwd()
source=root/'work/nats-prepared-49/nats-server-2.15.0'
out=root/'work/nats-mqtt-retained-266-20261008'
out.mkdir()
original=(source/'server/mqtt_test.go').read_text()
a=original.index('func TestMQTTRetainedMessageWithDelSubjectIsNotRestored(')
b=original.index('\nfunc ',a+1)
body=original[a:b]
needle='mc, r := testMQTTConnectRetry(t, &mqttConnInfo{cleanSess: true},'
assert body.count(needle)==1
body=body.replace(needle,'mc, r := testMQTTConnectRetry(t, &mqttConnInfo{clientID: "retained-publisher", cleanSess: true},',1)
needle='\ttestMQTTPublish(t, mc, r, 0, false, true, "foo/ok", 0, []byte("ok"))\n'
assert body.count(needle)==1
registration='\tawaitRetained := testMQTTObserveRetained(t, testMQTTGetAccountSessionManager(t, s, "retained-publisher"), nil)\n'
clean=body.replace(needle,registration+needle+'\t// QoS 0 write completion does not establish retained storage before restart.\n\tawaitRetained("ok")\n')
(out/'clean.go').write_text(original[:a]+clean+original[b:])
control=body.replace(needle,registration+'''	// Hold the actual MQTT read path while an independent NATS connection
	// performs the fixture's other publish. This changes no server code.
	publisher := testMQTTGetClient(t, s, "retained-publisher")
	publisher.mu.Lock()
	var once sync.Once
	release := func() { once.Do(publisher.mu.Unlock) }
	defer release()
'''+needle)
needle='''	require_NoError(t, err)

	// Restart the server so retained-message recovery runs through'''
assert control.count(needle)==1
control=control.replace(needle,'''	require_NoError(t, err)
	_, err = js.GetLastMsg(mqttRetainedMsgsStreamName, mqttRetainedMsgsStreamSubject+"foo.ok")
	require_True(t, errors.Is(err, nats.ErrMsgNotFound))
	t.Log("QoS0 write, publisher close and independent legacy PubAck all completed while the valid retained message was still absent")
	release()
	awaitRetained("ok")
	stored, err := js.GetLastMsg(mqttRetainedMsgsStreamName, mqttRetainedMsgsStreamSubject+"foo.ok")
	require_NoError(t, err)
	var valid mqttRetainedMsg
	require_NoError(t, json.Unmarshal(stored.Data, &valid))
	require_Equal(t, valid.Subject, "foo.ok")
	require_Equal(t, string(valid.Msg), "ok")

	// Restart the server so retained-message recovery runs through''')
(out/'control.go').write_text(original[:a]+control+original[b:])
for p in out.glob('*.go'): subprocess.run(['gofmt','-w',str(p)],check=True)
cases=[]
for variant,count in [('clean',20),('control',5)]:
 for target in ['fedora','leap','el10']:
  cases.append({'name':f'{target}-nats-mqtt-retained-266-{variant}','target':target,'count':count,'race':True,
   'pattern':'^TestMQTTRetainedMessageWithDelSubjectIsNotRestored$',
   'sublist':str((source/'server/sublist.go').relative_to(root)),
   'overlays':{str((out/(variant+'.go')).relative_to(root)):'server/mqtt_test.go'}})
(root/'work/nats-mqtt-retained-266.json').write_text(json.dumps({'source':str(source.relative_to(root)),'workers':3,'cases':cases},indent=2)+'\n')
print('Prepared clean storage precondition and independently ordered MQTT/NATS control')
