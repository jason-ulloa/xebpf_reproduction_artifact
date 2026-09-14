#!/usr/bin/env python3
import argparse, hashlib, json, py_compile, subprocess, sys
from pathlib import Path
ap=argparse.ArgumentParser(description='Static integrity/self-consistency validation for the XEBPF artifact')
ap.add_argument('--root',default=str(Path(__file__).resolve().parent)); a=ap.parse_args(); root=Path(a.root); errors=[]
required=['README.md','RELEASE_NOTES.md','VERSION','CITATION.cff','.zenodo.json','protocol_spec.json','collector.py','collector.bt','controlled_workload.py','benign_workloads.py','attack_emulation_workloads.py','production_safety_gate.py','run_calibration.sh','run_benign1.sh','run_attack_emulation1.sh','validate_environment.py','validate_calibration1.py','validate_benign1.py','validate_attack_emulation1.py','validate_host_reproduction.py','analysis/feature_extract.py','analysis/model1.py','analysis/shift_decomposition.py','analysis/window_sensitivity.py','analysis/feature_ablation.py','analysis/environment_shift.py','analysis/generate_manifest.py','analysis/merge_manifests.py','analysis/run_analysis_pipeline.py','analysis/validate_analysis_reproduction.py','analysis/check_analysis_environment.py','analysis/summarize_reproduction.py','external_validation/run_external_validation.sh','external_validation/validate_external_validation.py','run_controlled_acquisition.sh','confidentiality_audit.py']
for f in required:
 if not (root/f).is_file(): errors.append('missing required file '+f)
try:
 spec=json.loads((root/'protocol_spec.json').read_text())
 if spec.get('schema_version')!='xebpf-1.3.2': errors.append('protocol_spec schema mismatch')
 if spec.get('collector')!='bpftrace-common-v1.3.2': errors.append('protocol_spec collector mismatch')
 if spec.get('features',{}).get('analysis_duration_seconds')!=120 or spec.get('features',{}).get('complete_windows_only') is not True: errors.append('protocol_spec complete-window rule mismatch')
 expected_rf={'rf_model1':400,'rf_shift_decomposition':20,'rf_window_sensitivity':20,'rf_feature_ablation_sensitivity':5}
 for k,v in expected_rf.items():
  if spec.get('models',{}).get(k,{}).get('n_estimators')!=v: errors.append(f'protocol_spec {k} tree count mismatch')
 if spec.get('models',{}).get('bootstrap',{}).get('iterations')!=5000: errors.append('protocol_spec bootstrap iteration mismatch')
 if spec.get('models',{}).get('lr',{}).get('standardize') is not True: errors.append('protocol_spec LR standardization mismatch')
except Exception as e: errors.append('protocol_spec invalid: '+str(e))
for p in root.rglob('*.py'):
 try: py_compile.compile(str(p),doraise=True)
 except Exception as e: errors.append(f'Python compile failure {p.relative_to(root)}: {e}')
for p in root.rglob('*.sh'):
 rc=subprocess.run(['bash','-n',str(p)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 if rc.returncode: errors.append(f'Bash syntax failure {p.relative_to(root)}: {rc.stderr.strip()}')

# Verify the release file manifest when present. The manifest intentionally excludes itself.
manifest_path=root/'FILE_MANIFEST_SHA256.json'
if not manifest_path.is_file():
 errors.append('missing FILE_MANIFEST_SHA256.json')
else:
 try:
  manifest=json.loads(manifest_path.read_text())
  for rel,expected_hash in manifest.items():
   fp=root/rel
   if not fp.is_file(): errors.append('manifest-listed file missing '+rel); continue
   actual=hashlib.sha256(fp.read_bytes()).hexdigest()
   if actual!=expected_hash: errors.append('SHA-256 mismatch '+rel)
  actual_files={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and p.name!='FILE_MANIFEST_SHA256.json' and '__pycache__' not in p.parts}
  listed=set(manifest)
  extra=sorted(actual_files-listed)
  missing=sorted(listed-actual_files)
  if extra: errors.append('files absent from manifest: '+','.join(extra))
  if missing: errors.append('manifest entries absent from artifact: '+','.join(missing))
 except Exception as e: errors.append('FILE_MANIFEST_SHA256.json invalid: '+str(e))

version=(root/'VERSION').read_text().strip() if (root/'VERSION').exists() else ''
if version!='1.0.1': errors.append('VERSION is not 1.0.1')
print('XEBPF ARTIFACT VALIDATION'); print('Required files:',len(required)); print('RESULT:','PASS' if not errors else 'FAIL')
for e in errors: print(' - '+e)
if errors: sys.exit(2)
