# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import difflib
import hashlib
import json

root = Path('work/node-obs-diagnostic-20261006/node-v24.18.1')
out = Path('work/node-reschedule-native-20261007')
relative = 'deps/v8/src/compiler/raw-machine-assembler.cc'
original = (root / relative).read_text()
anchor = '''    } else if (block->IsLoopHeader()) {'''
replacement = '''      // The end block only collects terminal control inputs. It has no nodes
      // or successors requiring a final effect/control pair.
      DCHECK(block->empty());
      DCHECK_EQ(block->control(), BasicBlock::kNone);
      DCHECK_NULL(block->control_input());
      DCHECK_EQ(block->SuccessorCount(), 0);
      continue;
    } else if (block->IsLoopHeader()) {'''
assert original.count(anchor) == 1
fixed = original.replace(anchor, replacement)
declaration = '    Node* current_control;\n    Node* current_effect;'
instrument_declaration = declaration + '''
    // Diagnostic only: reflect each new C++ lifetime in Memcheck shadow state.
    VALGRIND_MAKE_MEM_UNDEFINED(&current_control, sizeof(current_control));
    VALGRIND_MAKE_MEM_UNDEFINED(&current_effect, sizeof(current_effect));'''
store = '    block_final_effect[block->id().ToSize()] = current_effect;'
instrument_store = '''    VALGRIND_CHECK_MEM_IS_DEFINED(&current_control, sizeof(current_control));
    VALGRIND_CHECK_MEM_IS_DEFINED(&current_effect, sizeof(current_effect));
''' + store
for name, text in [('original', original), ('fixed', fixed)]:
    (out / (name + '-raw.cc')).write_text(text)
    assert text.count(declaration) == 1 and text.count(store) == 1
    instrumented = '#include <valgrind/memcheck.h>\n' + text.replace(
        declaration, instrument_declaration).replace(store, instrument_store)
    (out / (name + '-instrumented-raw.cc')).write_text(instrumented)
(out / 'proposed.patch').write_text(
    '# Copyright 2026 Qore Technologies, s.r.o.; BSD-3-Clause.\n'
    '# Finish terminal control merging before reading nonexistent end-block state.\n' +
    ''.join(difflib.unified_diff(original.splitlines(True), fixed.splitlines(True),
        fromfile='a/' + relative, tofile='b/' + relative)))
(out / 'source-hashes.json').write_text(json.dumps({p.name: hashlib.sha256(p.read_bytes()).hexdigest()
    for p in out.glob('*raw.cc')}, indent=2) + '\n')
