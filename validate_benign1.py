#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
ap=argparse.ArgumentParser(); ap.add_argument('--root',default='/var/lib/ebpf-research'); ap.add_argument('--reps',type=int,default=3); ap.add_argument('--protocol-spec',default=str(Path(__file__).with_name('protocol_spec.json'))); a=ap.parse_args()
root=Path(a.root); spec=json.loads(Path(a.protocol_spec).read_text()); expected=set(spec['acquisition']['benign']['profiles']); runs=[]; errors=[]
for d in sorted(root.glob('BENIGN1-*')):
 if not d.is_dir(): continue
 mp,sp,wp=d/'metadata.json',d/'stats.json',d/'workload_status.json'
 if not mp.exists() or not sp.exists() or not wp.exists(): errors.append('%s missing metadata/stats/workload_status'%d.name); continue
 try:m=json.loads(mp.read_text()); s=json.loads(sp.read_text()); wstat=json.loads(wp.read_text())
 except Exception as e: errors.append('%s JSON error %s'%(d.name,e)); continue
 checks={
  'schema':m.get('schema_version')==spec['schema_version'],
  'collector':m.get('collector')==spec['collector'],
  'capture_scope':m.get('capture_scope')==spec['capture_scope'],
  'raw_identifiers_persisted':m.get('raw_identifiers_persisted') is spec['raw_identifiers_persisted'],
  'workload':m.get('workload_id') in expected,
  'label':m.get('label')=='benign',
  'malformed_lines':int(s.get('malformed_lines',-1))==0,
  'collector_exit':int(s.get('exit_code',-1))==0,
  'workload_completed':wstat.get('workload_completed') is True,
  'workload_exit':int(wstat.get('workload_exit_code',-1))==0,
  'duration':int(wstat.get('workload_duration_seconds',-1))==spec['acquisition']['workload_duration_seconds'],
  'rate':int(wstat.get('rate_per_second',-1))==spec['acquisition']['rate_per_second'],
  'status_workload':wstat.get('workload_id')==m.get('workload_id'),
 }
 for name,ok in checks.items():
  if not ok: errors.append('%s %s mismatch'%(d.name,name))
 runs.append((d.name,m.get('workload_id'),s.get('total_events'),s.get('event_counts',{})))
counts={}
for _,w,_,_ in runs: counts[w]=counts.get(w,0)+1
for w in sorted(expected):
 if counts.get(w,0)!=a.reps: errors.append('%s runs=%d expected=%d'%(w,counts.get(w,0),a.reps))
print('runs=%d expected=%d'%(len(runs),len(expected)*a.reps))
for r in runs: print('%s\t%s\ttotal=%s\t%s'%(r[0],r[1],r[2],json.dumps(r[3],sort_keys=True)))
if errors:
 print('\nFAIL'); [print(' - '+e) for e in errors]; sys.exit(1)
print('\nPASS: BENIGN-1 matches the frozen public reproduction protocol')
