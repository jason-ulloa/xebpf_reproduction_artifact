#!/usr/bin/env python3
import argparse,json,os,sys
from pathlib import Path
ap=argparse.ArgumentParser(); ap.add_argument('--root',default='/var/lib/ebpf-research'); ap.add_argument('--reps',type=int,default=3); ap.add_argument('--protocol-spec',default=str(Path(__file__).with_name('protocol_spec.json'))); a=ap.parse_args()
root=Path(a.root); spec=json.loads(Path(a.protocol_spec).read_text()); errors=[]; found=[]
profiles={
 'FILE_CHURN':'ae-file-churn-v1','PROCESS_CHAIN':'ae-process-chain-v1','LOOPBACK_BEACON':'ae-loopback-beacon-v1','STAGING':'ae-staging-v1','MIXED_BURST':'ae-mixed-burst-v1'}
for p,workload in profiles.items():
 for r in range(1,a.reps+1):
  prefix='AE1-%s-R%02d'%(p,r); matches=[]
  for name in os.listdir(a.root):
   d=os.path.join(a.root,name)
   if os.path.isdir(d) and name.startswith(prefix): matches.append(d)
  if len(matches)!=1: errors.append('%s expected 1 run, found %d'%(prefix,len(matches))); continue
  d=matches[0]; found.append(d)
  for fn in ['metadata.json','stats.json','events.jsonl','workload_status.json']:
   if not os.path.isfile(os.path.join(d,fn)): errors.append('%s missing %s'%(prefix,fn))
  try:
   m=json.load(open(os.path.join(d,'metadata.json'))); s=json.load(open(os.path.join(d,'stats.json'))); w=json.load(open(os.path.join(d,'workload_status.json')))
   checks={
    'schema':m.get('schema_version')==spec['schema_version'], 'collector':m.get('collector')==spec['collector'],
    'capture_scope':m.get('capture_scope')==spec['capture_scope'], 'raw_identifiers_persisted':m.get('raw_identifiers_persisted') is spec['raw_identifiers_persisted'],
    'label':m.get('label')=='malicious','workload':m.get('workload_id')==workload,
    'malformed_lines':int(s.get('malformed_lines',-1))==0,'collector_exit_code':int(s.get('exit_code',-1))==0,
    'workload_completed':w.get('workload_completed') is True,'workload_exit':int(w.get('workload_exit_code',-1))==0,
    'duration':int(w.get('workload_duration_seconds',-1))==spec['acquisition']['workload_duration_seconds'],
    'rate':int(w.get('rate_per_second',-1))==spec['acquisition']['rate_per_second'],
    'status_workload':w.get('workload_id')==workload,
   }
   for name,ok in checks.items():
    if not ok: errors.append('%s %s mismatch'%(prefix,name))
  except Exception as e: errors.append('%s parse error: %s'%(prefix,e))
sg=root/'ATTACK_EMULATION1_SAFETY_GATE.json'
if not sg.is_file(): errors.append('missing ATTACK_EMULATION1_SAFETY_GATE.json')
else:
 try:
  gate=json.loads(sg.read_text())
  if gate.get('passed') is not True: errors.append('production safety gate did not pass')
  if gate.get('network_scope')!=spec['acquisition']['attack_emulation']['network_scope']: errors.append('safety gate network scope mismatch')
  if gate.get('filesystem_scope')!=spec['acquisition']['attack_emulation']['filesystem_scope']: errors.append('safety gate filesystem scope mismatch')
 except Exception as e: errors.append('safety gate parse error: %s'%e)
print('runs_found=%d expected=%d'%(len(found),len(profiles)*a.reps))
if errors:
 print('FAIL: ATTACK-EMULATION-1 validation'); [print(' - '+e) for e in errors]; sys.exit(2)
print('PASS: ATTACK-EMULATION-1 matches the frozen public reproduction protocol and safety gate evidence is present')
