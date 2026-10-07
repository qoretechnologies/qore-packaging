# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import difflib,json,subprocess
src=Path('work/nats-prepared-44/nats-server-2.15.0');out=Path('work/nats-publication-231-20261007');out.mkdir();patch=[]
def edit_function(text,name,change):
 a=text.index('func '+name+'(');b=text.find('\nfunc ',a+1);b=len(text) if b<0 else b
 return text[:a]+change(text[a:b])+text[b:]
filename='jetstream_batching_test.go';original=(src/'server'/filename).read_text();new=original
for name in ['TestJetStreamFastBatchPublishHeaderCheckError','TestJetStreamFastBatchPublishHeaderCheckErrorOnCommit']:
 def change(s):
  marker='\n\t\tinbox := nats.NewInbox()';assert s.count(marker)==1
  return s.replace(marker,'\n\t\t// Creation replies use a different route from stream subscriptions.\n\t\tawaitStreamRouteInterest(t, c, nc, "TEST")\n'+marker)
 new=edit_function(new,name,change)
files={filename:(original,new)}
ack='''
{indent}// Completion closes for both successful and failed asynchronous publishes.
{indent}// Check every acknowledgement before observing the prepared stream state.
{indent}for i, future := range futures {{
{indent}\tselect {{
{indent}\tcase ack := <-future.Ok():
{indent}\t\trequire_Equal(t, ack.Stream, "{stream}")
{indent}\t\trequire_Equal(t, ack.Sequence, uint64(i+1))
{indent}\tcase err := <-future.Err():
{indent}\t\tt.Fatalf("setup publication %d failed: %v", i+1, err)
{indent}\tdefault:
{indent}\t\tt.Fatalf("setup publication %d completed without a result", i+1)
{indent}\t}}
{indent}}}
'''
for filename,name,stream,indent,count in [('jetstream_test.go','TestJetStreamLastSequenceBySubjectWithSubject','KV','\t\t\t',7),('jetstream_consumer_test.go','TestJetStreamConsumerNumPendingWithMaxPerSubjectGreaterThanOne','TEST','\t\t',8)]:
 original=(src/'server'/filename).read_text()
 def change(s):
  first=s.index(indent+'js.PublishAsync(')
  pre=indent+f'futures := make([]nats.PubAckFuture, 0, {count})\n'+indent+'publish := func(subject string, data []byte) {\n'+indent+'\tt.Helper()\n'+indent+'\tfuture, err := js.PublishAsync(subject, data)\n'+indent+'\trequire_NoError(t, err)\n'+indent+'\tfutures = append(futures, future)\n'+indent+'}\n'
  if stream=='KV':pre=indent+'awaitStreamRouteInterest(t, c, nc, "KV")\n'+pre
  s=s[:first]+pre+s[first:].replace('js.PublishAsync(', 'publish(')
  if stream=='KV':
   marker='\n'+indent+'// Now make sure we get an error';assert s.count(marker)==1
   return s.replace(marker,ack.format(indent=indent,stream=stream)+marker)
  marker='\n'+indent+'ci, err := js.AddConsumer';assert s.count(marker)==1
  completion=indent+'select {\n'+indent+'case <-js.PublishAsyncComplete():\n'+indent+'case <-time.After(time.Second):\n'+indent+'\tt.Fatal("setup publications did not complete")\n'+indent+'}\n'
  return s.replace(marker,'\n'+completion+ack.format(indent=indent,stream=stream)+marker)
 new=edit_function(original,name,change);files[filename]=(original,new)
for name,(old,new) in files.items():
 p=out/name;p.write_text(new);subprocess.run(['gofmt','-w',str(p)],check=True);patch.append(''.join(difflib.unified_diff(old.splitlines(True),p.read_text().splitlines(True),fromfile='a/server/'+name,tofile='b/server/'+name)))
(out/'nats-server-publication-completion-tests.patch').write_text('# Copyright 2026 Qore Technologies, s.r.o.; Apache-2.0.\n# Join stream interest and verify async acknowledgements before fixture state assertions.\n'+''.join(patch))
cases=[]
for target in ['fedora','leap','el10']:
 cases.append({'name':f'{target}-nats-publication-231-fixed','target':target,'count':20,'race':True,'pattern':'^(TestJetStreamFastBatchPublishHeaderCheckError|TestJetStreamFastBatchPublishHeaderCheckErrorOnCommit|TestJetStreamLastSequenceBySubjectWithSubject|TestJetStreamConsumerNumPendingWithMaxPerSubjectGreaterThanOne)$','sublist':str(src/'server/sublist.go'),'overlays':{str(out/n):'server/'+n for n in files}})
Path('work/nats-publication-231-fixed.json').write_text(json.dumps({'source':str(src),'workers':3,'cases':cases},indent=2)+'\n')
