#!/usr/bin/env python3
import argparse, json, math
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

def featurize(df, window_s, duration_s=120.0):
    """Create only complete analysis windows inside the frozen workload interval.

    The collector intentionally runs longer than the workload. The original paper corpus
    used exactly floor(120/window_s) complete windows per run (24 at 5 s), so any partial
    trailing collector-margin window is excluded here.
    """
    if df.empty:
        return pd.DataFrame()
    if window_s <= 0 or duration_s <= 0:
        raise ValueError("window and duration must be positive")
    n_full=int(math.floor(duration_s/window_s + 1e-12))
    if n_full < 1:
        raise ValueError("window is longer than the analysis duration")
    t0=df.ts.min()
    df=df.copy()
    df["window"]=np.floor((df.ts-t0)/window_s).astype(int)
    df=df[(df.window>=0)&(df.window<n_full)]
    # Materialize every complete window, including a zero vector if a reproducer's
    # workload happens to emit no observed event in a particular bin. The original
    # corpus had at least one event in every complete bin, so this is behaviorally
    # neutral for the frozen analyses while making the protocol deterministic on
    # new systems.
    groups={int(w):g for w,g in df.groupby("window", sort=True)}
    out=[]
    for w in range(n_full):
        g=groups.get(w)
        if g is None or g.empty:
            r={"window":w,"total_events":0,"unique_pids":0,
               "interarrival_mean":0.0,"interarrival_std":0.0,"interarrival_p50":0.0}
            for e in EVENTS:
                r[e]=0; r[e+"_ratio"]=0.0
            out.append(r)
            continue
        g=g.sort_values("ts")
        inter=np.diff(g.ts.to_numpy())
        n=len(g)
        r={"window":w,"total_events":n,"unique_pids":int(g.pid.nunique())}
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
    ap.add_argument("--duration", type=float, default=120.0,
                    help="Frozen workload-analysis duration; trailing collector-margin windows are excluded")
    ap.add_argument("--output", required=True)
    a=ap.parse_args()
    m=pd.read_csv(a.manifest)
    required={"host","workload","label","rep","events_jsonl"}
    miss=required-set(m.columns)
    if miss: raise SystemExit(f"Missing manifest columns: {sorted(miss)}")
    all_rows=[]
    expected_per_run=int(math.floor(a.duration/a.window + 1e-12))
    errors=[]
    for _,row in m.iterrows():
        f=featurize(load_events(row.events_jsonl), a.window, a.duration)
        if len(f)!=expected_per_run:
            errors.append(f"{row.host}/{row.workload}/R{int(row.rep):02d}: expected {expected_per_run} full windows, found {len(f)}")
            continue
        for k in ["host","workload","label","rep"]:
            f[k]=row[k]
        cols=["host","workload","label","rep","window"]+[c for c in f.columns if c not in {"host","workload","label","rep","window"}]
        all_rows.append(f[cols])
    if errors:
        raise SystemExit("Feature extraction protocol mismatch:\n - "+"\n - ".join(errors))
    out=pd.concat(all_rows, ignore_index=True) if all_rows else pd.DataFrame()
    out.to_csv(a.output,index=False)
    print(f"Wrote {len(out)} windows to {a.output} ({expected_per_run} complete windows/run)")

if __name__=="__main__": main()
