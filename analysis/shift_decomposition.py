#!/usr/bin/env python3
import argparse, itertools, pandas as pd
from common import fit_model, score_f1, bootstrap_mean_ci

def _next_cyclic(xs, x):
    i=xs.index(x)
    return xs[(i+1)%len(xs)]

def main():
    ap=argparse.ArgumentParser(description="Matched I/E/B/E+B shift decomposition with equal training-family cardinality")
    ap.add_argument("--features",required=True); ap.add_argument("--output-prefix",required=True)
    ap.add_argument("--model",choices=["LR","RF"],default="LR")
    ap.add_argument("--rf-trees",type=int,default=20,
                    help="Frozen matched-decomposition RF gate uses 20 trees; MODEL-1 RF uses 400")
    ap.add_argument("--bootstrap",type=int,default=5000)
    a=ap.parse_args(); d=pd.read_csv(a.features)
    benign=sorted(d.loc[d.label==0,"workload"].unique().tolist())
    attack=sorted(d.loc[d.label==1,"workload"].unique().tolist())
    hosts=sorted(d.host.unique().tolist()); rows=[]
    if len(benign)!=5 or len(attack)!=5:
        raise SystemExit(f"Expected 5 benign and 5 attack families, found {len(benign)} and {len(attack)}")

    # For each source and held pair, train two equal-cardinality (8-family) regimes once.
    # Seen regime excludes a deterministic cyclic control pair, so the held pair is represented.
    # Unseen regime excludes the held pair itself.
    for src in hosts:
      for hb in benign:
        for ha in attack:
          cb=_next_cyclic(benign,hb); ca=_next_cyclic(attack,ha)
          seen_train=d[(d.host==src)&(d.rep.isin([1,2]))&(~d.workload.isin([cb,ca]))]
          unseen_train=d[(d.host==src)&(d.rep.isin([1,2]))&(~d.workload.isin([hb,ha]))]
          if seen_train.workload.nunique()!=8 or unseen_train.workload.nunique()!=8:
              raise SystemExit(f"Training-cardinality mismatch for {src}/{hb}/{ha}")
          if seen_train.label.nunique()<2 or unseen_train.label.nunique()<2:
              raise SystemExit(f"Training labels incomplete for {src}/{hb}/{ha}")
          seen_model,seen_X=fit_model(seen_train,a.model,rf_trees=a.rf_trees)
          unseen_model,unseen_X=fit_model(unseen_train,a.model,rf_trees=a.rf_trees)
          test_I=d[(d.host==src)&(d.rep==3)&(d.workload.isin([hb,ha]))]
          I=score_f1(seen_model,seen_X,test_I)
          B=score_f1(unseen_model,unseen_X,test_I)
          for tgt in hosts:
            if tgt==src: continue
            test_E=d[(d.host==tgt)&(d.rep==3)&(d.workload.isin([hb,ha]))]
            E=score_f1(seen_model,seen_X,test_E)
            EB=score_f1(unseen_model,unseen_X,test_E)
            dE=I-E; dB=I-B; dEB=I-EB
            interaction=dEB-dE-dB
            rows.append({"source":src,"target":tgt,"held_benign":hb,"held_attack":ha,
                         "control_benign":cb,"control_attack":ca,
                         "I":I,"E":E,"B":B,"E+B":EB,
                         "delta_E":dE,"delta_B":dB,"delta_EB":dEB,
                         "delta_B_minus_delta_E":dB-dE,
                         "interaction":interaction})
    out=pd.DataFrame(rows)
    out.to_csv(a.output_prefix+"_matched.csv",index=False)
    summ=[]
    for c in ["I","E","B","E+B","delta_E","delta_B","delta_EB","delta_B_minus_delta_E","interaction"]:
      mean,lo,hi=bootstrap_mean_ci(out[c],n_boot=a.bootstrap)
      summ.append({"metric":c,"mean":mean,"ci95_low":lo,"ci95_high":hi})
    pd.DataFrame(summ).to_csv(a.output_prefix+"_summary.csv",index=False)
    print(f"Wrote {len(out)} matched cells")
if __name__=="__main__": main()
