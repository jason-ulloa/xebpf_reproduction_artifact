#!/usr/bin/env python3
import argparse, json, os, platform, shutil, subprocess, sys
from pathlib import Path

ap=argparse.ArgumentParser(description='Validate current Linux environment prerequisites for XEBPF acquisition')
ap.add_argument('--protocol-spec',default=str(Path(__file__).with_name('protocol_spec.json')))
ap.add_argument('--output',default=None)
a=ap.parse_args(); spec=json.loads(Path(a.protocol_spec).read_text()); errors=[]

def version(cmd):
    try:
        p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=10)
        return (p.stdout or '').strip(),p.returncode
    except Exception as e: return str(e),127

bt,brc=version(['bpftrace','--version']) if shutil.which('bpftrace') else ('not installed',127)
py,prc=version(['python3','--version']) if shutil.which('python3') else ('not installed',127)
if brc!=0: errors.append('bpftrace unavailable')
if prc!=0: errors.append('python3 unavailable')
tracepoints={}
for tp in spec['required_tracepoints']:
    ok=Path('/sys/kernel/tracing/events',tp).is_dir()
    tracepoints[tp]=ok
    if not ok: errors.append('missing tracepoint '+tp)
obj={
  'validation':'XEBPF-ENVIRONMENT',
  'passed':not errors,
  'os_pretty_name':'unknown',
  'kernel_release':platform.release(),
  'architecture':platform.machine(),
  'python_version':py,
  'bpftrace_version':bt,
  'required_tracepoints':tracepoints,
  'errors':errors,
}
try:
    for line in Path('/etc/os-release').read_text().splitlines():
        if line.startswith('PRETTY_NAME='): obj['os_pretty_name']=line.split('=',1)[1].strip().strip('"')
except Exception: pass
print('XEBPF ENVIRONMENT VALIDATION')
print('OS:',obj['os_pretty_name']); print('Kernel:',obj['kernel_release']); print('Architecture:',obj['architecture'])
print('Python:',py); print('bpftrace:',bt)
for tp,ok in tracepoints.items(): print(('PASS' if ok else 'FAIL'),tp)
print('RESULT:', 'PASS' if not errors else 'FAIL')
if a.output:
    p=Path(a.output); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(obj,indent=2)+'\n')
if errors: sys.exit(2)
