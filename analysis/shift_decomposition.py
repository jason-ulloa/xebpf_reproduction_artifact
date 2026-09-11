#!/usr/bin/env python3
import argparse, itertools, pandas as pd
from common import fit_f1, bootstrap_mean_ci

def main():
    ap=argparse.ArgumentParser(description="Matched I/E/B/E+B shift decomposition")
    ap.add_argument("--features",required=True); ap.add_argument("--output-prefix",required=True)
    ap.add_argument("--model",choices=["LR","RF"],default="LR"); ap.add_argument("--rf-trees",type=int,default=400)
    a=ap.parse_args(); d=pd.read_csv(a.features)
    benign=sorted(d.loc[d.label==0,"workload"].unique())
    attack=sorted(d.loc[d.label==1,"workload"].unique())
    hosts=sorted(d.host.unique()); rows=[]
    for src,tgt in itertools.permutations(hosts,2):
      for hb in benign:
        for ha in attack:
          held={hb,ha}; represented=[w for w in sorted(d.workload.unique()) if w not in held]
          tr=d[(d.host==src)&(d.rep.isin([1,2]))&(d.workload.isin(represented))]
          if tr.label.nunique()<2: continue
          tests={
            "I":d[(d.host==src)&(d.rep==3)&(d.workload.isin(represented))],
            "E":d[(d.host==tgt)&(d.rep==3)&(d.workload.isin(represented))],
            "B":d[(d.host==src)&(d.rep==3)&(d.workload.isin(held))],
            "E+B":d[(d.host==tgt)&(d.rep==3)&(d.workload.isin(held))]
          }
          scores={}
          for cond,te in tests.items():
            if te.empty: break
            scores[cond]=fit_f1(tr,te,a.model,rf_trees=a.rf_trees)
          if len(scores)!=4: continue
          rows.append({"source":src,"target":tgt,"held_benign":hb,"held_attack":ha,**scores,
                       "delta_E":scores["I"]-scores["E"],
                       "delta_B":scores["I"]-scores["B"],
                       "delta_EB":scores["I"]-scores["E+B"],
                       "interaction":(scores["E+B"]-scores["B"])-(scores["E"]-scores["I"])})
    out=pd.DataFrame(rows)
    out.to_csv(a.output_prefix+"_matched.csv",index=False)
    summ=[]
    for c in ["I","E","B","E+B","delta_E","delta_B","delta_EB","interaction"]:
      mean,lo,hi=bootstrap_mean_ci(out[c])
      summ.append({"metric":c,"mean":mean,"ci95_low":lo,"ci95_high":hi})
    pd.DataFrame(summ).to_csv(a.output_prefix+"_summary.csv",index=False)
    print(f"Wrote {len(out)} matched cells")
if __name__=="__main__": main()
