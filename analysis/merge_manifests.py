#!/usr/bin/env python3
import argparse, pandas as pd
from pathlib import Path
ap=argparse.ArgumentParser(description='Merge per-environment XEBPF manifests and validate uniqueness')
ap.add_argument('--inputs',nargs='+',required=True); ap.add_argument('--output',required=True); a=ap.parse_args()
parts=[pd.read_csv(x) for x in a.inputs]; d=pd.concat(parts,ignore_index=True)
req=['host','workload','label','rep','events_jsonl']
miss=[c for c in req if c not in d.columns]
if miss: raise SystemExit('ERROR: missing columns '+','.join(miss))
if d[req[:-1]].duplicated().any():
 print(d[d[req[:-1]].duplicated(keep=False)].sort_values(req[:-1]).to_string(index=False)); raise SystemExit('ERROR: duplicate host/workload/label/rep rows')
out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True); d[req].to_csv(out,index=False)
print(f'Wrote {len(d)} rows from {d.host.nunique()} environments to {out}')
