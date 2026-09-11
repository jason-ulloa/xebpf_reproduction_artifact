#!/usr/bin/env python3
import argparse, socket, subprocess, tempfile, threading, time
from pathlib import Path
ap=argparse.ArgumentParser(description='XEBPF BENIGN-1 controlled workloads')
ap.add_argument('--profile',required=True,choices=['benign-file-v1','benign-process-v1','benign-network-v1','benign-service-v1','benign-bursty-v1'])
ap.add_argument('--duration',type=int,default=120)
ap.add_argument('--rate',type=int,default=4)
a=ap.parse_args()
if a.duration<1 or a.rate<1: raise SystemExit('duration and rate must be >=1')
root=Path(tempfile.mkdtemp(prefix='xebpf-benign1-')); stop=threading.Event(); ready=threading.Event(); ph=[]
def server():
 s=socket.socket(socket.AF_INET,socket.SOCK_STREAM); s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1); s.bind(('127.0.0.1',0)); s.listen(128); s.settimeout(.2); ph.append(s.getsockname()[1]); ready.set()
 while not stop.is_set():
  try:
   c,_=s.accept()
   try: c.recv(64)
   except Exception: pass
   c.close()
  except socket.timeout: pass
 s.close()
def file_cycle(seq,width=4):
 p=root/('f%04d.dat'%(seq%64))
 with p.open('w') as f:
  for i in range(width): f.write('xebpf-benign1-%d-%d\n'%(seq,i))
 for _ in range(2):
  with p.open('r') as f: f.read()
 with p.open('a') as f: f.write('tail\n')
 try: p.unlink()
 except FileNotFoundError: pass
def process_cycle(count=2):
 for _ in range(count): subprocess.run(['/bin/true'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=False)
def network_cycle(port,count=2):
 for _ in range(count):
  c=socket.socket(socket.AF_INET,socket.SOCK_STREAM); c.settimeout(1)
  try: c.connect(('127.0.0.1',port)); c.sendall(b'x')
  finally: c.close()
t=threading.Thread(target=server,daemon=True); t.start(); ready.wait(5)
if not ph: raise SystemExit('local TCP server failed to start')
port=ph[0]; period=1.0/float(a.rate); end=time.monotonic()+a.duration; nxt=time.monotonic(); seq=0
try:
 while time.monotonic()<end:
  p=a.profile
  if p=='benign-file-v1':
   file_cycle(seq,8)
   if seq%4==0: process_cycle(1)
   if seq%5==0: network_cycle(port,1)
  elif p=='benign-process-v1':
   process_cycle(3)
   if seq%3==0: file_cycle(seq,2)
   if seq%5==0: network_cycle(port,1)
  elif p=='benign-network-v1':
   network_cycle(port,3)
   if seq%3==0: file_cycle(seq,2)
   if seq%6==0: process_cycle(1)
  elif p=='benign-service-v1':
   file_cycle(seq,3); network_cycle(port,1)
   if seq%4==0: process_cycle(1)
  elif p=='benign-bursty-v1':
   phase=seq%8
   if phase<4: file_cycle(seq,4); process_cycle(2); network_cycle(port,2)
   elif phase==4: file_cycle(seq,1)
  seq+=1; nxt+=period; delay=nxt-time.monotonic()
  if delay>0: time.sleep(delay)
finally:
 stop.set(); t.join(timeout=2)
 for p in root.glob('*'):
  try: p.unlink()
  except Exception: pass
 try: root.rmdir()
 except Exception: pass
print('profile=%s cycles=%d duration=%d rate=%d'%(a.profile,seq,a.duration,a.rate))
