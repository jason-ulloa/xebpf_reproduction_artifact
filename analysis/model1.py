#!/usr/bin/env python3
import argparse, pandas as pd
from common import fit_f1

def main():
    ap=argparse.ArgumentParser(description="MODEL-1 known-behavior cross-environment evaluation")
    ap.add_argument("--features",required=True); ap.add_argument("--output",required=True)
    ap.add_argument("--model",choices=["LR","RF"],default="LR"); ap.add_argument("--rf-trees",type=int,default=400)
    a=ap.parse_args(); d=pd.read_csv(a.features)
    rows=[]
    hosts=sorted(d.host.unique())
    for src in hosts:
      for tgt in hosts:
        if src==tgt: continue
        tr=d[(d.host==src)&(d.rep.isin([1,2]))]
        te=d[(d.host==tgt)&(d.rep==3)]
        if tr.label.nunique()<2 or te.empty: continue
        rows.append({"source":src,"target":tgt,"model":a.model,
                     "f1":fit_f1(tr,te,a.model,rf_trees=a.rf_trees)})
    pd.DataFrame(rows).to_csv(a.output,index=False)
    print(f"Wrote {len(rows)} transfer cells")
if __name__=="__main__": main()
