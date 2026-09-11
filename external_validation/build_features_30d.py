#!/usr/bin/env python3
import sqlite3,json,argparse,csv
from pathlib import Path
from datetime import datetime

EVENTS=["PROCESS_EXEC","PROCESS_EXIT","NET_CONNECT","NET_ACCEPT","FILE_OPEN","FILE_DELETE",
        "PROCESS_OTHER","NET_OTHER","FILE_OTHER"]

def parse_ts(s):
    if s.endswith("Z"): s=s[:-1]+"+00:00"
    return datetime.fromisoformat(s).timestamp()

def semantic_event(source, parsed_json):
    try: p=json.loads(parsed_json) if parsed_json else {}
    except Exception: p={}
    e=str(p.get("event_type","")).lower()
    if source=="ebpf_process":
        if "exec" in e:return "PROCESS_EXEC"
        if "exit" in e:return "PROCESS_EXIT"
        return "PROCESS_OTHER"
    if source=="ebpf_network":
        if "accept" in e:return "NET_ACCEPT"
        if "connect" in e:return "NET_CONNECT"
        return "NET_OTHER"
    if source=="ebpf_file":
        if "unlink" in e or "delete" in e:return "FILE_DELETE"
        if "open" in e:return "FILE_OPEN"
        return "FILE_OTHER"
    return None

def emit(window, writer):
    total=sum(window["counts"].values())
    row={"window_epoch":window["epoch"],"label":int(window["malicious"]),
         "attack_families":"|".join(sorted(window["families"])),
         "n_attack_families":len(window["families"]),"total_events":total}
    for e in EVENTS:
        c=window["counts"].get(e,0)
        row[e]=c
        row[e+"_ratio"]=c/total if total else 0.0
    writer.writerow(row)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--db",required=True)
    ap.add_argument("--window",type=int,default=5)
    ap.add_argument("--out",required=True)
    a=ap.parse_args()
    Path(a.out).parent.mkdir(parents=True,exist_ok=True)

    con=sqlite3.connect(a.db)
    cur=con.cursor()
    cur.execute("""SELECT timestamp,source,is_malicious,attack_type,parsed FROM events
                   WHERE source IN ('ebpf_process','ebpf_network','ebpf_file')
                     AND is_malicious IN (0,1)
                   ORDER BY timestamp,id""")

    cols=["window_epoch","label","attack_families","n_attack_families","total_events"]
    for e in EVENTS: cols += [e,e+"_ratio"]

    n=bad=nwindows=0
    current=None
    with open(a.out,"w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=cols); writer.writeheader()
        while True:
            rows=cur.fetchmany(50000)
            if not rows: break
            for ts,src,mal,atype,pj in rows:
                n+=1
                try: epoch=int(parse_ts(ts)//a.window)*a.window
                except Exception:
                    bad+=1; continue
                if current is None:
                    current={"epoch":epoch,"counts":{},"malicious":False,"families":set()}
                elif epoch!=current["epoch"]:
                    emit(current,writer); nwindows+=1
                    current={"epoch":epoch,"counts":{},"malicious":False,"families":set()}
                event=semantic_event(src,pj)
                if event:
                    current["counts"][event]=current["counts"].get(event,0)+1
                if mal:
                    current["malicious"]=True
                    if atype: current["families"].add(str(atype))
        if current is not None:
            emit(current,writer); nwindows+=1
    con.close()

    print("eBPF events:",n,"timestamp parse failures:",bad,"windows:",nwindows)
    if bad>max(100,n*.001): raise SystemExit("TIMESTAMP GATE: FAIL")
    if nwindows<10000: raise SystemExit("WINDOW GATE: FAIL")
    print("FEATURE EXTRACTION GATE: PASS")
if __name__=="__main__": main()
