from pathlib import Path
import hashlib,json,re,subprocess
root=Path.cwd();records=[]
for binary in sorted(Path('payload/usr/lib/debug').rglob('*.debug')):
 if binary.is_symlink():continue
 sections=subprocess.check_output(['readelf','-SW',str(binary)],text=True)
 if '.debug_names' not in sections:continue
 label=binary.name;dest=root/label;dest.mkdir();original=dest/'original.debug';original.write_bytes(binary.read_bytes());fixed=dest/'no-index.debug'
 subprocess.run(['objcopy','--remove-section=.debug_names',str(original),str(fixed)],check=True)
 debug_sections=re.findall(r'\[\s*\d+\]\s+(\.debug_[\w.]+)\s',sections);assert len(debug_sections)>4
 hashes={}
 for section in debug_sections:
  if section=='.debug_names':continue
  files=[]
  for path,prefix in ((original,'original'),(fixed,'no-index')):
   output=dest/(prefix+section);subprocess.run(['objcopy','--dump-section',section+'='+str(output),str(path)],check=True);files.append(output.read_bytes())
  assert files[0]==files[1],(binary,section);hashes[section]=hashlib.sha256(files[0]).hexdigest()
 sym1=subprocess.check_output(['nm','-a',str(original)]);sym2=subprocess.check_output(['nm','-a',str(fixed)]);assert sym1==sym2
 options=['gdb','-q','-batch','-ex','set debuginfod enabled off','-ex','set substitute-path /usr/src/debug /fixture/payload/usr/src/debug','-ex','info functions _qaot_']
 initial=subprocess.run([*options,str(original)],capture_output=True,text=True,check=True);(dest/'original-functions.txt').write_text(initial.stdout+initial.stderr)
 source=None;location=None
 for line in initial.stdout.splitlines():
  if line.startswith('File '):source=line[5:].removesuffix(':')
  match=re.match(r'(\d+):\s+void _qaot_',line)
  if match and source:location=source+':'+match[1];break
 assert location,(binary,initial.stdout)
 options+=['-ex','break '+location,'-ex','info breakpoints','-ex','list '+location]
 outputs={}
 for path,prefix in ((original,'original'),(fixed,'no-index')):
  result=subprocess.run([*options,str(path)],capture_output=True,text=True,check=True);text=result.stdout+result.stderr;(dest/(prefix+'-gdb.txt')).write_text(text);outputs[prefix]=text
 assert 'warning: .debug_names not created by gdb; ignoring' in outputs['original'],outputs['original']
 assert not re.search(r'warning:|No source file|No line |No symbol',outputs['no-index']),outputs['no-index']
 assert 'Breakpoint 1 at ' in outputs['no-index'] and 'breakpoint     keep y' in outputs['no-index'],outputs['no-index']
 aot=lambda t:[line for line in t.splitlines() if re.match(r'\d+:\s+void _qaot_',line)]
 assert aot(outputs['original'])==aot(outputs['no-index']);assert aot(outputs['no-index'])
 assert any(re.match(r'\d+\s+[^\s]',l) for l in outputs['no-index'].splitlines()),outputs['no-index']
 edit=dest/'debugedit-no-index.debug';edit.write_bytes(fixed.read_bytes());r=subprocess.run(['debugedit','-b','/usr/src/debug','-d','/usr/src/debug','-i',str(edit)],capture_output=True,text=True);(dest/'debugedit.txt').write_text(r.stdout+r.stderr);assert r.returncode==0 and not r.stderr,r.stderr
 records.append({'binary':str(binary),'original_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'all_dwarf_sections_preserved':hashes,'symbols_unchanged':True,'aot_functions':len(aot(outputs['no-index'])),'breakpoint_source_location':location,'gdb_warning_removed':True,'debugedit_stderr':''})
assert len(records)==1,len(records)
Path('checks.json').write_text(json.dumps(records,indent=2)+'\n');print('PASS: GEOS AOT module preserve every DWARF section and symbol, GDB source/breakpoint lookup and debugedit pass')
