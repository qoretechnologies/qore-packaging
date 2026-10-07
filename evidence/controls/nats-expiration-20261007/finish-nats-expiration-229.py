# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import difflib,json,re,subprocess
src=Path('work/nats-prepared-43/nats-server-2.15.0');out=Path('work/nats-expiration-229-final')
p=out/'dirstore_test.go';s=p.read_text();assert 'func TestExpirationRoundedTimerBoundary' not in s
s+='''
func TestExpirationRoundedTimerBoundary(t *testing.T) {
    store, err := NewExpiringDirJWTStore(t.TempDir(), false, false, NoDelete, time.Hour, 10, true, 0, nil)
    require_NoError(t, err)
    defer store.Close()
    store.Lock()
    tracker := store.expiration
    tracker.close()
    store.Unlock()
    tracker.wg.Wait()
    key,err:=nkeys.CreateAccount()
    require_NoError(t,err)
    pub,err:=key.PublicKey()
    require_NoError(t,err)
    // The original helper rounds its current time before adding one second.
    created:=time.Unix(2000000000,500000001)
    expires:=created.Round(time.Second).Add(time.Second)
    claims:=jwt.NewAccountClaims(pub)
    claims.Expires=expires.Unix()
    token,err:=claims.Encode(key)
    require_NoError(t,err)
    require_NoError(t,store.SaveAcc(pub,token))
    // A legal 50ms timer phase puts one check just before expiry and the next
    // after the old test's 1500ms sleep. No scheduler delay is needed to fail.
    before:=expires.Add(-10*time.Millisecond)
    after:=before.Add(50*time.Millisecond)
    require_True(t,before.Before(created.Add(1500*time.Millisecond)))
    require_True(t,after.After(created.Add(1500*time.Millisecond)))
    store.Lock()
    removed:=store.expireOneLocked(tracker,before.UnixNano())
    store.Unlock()
    require_False(t,removed)
    assertStoreSize(t,store,1)
    store.Lock()
    removed=store.expireOneLocked(tracker,after.UnixNano())
    store.Unlock()
    require_True(t,removed)
    assertStoreSize(t,store,0)
}

func TestExpirationRemovalFailurePreservesState(t *testing.T) {
    store, err := NewExpiringDirJWTStore(t.TempDir(), false, false, NoDelete, time.Hour, 10, true, 0, nil)
    require_NoError(t, err)
    defer store.Close()
    store.Lock()
    tracker:=store.expiration
    tracker.close()
    store.Unlock()
    tracker.wg.Wait()
    key,err:=nkeys.CreateAccount()
    require_NoError(t,err)
    pub,err:=key.PublicKey()
    require_NoError(t,err)
    claims:=jwt.NewAccountClaims(pub)
    claims.Expires=2000000000
    token,err:=claims.Encode(key)
    require_NoError(t,err)
    require_NoError(t,store.SaveAcc(pub,token))
    before:=store.Hash()
    path:=store.pathForKey(pub)
    require_NoError(t,os.Remove(path))
    require_NoError(t,os.Mkdir(path,0700))
    // Removing a nonempty directory fails consistently, including for root.
    child:=filepath.Join(path,"occupied")
    require_NoError(t,os.WriteFile(child,[]byte("keep"),0600))
    store.Lock()
    removed:=store.expireOneLocked(tracker,time.Unix(claims.Expires,0).UnixNano())
    tracked,indexed,cached:=tracker.Len(),len(tracker.idx),tracker.lru.Len()
    store.Unlock()
    require_False(t,removed)
    require_Equal(t,tracked,1)
    require_Equal(t,indexed,1)
    require_Equal(t,cached,1)
    require_Equal(t,store.Hash(),before)
    require_NoError(t,os.Remove(child))
    require_NoError(t,os.Remove(path))
    require_NoError(t,os.WriteFile(path,[]byte(token),0600))
    store.Lock()
    removed=store.expireOneLocked(tracker,time.Unix(claims.Expires,0).UnixNano())
    store.Unlock()
    require_True(t,removed)
    assertStoreSize(t,store,0)
    require_Equal(t,store.Hash(),[32]byte{})
}
''';p.write_text(s);subprocess.run(['gofmt','-w',str(p),str(out/'dirstore.go')],check=True)
patch='# Copyright 2026 Qore Technologies, s.r.o.; Apache-2.0.\n# Test JWT expiry updates at exact boundaries using the unchanged timer expiry step.\n'
for f in ['dirstore.go','dirstore_test.go']:patch+=''.join(difflib.unified_diff((src/'server'/f).read_text().splitlines(True),(out/f).read_text().splitlines(True),fromfile='a/server/'+f,tofile='b/server/'+f))
(out/'nats-server-expiration-boundary-tests.patch').write_text(patch)
code=(out/'dirstore.go').read_text()
mutants={'late':code.replace('it.expiration <= now','it.expiration < now'), 'early':code.replace('it.expiration <= now','it.expiration <= now+1'), 'update':code.replace('i.expiration = exp','_ = exp // deliberately leave the previous deadline')}
for name,body in mutants.items():assert body!=code;(out/(name+'_dirstore.go')).write_text(body)
for variant,count in [('fixed',100),('integration',1),('late',1),('early',1),('update',1)]:
 names=re.findall(r'^func (Test\w+)\(',s,re.M) if variant=='integration' else ['TestExpirationUpdate','TestExpirationRoundedTimerBoundary','TestExpirationRemovalFailurePreservesState']
 cases=[]
 for target in ['fedora','leap','el10']:
  overlays={str(out/'dirstore_test.go'):'server/dirstore_test.go',str(out/('dirstore.go' if variant in ['fixed','integration'] else variant+'_dirstore.go')):'server/dirstore.go'}
  cases.append({'name':f'{target}-nats-expiration-229-final-{variant}','target':target,'count':count,'race':True,'pattern':'^('+'|'.join(names)+')$','sublist':str(src/'server/sublist.go'),'overlays':overlays})
 Path(f'work/nats-expiration-229-final-{variant}.json').write_text(json.dumps({'source':str(src),'workers':3,'cases':cases},indent=2)+'\n')
