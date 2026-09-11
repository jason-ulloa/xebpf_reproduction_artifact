#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
ap=argparse.ArgumentParser(); ap.add_argument('--root',default='/var/lib/ebpf-research'); ap.add_argument('--reps',type=int,default=3); a=ap.parse_args()
root=Path(a.root); expected={'benign-file-v1','benign-process-v1','benign-network-v1','benign-service-v1','benign-bursty-v1'}; runs=[]; errors=[]
for d in sorted(root.glob('BENIGN1-*')):
 if not d.is_dir(): continue
 mp,sp=d/'metadata.json',d/'stats.json'
 if not mp.exists() or not sp.exists(): errors.append('%s missing metadata/stats'%d.name); continue
 try:m=json.loads(mp.read_text()); s=json.loads(sp.read_text())
 except Exception as e: errors.append('%s JSON error %s'%(d.name,e)); continue
 if m.get('schema_version')!='xebpf-1.3.2': errors.append('%s bad schema'%d.name)
 if m.get('capture_scope')!='uid_scoped': errors.append('%s not uid_scoped'%d.name)
 if m.get('raw_identifiers_persisted') is not False: errors.append('%s raw identifiers flag'%d.name)
 if m.get('workload_id') not in expected: errors.append('%s bad workload'%d.name)
 if s.get('malformed_lines')!=0: errors.append('%s malformed=%r'%(d.name,s.get('malformed_lines')))
 if s.get('exit_code')!=0: errors.append('%s exit=%r'%(d.name,s.get('exit_code')))
 runs.append((d.name,m.get('workload_id'),s.get('total_events'),s.get('event_counts',{})))
counts={}
for _,w,_,_ in runs: counts[w]=counts.get(w,0)+1
for w in sorted(expected):
 if counts.get(w,0)!=a.reps: errors.append('%s runs=%d expected=%d'%(w,counts.get(w,0),a.reps))
print('runs=%d expected=%d'%(len(runs),len(expected)*a.reps))
for r in runs: print('%s\t%s\ttotal=%s\t%s'%(r[0],r[1],r[2],json.dumps(r[3],sort_keys=True)))
if errors:
 print('\nFAIL'); [print(' - '+e) for e in errors]; sys.exit(1)
print('\nPASS: BENIGN-1 result set is structurally valid')
