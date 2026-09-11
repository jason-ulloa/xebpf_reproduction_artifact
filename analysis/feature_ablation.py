#!/usr/bin/env python3
import argparse, tempfile, pandas as pd, subprocess, sys
from pathlib import Path
SETS={
 "counts_only":["total_events","unique_pids","FILE_OPEN","NET_ACCEPT","NET_CONNECT","PROCESS_EXEC","PROCESS_EXIT"],
 "ratios_only":["FILE_OPEN_ratio","NET_ACCEPT_ratio","NET_CONNECT_ratio","PROCESS_EXEC_ratio","PROCESS_EXIT_ratio"],
 "timing_only":["interarrival_mean","interarrival_std","interarrival_p50"],
}
META=["host","workload","label","rep","window"]
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--features",required=True); ap.add_argument("--outdir",required=True)
    ap.add_argument("--rf-trees",type=int,default=5,help="Sensitivity setting; primary RF may use a larger forest.")
    a=ap.parse_args(); d=pd.read_csv(a.features); out=Path(a.outdir); out.mkdir(parents=True,exist_ok=True)
    here=Path(__file__).resolve().parent
    sets=dict(SETS); sets["full"]=[c for c in d.columns if c not in META]
    for name,cols in sets.items():
      f=out/f"{name}_features.csv"; d[META+cols].to_csv(f,index=False)
      for model in ["LR","RF"]:
        pref=out/f"{name}_{model}"
        subprocess.check_call([sys.executable,str(here/"shift_decomposition.py"),"--features",str(f),
          "--output-prefix",str(pref),"--model",model,"--rf-trees",str(a.rf_trees)])
if __name__=="__main__": main()
