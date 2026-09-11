#!/usr/bin/env python3
import argparse, os, pwd, socket, shutil, stat, sys, tempfile
ap=argparse.ArgumentParser(description='Production Safety Gate for XEBPF ATTACK-EMULATION-1')
ap.add_argument('--user',default='xebpfexp')
ap.add_argument('--duration',type=int,default=120)
ap.add_argument('--rate',type=int,default=4)
ap.add_argument('--hmac-key-path',required=True)
a=ap.parse_args()
errors=[]
try:
    pw=pwd.getpwnam(a.user)
except KeyError:
    errors.append('experiment user does not exist'); pw=None
if pw and pw.pw_uid==0: errors.append('experiment user must not be root')
if a.duration < 1 or a.duration > 300: errors.append('duration must be 1..300 seconds')
if a.rate < 1 or a.rate > 10: errors.append('rate must be 1..10 cycles/s')
if not os.path.isfile(a.hmac_key_path): errors.append('missing HMAC key file')
else:
    mode=stat.S_IMODE(os.stat(a.hmac_key_path).st_mode)
    if mode & 0o077: errors.append('HMAC key permissions are too broad')
try:
    usage=shutil.disk_usage('/tmp')
    if usage.free < 256*1024*1024: errors.append('/tmp has less than 256 MiB free')
except Exception as e: errors.append('cannot check /tmp: %s'%e)
try:
    s=socket.socket(socket.AF_INET,socket.SOCK_STREAM); s.bind(('127.0.0.1',0)); s.close()
except Exception as e: errors.append('loopback bind failed: %s'%e)
try:
    d=tempfile.mkdtemp(prefix='xebpf-ae1-gate-',dir='/tmp'); os.rmdir(d)
except Exception as e: errors.append('cannot create/remove isolated /tmp workspace: %s'%e)
if errors:
    print('PRODUCTION SAFETY GATE: FAIL')
    for e in errors: print(' - '+e)
    sys.exit(2)
print('PRODUCTION SAFETY GATE: PASS')
print('user=%s uid=%s duration=%ss rate=%s/s scope=/tmp + 127.0.0.1 only'%(a.user,pw.pw_uid if pw else '?',a.duration,a.rate))
