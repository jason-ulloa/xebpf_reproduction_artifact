#!/usr/bin/env python3
import argparse, itertools, numpy as np, pandas as pd
from scipy.stats import wasserstein_distance
META={"host","workload","label","rep","window"}
def denom_pair(x,y):
    z=np.concatenate([np.asarray(x,float),np.asarray(y,float)])
    q1,q3=np.quantile(z,[.25,.75]); iqr=q3-q1
    if iqr>1e-12: return iqr
    return max(float(np.median(np.abs(z))),1e-9)
def main():
    ap=argparse.ArgumentParser(description="Matched cross-environment normalized Wasserstein characterization")
    ap.add_argument("--features",required=True); ap.add_argument("--output",required=True)
    ap.add_argument("--rep",type=int,default=3)
    a=ap.parse_args(); d=pd.read_csv(a.features); d=d[d.rep==a.rep]
    feats=[c for c in d.columns if c not in META]; rows=[]
    for workload,g in d.groupby("workload"):
      for h1,h2 in itertools.combinations(sorted(g.host.unique()),2):
        a1=g[g.host==h1]; a2=g[g.host==h2]
        for f in feats:
          x=a1[f].dropna().to_numpy(); y=a2[f].dropna().to_numpy()
          if not len(x) or not len(y): continue
          w=wasserstein_distance(x,y)
          rows.append({"workload":workload,"host_a":h1,"host_b":h2,"feature":f,
                       "w1":w,"denominator":denom_pair(x,y),"normalized_w1":w/denom_pair(x,y)})
    pd.DataFrame(rows).to_csv(a.output,index=False)
    print(f"Wrote {len(rows)} pairwise feature distances")
if __name__=="__main__": main()
