#!/usr/bin/env python3
"""Safe behavioral emulation only. No exploits, malware, external networking, privilege changes, or production-file access."""
import argparse, hashlib, os, shutil, socket, subprocess, tempfile, threading, time
from pathlib import Path
PROFILES=['ae-file-churn-v1','ae-process-chain-v1','ae-loopback-beacon-v1','ae-staging-v1','ae-mixed-burst-v1']
ap=argparse.ArgumentParser(description='XEBPF ATTACK-EMULATION-1 safe workloads')
ap.add_argument('--profile',required=True,choices=PROFILES)
ap.add_argument('--duration',type=int,default=120)
ap.add_argument('--rate',type=int,default=4)
a=ap.parse_args()
if not (1 <= a.duration <= 300): raise SystemExit('duration must be 1..300')
if not (1 <= a.rate <= 10): raise SystemExit('rate must be 1..10')
root=Path(tempfile.mkdtemp(prefix='xebpf-ae1-',dir='/tmp')).resolve()
# Fail closed: workspace must be a real /tmp/xebpf-ae1-* directory.
if root.parent != Path('/tmp') or not root.name.startswith('xebpf-ae1-') or root.is_symlink():
    raise SystemExit('unsafe workspace; refusing to run')
stop=threading.Event(); ready=threading.Event(); ports=[]
def server():
    s=socket.socket(socket.AF_INET,socket.SOCK_STREAM); s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
    s.bind(('127.0.0.1',0)); s.listen(64); s.settimeout(.2); ports.append(s.getsockname()[1]); ready.set()
    while not stop.is_set():
        try:
            c,_=s.accept(); c.settimeout(.2)
            try: c.recv(128)
            except Exception: pass
            c.close()
        except socket.timeout: pass
    s.close()
def local_connect(port,count=1):
    for _ in range(count):
        c=socket.socket(socket.AF_INET,socket.SOCK_STREAM); c.settimeout(.5)
        try: c.connect(('127.0.0.1',port)); c.sendall(b'ae1')
        finally: c.close()
def exec_true(count=1):
    for _ in range(count): subprocess.run(['/bin/true'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=False)
def safe_unlink(path):
    # Python <3.8 compatible replacement for Path.unlink(missing_ok=True).
    try:
        path.unlink()
    except FileNotFoundError:
        pass

def make_file(idx,size=512):
    p=root/('sample-%03d.dat'%(idx%96)); data=(('AE1-%d-'%idx).encode()*128)[:size]
    with p.open('wb') as f: f.write(data)
    return p
def read_transform_delete(idx):
    p=make_file(idx,768)
    with p.open('rb') as f: data=f.read()
    # In-memory reversible transformation on experiment-owned bytes only.
    out=root/('derived-%03d.bin'%(idx%96))
    with out.open('wb') as f: f.write(bytes((b ^ 0x5A) for b in data))
    with out.open('rb') as f: hashlib.sha256(f.read()).digest()
    safe_unlink(p); safe_unlink(out)
def staging_cycle(idx):
    src=make_file(idx,1024); stage=root/('stage-%03d.tmp'%(idx%96))
    shutil.copyfile(str(src),str(stage))
    with stage.open('rb') as f: hashlib.sha256(f.read()).digest()
    exec_true(1)
    safe_unlink(src); safe_unlink(stage)
t=threading.Thread(target=server,daemon=True); t.start(); ready.wait(5)
if not ports: raise SystemExit('loopback server failed')
port=ports[0]; period=1.0/a.rate; end=time.monotonic()+a.duration; nxt=time.monotonic(); seq=0
try:
    while time.monotonic()<end:
        if a.profile=='ae-file-churn-v1':
            read_transform_delete(seq)
            if seq%3==0: exec_true(1)
            if seq%5==0: local_connect(port,1)
        elif a.profile=='ae-process-chain-v1':
            exec_true(4)
            if seq%2==0: safe_unlink(make_file(seq,256))
            if seq%4==0: local_connect(port,1)
        elif a.profile=='ae-loopback-beacon-v1':
            local_connect(port,2 if seq%4 else 4)
            if seq%3==0: exec_true(1)
            if seq%5==0: safe_unlink(make_file(seq,384))
        elif a.profile=='ae-staging-v1':
            staging_cycle(seq)
            if seq%2==0: local_connect(port,1)
        elif a.profile=='ae-mixed-burst-v1':
            phase=seq%10
            if phase<3:
                read_transform_delete(seq); exec_true(3); local_connect(port,2)
            elif phase<6:
                staging_cycle(seq); local_connect(port,1)
            else:
                exec_true(1)
        seq+=1; nxt+=period; delay=nxt-time.monotonic()
        if delay>0: time.sleep(delay)
finally:
    stop.set(); t.join(timeout=2)
    # Cleanup is restricted to the isolated workspace created above.
    if root.exists() and root.parent==Path('/tmp') and root.name.startswith('xebpf-ae1-'):
        shutil.rmtree(str(root),ignore_errors=True)
print('profile=%s cycles=%d duration=%d rate=%d workspace_cleaned=yes'%(a.profile,seq,a.duration,a.rate))
