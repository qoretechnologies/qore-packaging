# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import difflib,json,subprocess
src=Path('work/nats-prepared-43/nats-server-2.15.0');out=Path('work/nats-tls-warning-228');out.mkdir()
p=src/'server/server_test.go';original=p.read_text();s=original
start=s.index('func TestInsecureSkipVerifyWarning(t *testing.T) {');middle=s.index('\n\ttc := &TLSConfigOpts{}',start)
body=s[start:middle]
body=body.replace('func TestInsecureSkipVerifyWarning(t *testing.T) {\n\tcheckWarnReported := func(t *testing.T, o *Options, expectedWarn string) {','func checkTLSInsecureWarning(t *testing.T, o *Options, expectedWarn string) string {')
body=body[:body.rindex('\n\t}')]+ '\n}'
body=body.replace('\n\t\t','\n\t')
body=body.replace('s, err := NewServer(o)','// Server startup writes assigned listener ports into its options. Each\n\t// warning case needs an independent copy of the reusable caller configuration.\n\ts, err := NewServer(o.Clone())')
body=body.replace('\twg.Add(1)\n','\twg.Add(1)\n\tdefer func() {\n\t\ts.Shutdown()\n\t\twg.Wait()\n\t}()\n')
body=body.replace('\ts.Shutdown()\n\twg.Wait()\n}', '\treturn s.ClientURL()\n}')
s=s[:start]+body+'\n\nfunc TestInsecureSkipVerifyWarning(t *testing.T) {'+s[middle:]
end=s.index('\nfunc TestConnectErrorReports(',start)
s=s[:start]+s[start:end].replace('checkWarnReported(', 'checkTLSInsecureWarning(')+s[end:]
s += '''
// A completed warning fixture must not reuse the previous kernel-assigned port.
func TestTLSInsecureWarningUsesFreshEphemeralListeners(t *testing.T) {
    config, err := GenTLSConfig(&TLSConfigOpts{
        CertFile: "../test/configs/certs/server-cert.pem",
        KeyFile: "../test/configs/certs/server-key.pem",
        CaFile: "../test/configs/certs/ca.pem",
        Insecure: true,
    })
    require_NoError(t, err)
    opts := DefaultOptions()
    opts.Cluster.Name = "TLS-WARNING"
    opts.Cluster.Port = -1
    opts.Cluster.TLSConfig = config
    address, err := url.Parse(checkTLSInsecureWarning(t, opts, clusterTLSInsecureWarning))
    require_NoError(t, err)
    // Reserve the released client address, forcing any stale-port reuse to fail.
    listener, err := net.Listen("tcp", address.Host)
    require_NoError(t, err)
    defer listener.Close()
    next, err := url.Parse(checkTLSInsecureWarning(t, opts, clusterTLSInsecureWarning))
    require_NoError(t, err)
    require_NotEqual(t, address.Host, next.Host)
    require_Equal(t, opts.Port, -1)
    require_Equal(t, opts.Cluster.Port, -1)
}
'''
(out/'server_test.go').write_text(s);subprocess.run(['gofmt','-w',str(out/'server_test.go')],check=True)
s=(out/'server_test.go').read_text();assert s.count('func checkTLSInsecureWarning(')==1
a=s.index('func checkTLSInsecureWarning(');b=s.index('\nfunc TestInsecureSkipVerifyWarning(',a);negative=s[:a]+s[a:b].replace('NewServer(o.Clone())','NewServer(o)')+s[b:];assert negative!=s;(out/'negative_server_test.go').write_text(negative)
patch='# Copyright 2026 Qore Technologies, s.r.o.; Apache-2.0.\n# Preserve ephemeral listener settings between independent TLS warning fixtures.\n'+''.join(difflib.unified_diff(original.splitlines(True),s.splitlines(True),fromfile='a/server/server_test.go',tofile='b/server/server_test.go'))
(out/'nats-server-tls-warning-listeners-tests.patch').write_text(patch)
for variant,count,pattern in [('fixed',25,'^(TestInsecureSkipVerifyWarning|TestTLSInsecureWarningUsesFreshEphemeralListeners)$'),('negative',1,'^TestTLSInsecureWarningUsesFreshEphemeralListeners$')]:
 cases=[]
 for target in ['fedora','leap','el10']:
  cases.append({'name':f'{target}-nats-tls-warning-228-{variant}','target':target,'count':count,'race':True,'pattern':pattern,'sublist':str(src/'server/sublist.go'),'overlays':{str(out/('server_test.go' if variant=='fixed' else 'negative_server_test.go')):'server/server_test.go'}})
 Path(f'work/nats-tls-warning-228-{variant}.json').write_text(json.dumps({'source':str(src),'workers':3,'cases':cases},indent=2)+'\n')
