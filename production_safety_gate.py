#!/usr/bin/env python3
import argparse, json, os, pwd, socket, shutil, stat, sys, tempfile, time
from pathlib import Path
ap=argparse.ArgumentParser(description='Production Safety Gate for XEBPF ATTACK-EMULATION-1')
ap.add_argument('--user',default='xebpfexp')
ap.add_argument('--duration',type=int,default=120)
ap.add_argument('--rate',type=int,default=4)
ap.add_argument('--hmac-key-path',required=True)
ap.add_argument('--report',default=None)
a=ap.parse_args(); errors=[]; checks={}
try:
    pw=pwd.getpwnam(a.user); checks['experiment_user_exists']=True
except KeyError:
    errors.append('experiment user does not exist'); pw=None; checks['experiment_user_exists']=False
checks['experiment_user_non_root']=bool(pw and pw.pw_uid!=0)
if pw and pw.pw_uid==0: errors.append('experiment user must not be root')
checks['duration_within_1_300']=1 <= a.duration <= 300
if not checks['duration_within_1_300']: errors.append('duration must be 1..300 seconds')
checks['rate_within_1_10']=1 <= a.rate <= 10
if not checks['rate_within_1_10']: errors.append('rate must be 1..10 cycles/s')
checks['hmac_key_exists']=os.path.isfile(a.hmac_key_path)
if not checks['hmac_key_exists']: errors.append('missing HMAC key file')
else:
    mode=stat.S_IMODE(os.stat(a.hmac_key_path).st_mode); checks['hmac_key_restrictive_permissions']=(mode & 0o077)==0
    if not checks['hmac_key_restrictive_permissions']: errors.append('HMAC key permissions are too broad')
try:
    usage=shutil.disk_usage('/tmp'); checks['tmp_free_at_least_256MiB']=usage.free >= 256*1024*1024
    if not checks['tmp_free_at_least_256MiB']: errors.append('/tmp has less than 256 MiB free')
except Exception as e: errors.append('cannot check /tmp: %s'%e); checks['tmp_free_at_least_256MiB']=False
try:
    s=socket.socket(socket.AF_INET,socket.SOCK_STREAM); s.bind(('127.0.0.1',0)); s.close(); checks['loopback_bind']=True
except Exception as e: errors.append('loopback bind failed: %s'%e); checks['loopback_bind']=False
try:
    d=tempfile.mkdtemp(prefix='xebpf-ae1-gate-',dir='/tmp'); os.rmdir(d); checks['isolated_tmp_create_remove']=True
except Exception as e: errors.append('cannot create/remove isolated /tmp workspace: %s'%e); checks['isolated_tmp_create_remove']=False
obj={'gate':'ATTACK-EMULATION-1','passed':not errors,'user':a.user,'uid':pw.pw_uid if pw else None,'duration_seconds':a.duration,'rate_per_second':a.rate,'network_scope':'127.0.0.1 only','filesystem_scope':'isolated /tmp/xebpf-ae1-* only','checks':checks,'errors':errors,'recorded_at_epoch':time.time()}
if a.report:
    p=Path(a.report); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(obj,indent=2)+'\n'); os.chmod(p,0o600)
if errors:
    print('PRODUCTION SAFETY GATE: FAIL')
    for e in errors: print(' - '+e)
    sys.exit(2)
print('PRODUCTION SAFETY GATE: PASS')
print('user=%s uid=%s duration=%ss rate=%s/s scope=/tmp + 127.0.0.1 only'%(a.user,pw.pw_uid if pw else '?',a.duration,a.rate))
