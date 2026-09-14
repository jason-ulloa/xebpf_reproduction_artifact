#!/usr/bin/env python3
import argparse, re, sys
from pathlib import Path
ap=argparse.ArgumentParser(description='Public-artifact confidentiality hygiene scan (heuristic, not a legal guarantee)')
ap.add_argument('--root',default=str(Path(__file__).resolve().parent)); a=ap.parse_args(); root=Path(a.root); issues=[]
forbidden_suffix={'.jsonl','.db','.zst','.key','.pem','.pcap','.pcapng'}
allowed_json={'protocol_spec.json','FILE_MANIFEST_SHA256.json','.zenodo.json'}
private_ip=re.compile(r'(?<!\d)(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})(?!\d)')
for p in root.rglob('*'):
 if not p.is_file(): continue
 rel=str(p.relative_to(root))
 if any(part in {'.git','.venv-analysis','__pycache__'} for part in p.parts): continue
 if p.suffix.lower() in forbidden_suffix: issues.append(f'forbidden data/secret-like file type: {rel}')
 try: text=p.read_text(errors='ignore')
 except Exception: continue
 if private_ip.search(text): issues.append(f'private RFC1918 IPv4 literal found: {rel}')
 forbidden_key_path='/'+'etc'+'/'+'ebpf-research'+'/'+'anonymization'+'.key'
 if forbidden_key_path in text: issues.append(f'original infrastructure-specific key path found: {rel}')
 if 'events.jsonl' in rel.lower(): issues.append(f'event telemetry file present: {rel}')
print('XEBPF PUBLIC ARTIFACT CONFIDENTIALITY AUDIT'); print('RESULT:','PASS' if not issues else 'FAIL')
for x in issues: print(' - '+x)
if issues: sys.exit(2)
