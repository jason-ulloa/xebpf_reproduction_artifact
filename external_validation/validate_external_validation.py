#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path
import pandas as pd
ap=argparse.ArgumentParser(description='Validate Security-Gym EV2/EV2.1 outputs against the frozen external-validation protocol')
ap.add_argument('--results-root',default='results'); ap.add_argument('--tolerance',type=float,default=0.02); a=ap.parse_args(); root=Path(a.results_root); errors=[]; warnings=[]
summary=root/'ev2'/'summary.json'
if not summary.is_file(): errors.append('missing ev2/summary.json')
else:
 try:
  s=json.loads(summary.read_text())
  if s.get('dataset')!='Security-Gym v4.1': errors.append('dataset identity mismatch')
  if s.get('dataset_doi')!='10.5281/zenodo.21763493': errors.append('Security-Gym DOI mismatch')
  if int(s.get('windows',-1))!=457786: errors.append(f'window count={s.get("windows")} expected=457786')
  if int(s.get('malicious_windows',-1))!=6180: errors.append(f'malicious windows={s.get("malicious_windows")} expected=6180')
  fam=set(s.get('attack_families',[])); expected={'brute_force','credential_stuffing','discovery','execution','web_exploit'}
  if fam!=expected: errors.append('attack family set mismatch')
 except Exception as e: errors.append('ev2 summary parse error: '+str(e))
for fn in [root/'ev2'/'temporal_forward_results.csv',root/'ev2'/'leave_one_attack_family_out.csv',root/'ev21'/'combined_temporal_loafo_results.csv',root/'ev21'/'combined_temporal_loafo_summary.csv']:
 if not fn.is_file(): errors.append('missing '+str(fn))
# EV2.1 is based on a fixed public stream and deterministic seeds, so approximate reported means are a useful integrity check.
p=root/'ev21'/'combined_temporal_loafo_summary.csv'
if p.is_file():
 try:
  d=pd.read_csv(p).set_index('model')
  expected={'logreg':{'f1':0.248549,'pr_auc':0.224268,'mcc':0.232865},'rf100_sensitivity':{'f1':0.212647,'pr_auc':0.212965,'mcc':0.176863}}
  for model,vals in expected.items():
   if model not in d.index: errors.append('EV2.1 missing model '+model); continue
   for metric,target in vals.items():
    observed=float(d.loc[model,metric])
    if abs(observed-target)>a.tolerance: warnings.append(f'EV2.1 {model} {metric}={observed:.6f} differs from reported {target:.6f} by > {a.tolerance}; inspect numerical-library/platform effects and protocol')
 except Exception as e: errors.append('EV2.1 summary parse error: '+str(e))
print('XEBPF EXTERNAL VALIDATION CHECK')
print('Structural/frozen-dataset result:','PASS' if not errors else 'FAIL')
for e in errors: print(' - ERROR:',e)
for w in warnings: print(' - WARNING:',w)
if errors: sys.exit(2)
