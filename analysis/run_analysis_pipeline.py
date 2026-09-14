#!/usr/bin/env python3
import argparse, json, subprocess, sys
from pathlib import Path
import numpy, pandas, sklearn, scipy

def run(cmd):
    cmd=[str(x) for x in cmd]; print('+',' '.join(cmd),flush=True); subprocess.check_call([sys.executable]+cmd)

def main():
    ap=argparse.ArgumentParser(description='Run the complete controlled paper analysis')
    ap.add_argument('--manifest',required=True); ap.add_argument('--outdir',required=True); a=ap.parse_args()
    here=Path(__file__).resolve().parent; root=here.parent; out=Path(a.outdir); out.mkdir(parents=True,exist_ok=True)
    spec=json.loads((root/'protocol_spec.json').read_text())
    duration=spec['features']['analysis_duration_seconds']; primary_w=spec['features']['primary_window_seconds']
    boot=spec['models']['bootstrap']['iterations']; rf_model1=spec['models']['rf_model1']['n_estimators']; rf_shift=spec['models']['rf_shift_decomposition']['n_estimators']; rf_window=spec['models']['rf_window_sensitivity']['n_estimators']; rf_ab=spec['models']['rf_feature_ablation_sensitivity']['n_estimators']
    features=out/'features_5s.csv'
    run([here/'feature_extract.py','--manifest',a.manifest,'--window',primary_w,'--duration',duration,'--output',features])
    run([here/'model1.py','--features',features,'--model','LR','--output',out/'model1_lr.csv'])
    run([here/'model1.py','--features',features,'--model','RF','--rf-trees',rf_model1,'--output',out/'model1_rf.csv'])
    run([here/'shift_decomposition.py','--features',features,'--model','LR','--bootstrap',boot,'--output-prefix',out/'shift_lr'])
    run([here/'shift_decomposition.py','--features',features,'--model','RF','--rf-trees',rf_shift,'--bootstrap',boot,'--output-prefix',out/'shift_rf'])
    run([here/'window_sensitivity.py','--manifest',a.manifest,'--outdir',out/'window_sensitivity','--windows',*spec['features']['window_sensitivity_seconds'],'--models','LR','RF','--rf-trees',rf_window,'--duration',duration,'--bootstrap',boot])
    run([here/'feature_ablation.py','--features',features,'--outdir',out/'ablation','--rf-trees',rf_ab])
    run([here/'environment_shift.py','--features',features,'--rep',3,'--output',out/'environment_shift.csv'])
    marker={'pipeline':'XEBPF controlled analysis','completed':True,'analysis_duration_seconds':duration,'complete_windows_only':True,'primary_window_seconds':primary_w,'model1_rf_trees':rf_model1,'shift_rf_trees':rf_shift,'window_sensitivity_rf_trees':rf_window,'ablation_rf_trees':rf_ab,'bootstrap_iterations':boot,'window_sensitivity_seconds':spec['features']['window_sensitivity_seconds'],'python_version':sys.version.split()[0],'numpy_version':numpy.__version__,'pandas_version':pandas.__version__,'scikit_learn_version':sklearn.__version__,'scipy_version':scipy.__version__}
    (out/'PIPELINE_COMPLETE.json').write_text(json.dumps(marker,indent=2)+'\n')
    print('PASS: controlled analysis pipeline completed')
if __name__=='__main__': main()
