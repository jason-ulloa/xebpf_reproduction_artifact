#!/usr/bin/env python3
import argparse, subprocess, sys
from pathlib import Path
def main():
    ap=argparse.ArgumentParser(description="Re-run feature extraction and shift decomposition over multiple window sizes")
    ap.add_argument("--manifest",required=True); ap.add_argument("--outdir",required=True)
    ap.add_argument("--windows",nargs="+",type=int,default=[1,5,10,30])
    ap.add_argument("--models",nargs="+",default=["LR","RF"]); ap.add_argument("--rf-trees",type=int,default=400)
    a=ap.parse_args(); here=Path(__file__).resolve().parent; out=Path(a.outdir); out.mkdir(parents=True,exist_ok=True)
    for w in a.windows:
      feat=out/f"features_{w}s.csv"
      subprocess.check_call([sys.executable,str(here/"feature_extract.py"),"--manifest",a.manifest,"--window",str(w),"--output",str(feat)])
      for m in a.models:
        prefix=out/f"{m.lower()}_{w}s"
        subprocess.check_call([sys.executable,str(here/"shift_decomposition.py"),"--features",str(feat),
                               "--output-prefix",str(prefix),"--model",m,"--rf-trees",str(a.rf_trees)])
if __name__=="__main__": main()
