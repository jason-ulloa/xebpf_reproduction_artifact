#!/usr/bin/env python3
import json, sys
from pathlib import Path
errors=[]
root=Path(__file__).resolve().parents[1]
print('XEBPF ANALYSIS ENVIRONMENT CHECK')
print('Artifact root:',root)
try:
 import numpy, pandas, sklearn, scipy
 mods=[('numpy',numpy.__version__),('pandas',pandas.__version__),('scikit-learn',sklearn.__version__),('scipy',scipy.__version__)]
 for n,v in mods: print(f'{n}: {v} PASS')
except Exception as e: errors.append('analysis dependency import failed: '+str(e))
try:
 spec=json.loads((root/'protocol_spec.json').read_text())
 if spec.get('artifact_protocol')!='xebpf-paper-protocol-v1': errors.append('protocol_spec artifact_protocol mismatch')
 else: print('protocol_spec.json: PASS')
except Exception as e: errors.append('protocol_spec.json unreadable: '+str(e))
print('Python:',sys.executable)
print('RESULT:','PASS' if not errors else 'FAIL')
for e in errors: print(' - '+e)
if errors: sys.exit(2)
