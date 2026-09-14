#!/usr/bin/env python3
import argparse, json, re, sys
from collections import Counter, defaultdict
from pathlib import Path

ap=argparse.ArgumentParser(description='Validate one host acquisition corpus against the frozen paper protocol')
ap.add_argument('--root',default='/var/lib/ebpf-research')
ap.add_argument('--host-label',required=True,help='Neutral environment label, e.g. E1')
ap.add_argument('--protocol-spec',default=str(Path(__file__).with_name('protocol_spec.json')))
ap.add_argument('--report-prefix',default=None)
a=ap.parse_args(); root=Path(a.root); spec=json.loads(Path(a.protocol_spec).read_text()); errors=[]; warnings=[]
acq=spec['acquisition']; expected={}
for r in range(1,acq['calibration']['repetitions']+1): expected[f'CAL1-R{r:02d}']=(acq['calibration']['workload'],'benign')
short_b={'benign-file-v1':'FILE','benign-process-v1':'PROCESS','benign-network-v1':'NETWORK','benign-service-v1':'SERVICE','benign-bursty-v1':'BURSTY'}
for workload in acq['benign']['profiles']:
    for r in range(1,acq['benign']['repetitions_per_profile']+1): expected[f'BENIGN1-{short_b[workload]}-R{r:02d}']=(workload,'benign')
short_a={'ae-file-churn-v1':'FILE_CHURN','ae-process-chain-v1':'PROCESS_CHAIN','ae-loopback-beacon-v1':'LOOPBACK_BEACON','ae-staging-v1':'STAGING','ae-mixed-burst-v1':'MIXED_BURST'}
for workload in acq['attack_emulation']['profiles']:
    for r in range(1,acq['attack_emulation']['repetitions_per_profile']+1): expected[f'AE1-{short_a[workload]}-R{r:02d}']=(workload,'malicious')

found={}; host_fingerprints=set(); counts_by_workload=defaultdict(list)
for d in root.iterdir() if root.exists() else []:
    if not d.is_dir(): continue
    mp=d/'metadata.json'
    if not mp.exists(): continue
    try: m=json.loads(mp.read_text())
    except Exception: continue
    exp=str(m.get('experiment_id',''))
    if exp not in expected: continue
    if exp in found: errors.append(f'{exp}: duplicate eligible run directories'); continue
    found[exp]=d
    needed=['events.jsonl','metadata.json','stats.json','collector_stderr.log','workload_status.json']
    for fn in needed:
        if not (d/fn).is_file(): errors.append(f'{exp}: missing {fn}')
    try: s=json.loads((d/'stats.json').read_text()); w=json.loads((d/'workload_status.json').read_text())
    except Exception as e: errors.append(f'{exp}: status parse error {e}'); continue
    ew,el=expected[exp]
    checks={
      'schema_version':m.get('schema_version')==spec['schema_version'],
      'collector':m.get('collector')==spec['collector'],
      'capture_scope':m.get('capture_scope')==spec['capture_scope'],
      'raw_identifiers_persisted':m.get('raw_identifiers_persisted') is spec['raw_identifiers_persisted'],
      'workload_id':m.get('workload_id')==ew,
      'label':m.get('label')==el,
      'malformed_lines':int(s.get('malformed_lines',-1))==0,
      'collector_exit_code':int(s.get('exit_code',-1))==0,
      'workload_completed':w.get('workload_completed') is True,
      'workload_exit_code':int(w.get('workload_exit_code',-1))==0,
      'workload_duration_seconds':int(w.get('workload_duration_seconds',-1))==acq['workload_duration_seconds'],
      'rate_per_second':int(w.get('rate_per_second',-1))==acq['rate_per_second'],
      'workload_id_status':w.get('workload_id')==ew,
      'experiment_id_status':w.get('experiment_id')==exp,
    }
    for name,ok in checks.items():
        if not ok: errors.append(f'{exp}: {name} mismatch')
    host_fingerprints.add((m.get('os_pretty_name'),m.get('kernel_release'),m.get('architecture'),m.get('bpftrace_version')))
    counts_by_workload[ew].append(s.get('event_counts',{}))

for exp in expected:
    if exp not in found: errors.append(f'{exp}: missing expected run')
if len(host_fingerprints)>1: errors.append('run metadata contain more than one OS/kernel/architecture/bpftrace fingerprint on this host corpus')
if len(found)!=len(expected): errors.append(f'eligible expected runs={len(found)} expected={len(expected)}')

# Protocol records are mandatory and must match the frozen acquisition settings.
protocol_files=['CAL1_PROTOCOL.json','BENIGN1_PROTOCOL.json','ATTACK_EMULATION1_PROTOCOL.json','ATTACK_EMULATION1_SAFETY_GATE.json']
for fn in protocol_files:
    if not (root/fn).is_file(): errors.append('missing protocol evidence file '+fn)
try:
    calp=json.loads((root/'CAL1_PROTOCOL.json').read_text())
    if calp.get('protocol')!='CAL-1' or int(calp.get('repetitions',-1))!=acq['calibration']['repetitions'] or int(calp.get('duration_seconds',-1))!=acq['workload_duration_seconds'] or int(calp.get('base_rate_per_second',-1))!=acq['rate_per_second']: errors.append('CAL1_PROTOCOL.json settings mismatch')
