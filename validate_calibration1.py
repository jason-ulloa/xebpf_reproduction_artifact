#!/usr/bin/env python3
import argparse, json, re, sys
from pathlib import Path

ap=argparse.ArgumentParser(description='Validate CAL-1 against the frozen public reproduction protocol')
ap.add_argument('--root',default='/var/lib/ebpf-research')
ap.add_argument('--reps',type=int,default=5)
ap.add_argument('--protocol-spec',default=str(Path(__file__).with_name('protocol_spec.json')))
a=ap.parse_args()
root=Path(a.root); spec=json.loads(Path(a.protocol_spec).read_text()); errors=[]; rows=[]
cal=spec['acquisition']['calibration']
for r in range(1,a.reps+1):
    exp=f'CAL1-R{r:02d}'
    matches=[]
    for d in root.glob(exp+'_*'):
        if d.is_dir(): matches.append(d)
    if len(matches)!=1:
        errors.append(f'{exp}: expected exactly 1 run, found {len(matches)}'); continue
    d=matches[0]
    needed=['metadata.json','stats.json','events.jsonl','workload_status.json']
    for fn in needed:
        if not (d/fn).is_file(): errors.append(f'{exp}: missing {fn}')
    try:
        m=json.loads((d/'metadata.json').read_text()); s=json.loads((d/'stats.json').read_text()); w=json.loads((d/'workload_status.json').read_text())
    except Exception as e:
        errors.append(f'{exp}: parse error: {e}'); continue
    checks=[
        (m.get('schema_version')==spec['schema_version'],'schema'),
        (m.get('collector')==spec['collector'],'collector'),
        (m.get('capture_scope')==spec['capture_scope'],'capture_scope'),
        (m.get('raw_identifiers_persisted') is spec['raw_identifiers_persisted'],'raw_identifiers_persisted'),
        (m.get('workload_id')==cal['workload'],'workload_id'),
        (m.get('label')==cal['label'],'label'),
        (int(s.get('malformed_lines',-1))==0,'malformed_lines'),
        (int(s.get('exit_code',-1))==0,'collector_exit_code'),
        (w.get('workload_completed') is True,'workload_completed'),
        (int(w.get('workload_exit_code',-1))==0,'workload_exit_code'),
        (int(w.get('workload_duration_seconds',-1))==spec['acquisition']['workload_duration_seconds'],'workload_duration_seconds'),
        (int(w.get('rate_per_second',-1))==spec['acquisition']['rate_per_second'],'rate_per_second'),
    ]
    for ok,name in checks:
        if not ok: errors.append(f'{exp}: {name} mismatch')
    rows.append((exp,s.get('total_events'),s.get('event_counts',{})))
print(f'runs_found={len(rows)} expected={a.reps}')
for exp,total,counts in rows: print(f'{exp}\ttotal={total}\t{json.dumps(counts,sort_keys=True)}')
if errors:
    print('\nFAIL: CAL-1 validation')
    for e in errors: print(' - '+e)
    sys.exit(2)
print('\nPASS: CAL-1 matches the frozen public reproduction protocol')
