#!/usr/bin/env python3
import argparse, os, socket, subprocess, tempfile, threading, time
from pathlib import Path

ap = argparse.ArgumentParser(description='Deterministic benign workload for XEBPF calibration')
ap.add_argument('--duration', type=int, default=120)
ap.add_argument('--rate', type=int, default=4, help='cycles per second')
args = ap.parse_args()

root = Path(tempfile.mkdtemp(prefix='xebpf-cal-'))
stop = threading.Event()
server_ready = threading.Event()
port_holder = []

def server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('127.0.0.1', 0))
    s.listen(64)
    s.settimeout(0.2)
    port_holder.append(s.getsockname()[1])
    server_ready.set()
    while not stop.is_set():
        try:
            c, _ = s.accept()
            try:
                c.recv(16)
            except Exception:
                pass
            c.close()
        except socket.timeout:
            pass
    s.close()

t = threading.Thread(target=server, daemon=True)
t.start(); server_ready.wait(5)
if not port_holder:
    raise SystemExit('local TCP server failed to start')
port = port_holder[0]

period = 1.0 / max(1, args.rate)
end = time.monotonic() + args.duration
seq = 0
next_tick = time.monotonic()
try:
    while time.monotonic() < end:
        p = root / ('f%04d.tmp' % (seq % 32))
        with p.open('w') as f:
            f.write('xebpf-calibration-%d\n' % seq)
        with p.open('r') as f:
            f.read()
        try:
            p.unlink()
        except FileNotFoundError:
            pass
        subprocess.run(['/bin/true'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        c.settimeout(1)
        try:
            c.connect(('127.0.0.1', port)); c.sendall(b'x')
        finally:
            c.close()
        seq += 1
        next_tick += period
        delay = next_tick - time.monotonic()
        if delay > 0:
            time.sleep(delay)
finally:
    stop.set(); t.join(timeout=2)
    for p in root.glob('*'):
        try: p.unlink()
        except Exception: pass
    try: root.rmdir()
    except Exception: pass
print('cycles=%d duration=%d rate=%d' % (seq, args.duration, args.rate))