except Exception as e: errors.append('CAL1_PROTOCOL.json parse/settings error: '+str(e))
try:
    bp=json.loads((root/'BENIGN1_PROTOCOL.json').read_text())
    if bp.get('protocol')!='BENIGN-1' or int(bp.get('repetitions_per_profile',-1))!=acq['benign']['repetitions_per_profile'] or int(bp.get('duration_seconds',-1))!=acq['workload_duration_seconds'] or int(bp.get('base_rate_per_second',-1))!=acq['rate_per_second'] or set(bp.get('profiles',[]))!=set(acq['benign']['profiles']): errors.append('BENIGN1_PROTOCOL.json settings/profile mismatch')
except Exception as e: errors.append('BENIGN1_PROTOCOL.json parse/settings error: '+str(e))
try:
    aprot=json.loads((root/'ATTACK_EMULATION1_PROTOCOL.json').read_text())
    if aprot.get('protocol')!='ATTACK-EMULATION-1' or int(aprot.get('repetitions_per_profile',-1))!=acq['attack_emulation']['repetitions_per_profile'] or int(aprot.get('duration_seconds',-1))!=acq['workload_duration_seconds'] or int(aprot.get('base_rate_per_second',-1))!=acq['rate_per_second'] or set(aprot.get('profiles',[]))!=set(acq['attack_emulation']['profiles']) or aprot.get('network_scope')!=acq['attack_emulation']['network_scope'] or aprot.get('filesystem_scope')!=acq['attack_emulation']['filesystem_scope']: errors.append('ATTACK_EMULATION1_PROTOCOL.json settings/profile/scope mismatch')
except Exception as e: errors.append('ATTACK_EMULATION1_PROTOCOL.json parse/settings error: '+str(e))
try:
    gate=json.loads((root/'ATTACK_EMULATION1_SAFETY_GATE.json').read_text())
    if gate.get('passed') is not True or gate.get('network_scope')!=acq['attack_emulation']['network_scope'] or gate.get('filesystem_scope')!=acq['attack_emulation']['filesystem_scope']: errors.append('ATTACK_EMULATION1_SAFETY_GATE.json mismatch/failure')
except Exception as e: errors.append('ATTACK_EMULATION1_SAFETY_GATE.json parse/settings error: '+str(e))

# Repeatability is reported, not a universal pass/fail requirement; exact counts can legitimately differ slightly on other systems.
repeatability={}
for workload,seq in counts_by_workload.items():
    canonical=[json.dumps(x,sort_keys=True) for x in seq]
    repeatability[workload]={'runs':len(seq),'identical_event_counts':len(set(canonical))<=1}

report={
 'validation':'XEBPF-HOST-REPRODUCTION', 'host_label':a.host_label, 'passed':not errors,
 'expected_runs':len(expected),'found_runs':len(found),'host_fingerprint':list(next(iter(host_fingerprints))) if len(host_fingerprints)==1 else None,
 'repeatability_observation':repeatability,'errors':errors,'warnings':warnings,
 'protocol_alignment':{
   'schema_version':spec['schema_version'],'collector':spec['collector'],'capture_scope':spec['capture_scope'],
   'workload_duration_seconds':acq['workload_duration_seconds'],'rate_per_second':acq['rate_per_second'],
   'calibration_runs':acq['calibration']['repetitions'],
   'classification_runs':len(acq['benign']['profiles'])*acq['benign']['repetitions_per_profile']+len(acq['attack_emulation']['profiles'])*acq['attack_emulation']['repetitions_per_profile']
 }
}
print('XEBPF HOST REPRODUCTION VALIDATION')
print('Host label:',a.host_label)
if report['host_fingerprint']: print('Environment:', ' | '.join(str(x) for x in report['host_fingerprint']))
print(f'Expected runs: {len(expected)}  Found: {len(found)}')
print('CAL-1:', 'PASS' if all(f'CAL1-R{i:02d}' in found for i in range(1,6)) else 'FAIL')
print('BENIGN-1:', 'PASS' if sum(1 for x in found if x.startswith('BENIGN1-'))==15 else 'FAIL')
print('ATTACK-EMULATION-1:', 'PASS' if sum(1 for x in found if x.startswith('AE1-'))==15 else 'FAIL')
print('Protocol files:', 'PASS' if all((root/f).is_file() for f in ['CAL1_PROTOCOL.json','BENIGN1_PROTOCOL.json','ATTACK_EMULATION1_PROTOCOL.json','ATTACK_EMULATION1_SAFETY_GATE.json']) else 'FAIL')
print('RESULT:', 'PASS' if not errors else 'FAIL')
if errors:
    for e in errors: print(' - '+e)
if a.report_prefix:
    p=Path(a.report_prefix); p.parent.mkdir(parents=True,exist_ok=True)
    Path(str(p)+'.json').write_text(json.dumps(report,indent=2)+'\n')
    lines=['XEBPF HOST REPRODUCTION VALIDATION',f'host_label={a.host_label}',f'passed={report["passed"]}',f'expected_runs={len(expected)}',f'found_runs={len(found)}']
    for e in errors: lines.append('ERROR: '+e)
    Path(str(p)+'.txt').write_text('\n'.join(lines)+'\n')
if errors: sys.exit(2)
