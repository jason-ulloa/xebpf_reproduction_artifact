#!/usr/bin/env python3
import argparse, subprocess, sys
from pathlib import Path

def main():
    ap=argparse.ArgumentParser(description="Re-run feature extraction and matched shift decomposition over multiple window sizes")
    ap.add_argument("--manifest",required=True); ap.add_argument("--outdir",required=True)
    ap.add_argument("--windows",nargs="+",type=int,default=[1,5,10,30])
    ap.add_argument("--models",nargs="+",default=["LR","RF"])
    ap.add_argument("--rf-trees",type=int,default=20)
    ap.add_argument("--duration",type=int,default=120)
    ap.add_argument("--bootstrap",type=int,default=5000)
    a=ap.parse_args(); here=Path(__file__).resolve().parent; out=Path(a.outdir); out.mkdir(parents=True,exist_ok=True)
    for w in a.windows:
      feat=out/f"features_{w}s.csv"
      subprocess.check_call([sys.executable,str(here/"feature_extract.py"),"--manifest",a.manifest,"--window",str(w),"--duration",str(a.duration),"--output",str(feat)])
      for m in a.models:
        prefix=out/f"{m.lower()}_{w}s"
        subprocess.check_call([sys.executable,str(here/"shift_decomposition.py"),"--features",str(feat),
                               "--output-prefix",str(prefix),"--model",m,"--rf-trees",str(a.rf_trees),"--bootstrap",str(a.bootstrap)])
if __name__=="__main__": main()
