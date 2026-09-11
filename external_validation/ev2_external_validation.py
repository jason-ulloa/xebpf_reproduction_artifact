#!/usr/bin/env python3
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (f1_score,precision_score,recall_score,balanced_accuracy_score,
                             matthews_corrcoef,average_precision_score,roc_auc_score)
from sklearn.model_selection import TimeSeriesSplit

META={"window_epoch","label","attack_families","n_attack_families"}

def models(rf_trees=400):
    return {
      "logreg":Pipeline([("scale",StandardScaler()),
                         ("model",LogisticRegression(max_iter=3000,class_weight="balanced",random_state=42))]),
      "rf":RandomForestClassifier(n_estimators=rf_trees,class_weight="balanced_subsample",
                                  random_state=42,n_jobs=-1,min_samples_leaf=2)
    }

def score(y,p,prob):
    out={"f1":f1_score(y,p,zero_division=0),
         "precision":precision_score(y,p,zero_division=0),
         "recall":recall_score(y,p,zero_division=0),
         "balanced_accuracy":balanced_accuracy_score(y,p),
         "mcc":matthews_corrcoef(y,p)}
    try: out["pr_auc"]=average_precision_score(y,prob)
    except Exception: out["pr_auc"]=np.nan
    try: out["roc_auc"]=roc_auc_score(y,prob)
    except Exception: out["roc_auc"]=np.nan
    return out

def famset(s):
    return set() if pd.isna(s) or not str(s) else set(str(s).split("|"))

def main():
    ap=argparse.ArgumentParser(description="Security-Gym EV2 temporal and pure LOAFO evaluation")
    ap.add_argument("--features",required=True)
    ap.add_argument("--outdir",required=True)
    ap.add_argument("--rf-trees",type=int,default=400)
    a=ap.parse_args()
    out=Path(a.outdir); out.mkdir(parents=True,exist_ok=True)

    df=pd.read_csv(a.features).sort_values("window_epoch").reset_index(drop=True)
    feat=[c for c in df.columns if c not in META]
    X=df[feat].replace([np.inf,-np.inf],0).fillna(0)
    y=df.label.astype(int)
    sets=df.attack_families.fillna("").map(famset)
    fams=sorted({f for s in sets for f in s})
    if len(fams)<4: raise SystemExit("ATTACK FAMILY GATE: FAIL")

    temporal=[]
    for fold,(tr,te) in enumerate(TimeSeriesSplit(n_splits=5).split(X),1):
        if y.iloc[tr].nunique()<2 or y.iloc[te].nunique()<2:
            temporal.append({"fold":fold,"status":"SKIP_SINGLE_CLASS"}); continue
        for name,m in models(a.rf_trees).items():
            m.fit(X.iloc[tr],y.iloc[tr]); p=m.predict(X.iloc[te]); prob=m.predict_proba(X.iloc[te])[:,1]
            r=score(y.iloc[te],p,prob)
            r.update(model=name,fold=fold,status="OK",
                     train_malicious=int(y.iloc[tr].sum()),test_malicious=int(y.iloc[te].sum()))
            temporal.append(r)
    pd.DataFrame(temporal).to_csv(out/"temporal_forward_results.csv",index=False)

    rng=np.random.default_rng(42); rows=[]
    for held in fams:
        pos=np.array([i for i,s in enumerate(sets) if s=={held}])
        benign=np.array([i for i,s in enumerate(sets) if not s and y.iloc[i]==0])
        train=np.array([i for i,s in enumerate(sets) if held not in s])
        nben=min(len(benign),max(200,20*len(pos)))
        bsel=np.sort(rng.choice(benign,size=nben,replace=False)) if nben<len(benign) else benign
        test=np.sort(np.concatenate([pos,bsel]))
        train=np.setdiff1d(train,test)
        if not len(pos) or y.iloc[train].nunique()<2: continue
        for name,m in models(a.rf_trees).items():
            m.fit(X.iloc[train],y.iloc[train]); p=m.predict(X.iloc[test]); prob=m.predict_proba(X.iloc[test])[:,1]
            r=score(y.iloc[test],p,prob)
            r.update(model=name,held_family=held,status="OK",
                     held_malicious_windows=len(pos),test_benign_windows=len(bsel))
            rows.append(r)
    pd.DataFrame(rows).to_csv(out/"leave_one_attack_family_out.csv",index=False)

    summary={"dataset":"Security-Gym v4.1","dataset_doi":"10.5281/zenodo.21763493",
             "stream":"exp_30d_heavy_v4","windows":int(len(df)),
             "malicious_windows":int(y.sum()),"attack_families":fams,
             "interpretation_guardrail":
             "External behavioral validation only; Security-Gym provenance prevents causal environment-shift inference."}
    (out/"summary.json").write_text(json.dumps(summary,indent=2))
    print("EXTERNAL-VALIDATION-2: PASS")
if __name__=="__main__": main()
