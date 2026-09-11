#!/usr/bin/env python3
import argparse
from pathlib import Path
import numpy as np,pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (f1_score,precision_score,recall_score,balanced_accuracy_score,
                             matthews_corrcoef,average_precision_score,roc_auc_score,confusion_matrix)

META={"window_epoch","label","attack_families","n_attack_families"}

def famset(s):
    return set() if pd.isna(s) or not str(s) else set(str(s).split("|"))

def make_model(name,rf_trees):
    if name=="logreg":
        return Pipeline([("scale",StandardScaler()),
                         ("model",LogisticRegression(max_iter=3000,class_weight="balanced",random_state=42))])
    return RandomForestClassifier(n_estimators=rf_trees,class_weight="balanced_subsample",
                                  random_state=42,n_jobs=-1,min_samples_leaf=2)

def metrics(y,p,prob):
    tn,fp,fn,tp=confusion_matrix(y,p,labels=[0,1]).ravel()
    return {"f1":f1_score(y,p,zero_division=0),"precision":precision_score(y,p,zero_division=0),
            "recall":recall_score(y,p,zero_division=0),
            "balanced_accuracy":balanced_accuracy_score(y,p),
            "mcc":matthews_corrcoef(y,p),"pr_auc":average_precision_score(y,prob),
            "roc_auc":roc_auc_score(y,prob),"tn":tn,"fp":fp,"fn":fn,"tp":tp}

def main():
    ap=argparse.ArgumentParser(description="EV2.1: strict 70/30 temporal split + held-family exclusion")
    ap.add_argument("--features",required=True)
    ap.add_argument("--outdir",required=True)
    ap.add_argument("--rf-trees",type=int,default=100,
                    help="100 reproduces the RF sensitivity configuration reported for EV2.1")
    a=ap.parse_args()
    out=Path(a.outdir); out.mkdir(parents=True,exist_ok=True)

    df=pd.read_csv(a.features).sort_values("window_epoch").reset_index(drop=True)
    feat=[c for c in df.columns if c not in META]
    X=df[feat].replace([np.inf,-np.inf],0).fillna(0)
    y=df.label.astype(int)
    sets=df.attack_families.fillna("").map(famset)
    fams=sorted({f for s in sets for f in s})

    cut=int(len(df)*0.70)
    early=np.arange(cut); late=np.arange(cut,len(df))
    cutoff_epoch=int(df.iloc[cut]["window_epoch"])

    rows=[]
    for held in fams:
        train=np.array([i for i in early if held not in sets.iloc[i]])
        positives=np.array([i for i in late if sets.iloc[i]=={held} and y.iloc[i]==1])
        benign=np.array([i for i in late if not sets.iloc[i] and y.iloc[i]==0])

        if not len(positives) or y.iloc[train].nunique()<2: continue

        # Same deterministic late-benign sampling rule used in the study:
        # up to 20 benign windows per held-family positive, minimum 200 when available.
        rng=np.random.default_rng(100+fams.index(held))
        nben=min(len(benign),max(200,20*len(positives)))
        bsel=np.sort(rng.choice(benign,size=nben,replace=False)) if nben<len(benign) else benign
        test=np.sort(np.concatenate([positives,bsel]))

        for name in ["logreg","rf"]:
            model=make_model(name,a.rf_trees)
            model.fit(X.iloc[train],y.iloc[train])
            pred=model.predict(X.iloc[test]); prob=model.predict_proba(X.iloc[test])[:,1]
            r=metrics(y.iloc[test],pred,prob)
            r.update(model=("rf100_sensitivity" if name=="rf" and a.rf_trees==100 else name),
                     held_family=held,train_n=len(train),train_malicious=int(y.iloc[train].sum()),
                     train_benign=int((y.iloc[train]==0).sum()),test_n=len(test),
                     test_malicious=len(positives),test_benign=len(bsel),status="OK",
                     train_prevalence=float(y.iloc[train].mean()),
                     test_prevalence=float(y.iloc[test].mean()),cutoff_epoch=cutoff_epoch)
            rows.append(r)

    detail=pd.DataFrame(rows)
    detail.to_csv(out/"combined_temporal_loafo_results.csv",index=False)

    summary=(detail.groupby("model")[["f1","precision","recall","pr_auc","roc_auc","mcc"]]
                   .mean().reset_index())
    summary.to_csv(out/"combined_temporal_loafo_summary.csv",index=False)
    print("EV2.1 STRICT TEMPORAL + FAMILY HOLDOUT: PASS")
    print(summary.to_string(index=False))
if __name__=="__main__": main()
