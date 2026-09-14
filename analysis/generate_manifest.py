#!/usr/bin/env python3
import argparse, csv, json, re
from pathlib import Path

def main():
    ap=argparse.ArgumentParser(description='Build an analysis manifest from validated BENIGN-1 and ATTACK-EMULATION-1 runs')
    ap.add_argument('--root',default='/var/lib/ebpf-research'); ap.add_argument('--host',required=True,help='Neutral environment label, e.g. E1'); ap.add_argument('--output',required=True)
    ap.add_argument('--protocol-spec',default=str(Path(__file__).resolve().parents[1]/'protocol_spec.json')); a=ap.parse_args()
    spec=json.loads(Path(a.protocol_spec).read_text()); root=Path(a.root); rows=[]; errors=[]
    expected=set(spec['acquisition']['benign']['profiles']+spec['acquisition']['attack_emulation']['profiles'])
    for d in sorted(root.iterdir() if root.exists() else []):
        if not d.is_dir() or not (d.name.startswith('BENIGN1-') or d.name.startswith('AE1-')): continue
        mp,ep,wp,sp=d/'metadata.json',d/'events.jsonl',d/'workload_status.json',d/'stats.json'
        if not all(x.exists() for x in [mp,ep,wp,sp]): errors.append(f'{d.name}: missing metadata/events/workload_status/stats'); continue
        try: m=json.loads(mp.read_text()); w=json.loads(wp.read_text()); s=json.loads(sp.read_text())
        except Exception as e: errors.append(f'{d.name}: JSON parse error: {e}'); continue
        if m.get('schema_version')!=spec['schema_version'] or m.get('collector')!=spec['collector'] or m.get('capture_scope')!=spec['capture_scope']: errors.append(f'{d.name}: collector protocol metadata mismatch'); continue
        if s.get('malformed_lines')!=0 or s.get('exit_code')!=0: errors.append(f'{d.name}: collector status invalid'); continue
        if not w.get('workload_completed') or int(w.get('workload_exit_code',-1))!=0: errors.append(f'{d.name}: workload did not complete successfully'); continue
        if int(w.get('workload_duration_seconds',-1))!=spec['acquisition']['workload_duration_seconds'] or int(w.get('rate_per_second',-1))!=spec['acquisition']['rate_per_second']: errors.append(f'{d.name}: workload duration/rate mismatch'); continue
        if m.get('workload_id') not in expected or w.get('workload_id')!=m.get('workload_id'): errors.append(f'{d.name}: workload identity mismatch'); continue
        match=re.search(r'-R(\d+)$',str(m.get('experiment_id','')))
        if not match: errors.append(f'{d.name}: cannot infer repetition from experiment_id'); continue
        label_text=m.get('label')
        if label_text not in {'benign','malicious'}: errors.append(f'{d.name}: unexpected label {label_text!r}'); continue
        rows.append({'host':a.host,'workload':m.get('workload_id'),'label':0 if label_text=='benign' else 1,'rep':int(match.group(1)),'events_jsonl':str(ep.resolve())})
    if errors:
        print('Manifest generation errors:'); [print(' - '+e) for e in errors]; raise SystemExit(2)
    if len(rows)!=30: raise SystemExit(f'ERROR: eligible classification runs={len(rows)} expected=30')
    keys={(r['workload'],r['rep']) for r in rows}
    if len(keys)!=30: raise SystemExit('ERROR: duplicate/missing workload-repetition cells in classification manifest')
    out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('w',newline='') as f:
        wr=csv.DictWriter(f,fieldnames=['host','workload','label','rep','events_jsonl']); wr.writeheader(); wr.writerows(rows)
    print(f'PASS: wrote 30 validated classification runs for {a.host} to {out}')
if __name__=='__main__': main()
