import numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score

META={"host","workload","label","rep","window"}
def feature_columns(df):
    return [c for c in df.columns if c not in META]

def model(name, seed=42, rf_trees=400):
    if name=="LR":
        return LogisticRegression(max_iter=5000, class_weight="balanced", random_state=seed)
    if name=="RF":
        return RandomForestClassifier(n_estimators=rf_trees, class_weight="balanced",
                                      random_state=seed, n_jobs=-1)
    raise ValueError(name)

def fit_f1(train,test,name,seed=42,rf_trees=400):
    X=feature_columns(train)
    m=model(name,seed,rf_trees)
    m.fit(train[X],train.label.astype(int))
    p=m.predict(test[X])
    return f1_score(test.label.astype(int),p,zero_division=0)

def bootstrap_mean_ci(values, n_boot=2000, seed=42):
    x=np.asarray(values,float)
    if len(x)==0: return (np.nan,np.nan,np.nan)
    rng=np.random.default_rng(seed)
    means=np.array([rng.choice(x,size=len(x),replace=True).mean() for _ in range(n_boot)])
    return x.mean(),np.quantile(means,.025),np.quantile(means,.975)
