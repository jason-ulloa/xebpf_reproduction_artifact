import numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import f1_score

META={"host","workload","label","rep","window"}

def feature_columns(df):
    return [c for c in df.columns if c not in META]

def model(name, seed=42, rf_trees=400):
    if name=="LR":
        return make_pipeline(StandardScaler(), LogisticRegression(max_iter=5000, class_weight="balanced", random_state=seed))
    if name=="RF":
        return RandomForestClassifier(n_estimators=rf_trees, class_weight="balanced_subsample",
                                      random_state=seed, n_jobs=-1)
    raise ValueError(name)

def fit_model(train,name,seed=42,rf_trees=400):
    X=feature_columns(train)
    m=model(name,seed,rf_trees)
    m.fit(train[X],train.label.astype(int))
    return m,X

def score_f1(m, X, test):
    return f1_score(test.label.astype(int),m.predict(test[X]),zero_division=0)

def fit_f1(train,test,name,seed=42,rf_trees=400):
    m,X=fit_model(train,name,seed,rf_trees)
    return score_f1(m,X,test)

def bootstrap_mean_ci(values, n_boot=5000, seed=42):
    """Bootstrap matched-cell values, not individual feature windows."""
    x=np.asarray(values,float)
    if len(x)==0: return (np.nan,np.nan,np.nan)
    rng=np.random.default_rng(seed)
    means=np.array([rng.choice(x,size=len(x),replace=True).mean() for _ in range(n_boot)])
    return x.mean(),np.quantile(means,.025),np.quantile(means,.975)
