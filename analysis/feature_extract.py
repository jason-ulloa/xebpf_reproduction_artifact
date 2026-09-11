#!/usr/bin/env python3
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd

EVENTS = ["FILE_OPEN","NET_ACCEPT","NET_CONNECT","PROCESS_EXEC","PROCESS_EXIT"]

def load_events(path):
    rows=[]
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                x=json.loads(line)
                rows.append({
                    "event_type": x["event_type"],
                    "ts": int(x["timestamp_monotonic_ns"])/1e9,
                    "pid": int(x["pid"]),
                })
    return pd.DataFrame(rows)

def featurize(df, window_s):
    if df.empty:
        return pd.DataFrame()
    t0=df.ts.min()
    df=df.copy()
    df["window"]=np.floor((df.ts-t0)/window_s).astype(int)
    out=[]
    for w,g in df.groupby("window", sort=True):
        g=g.sort_values("ts")
        inter=np.diff(g.ts.to_numpy())
        n=len(g)
        r={"window":int(w),"total_events":n,"unique_pids":int(g.pid.nunique())}
        r["interarrival_mean"]=float(inter.mean()) if len(inter) else 0.0
        r["interarrival_std"]=float(inter.std(ddof=0)) if len(inter) else 0.0
        r["interarrival_p50"]=float(np.median(inter)) if len(inter) else 0.0
        vc=g.event_type.value_counts()
        for e in EVENTS:
            c=int(vc.get(e,0))
            r[e]=c
            r[e+"_ratio"]=c/n if n else 0.0
        out.append(r)
    return pd.DataFrame(out)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--window", type=float, default=5.0)
    ap.add_argument("--output", required=True)
    a=ap.parse_args()
    m=pd.read_csv(a.manifest)
    required={"host","workload","label","rep","events_jsonl"}
    miss=required-set(m.columns)
    if miss: raise SystemExit(f"Missing manifest columns: {sorted(miss)}")
    all_rows=[]
    for _,row in m.iterrows():
        f=featurize(load_events(row.events_jsonl), a.window)
        if f.empty: continue
        for k in ["host","workload","label","rep"]:
            f.insert(len([x for x in ["host","workload","label","rep"] if x in f.columns]), k, row[k])
        # force canonical metadata order
        cols=["host","workload","label","rep","window"]+[c for c in f.columns if c not in {"host","workload","label","rep","window"}]
        all_rows.append(f[cols])
    out=pd.concat(all_rows, ignore_index=True) if all_rows else pd.DataFrame()
    out.to_csv(a.output,index=False)
    print(f"Wrote {len(out)} windows to {a.output}")

if __name__=="__main__": main()
