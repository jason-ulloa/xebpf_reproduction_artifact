#!/usr/bin/env python3
import argparse,json,os,sys
ap=argparse.ArgumentParser(); ap.add_argument('--root',default='/var/lib/ebpf-research'); ap.add_argument('--reps',type=int,default=3); a=ap.parse_args()
profiles=['FILE_CHURN','PROCESS_CHAIN','LOOPBACK_BEACON','STAGING','MIXED_BURST']; errors=[]; found=[]
for p in profiles:
 for r in range(1,a.reps+1):
  prefix='AE1-%s-R%02d'%(p,r); matches=[]
  for name in os.listdir(a.root):
   d=os.path.join(a.root,name)
   if os.path.isdir(d) and name.startswith(prefix): matches.append(d)
  if len(matches)!=1: errors.append('%s expected 1 run, found %d'%(prefix,len(matches))); continue
  d=matches[0]; found.append(d)
  for fn in ['metadata.json','stats.json','events.jsonl']:
   if not os.path.isfile(os.path.join(d,fn)): errors.append('%s missing %s'%(prefix,fn))
  try:
   m=json.load(open(os.path.join(d,'metadata.json'))); s=json.load(open(os.path.join(d,'stats.json')))
   if m.get('schema_version')!='xebpf-1.3.2': errors.append('%s schema=%r'%(prefix,m.get('schema_version')))
   if m.get('capture_scope')!='uid_scoped': errors.append('%s not uid_scoped'%prefix)
   if m.get('label')!='malicious': errors.append('%s label=%r'%(prefix,m.get('label')))
   if int(s.get('malformed_lines',-1))!=0: errors.append('%s malformed_lines=%r'%(prefix,s.get('malformed_lines')))
   if int(s.get('exit_code',-1))!=0: errors.append('%s exit_code=%r'%(prefix,s.get('exit_code')))
  except Exception as e: errors.append('%s parse error: %s'%(prefix,e))
print('runs_found=%d expected=%d'%(len(found),len(profiles)*a.reps))
if errors:
 print('FAIL: ATTACK-EMULATION-1 validation'); [print(' - '+e) for e in errors]; sys.exit(2)
print('PASS: ATTACK-EMULATION-1 result set is structurally valid')
