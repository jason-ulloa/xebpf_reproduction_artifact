#!/usr/bin/env python3
import argparse, json, math, sys, inspect
from pathlib import Path
import pandas as pd

ap=argparse.ArgumentParser(description='Validate controlled analysis outputs against the frozen XEBPF paper protocol')
ap.add_argument('--manifest',required=True)
ap.add_argument('--outdir',required=True)
ap.add_argument('--protocol-spec',default=str(Path(__file__).resolve().parents[1]/'protocol_spec.json'))
ap.add_argument('--report-prefix',default=None)
a=ap.parse_args()
spec=json.loads(Path(a.protocol_spec).read_text()); m=pd.read_csv(a.manifest); out=Path(a.outdir); errors=[]; observations={}

try:
 import common, feature_extract
 if list(feature_extract.EVENTS)!=list(spec['features']['event_types']): errors.append('feature_extract.EVENTS differs from protocol_spec')
 lr=common.model('LR'); lp=lr.get_params()
 if 'standardscaler' not in getattr(lr,'named_steps',{}): errors.append('LR standardization step missing')
 lrp=getattr(lr,'named_steps',{}).get('logisticregression')
 if lrp is None or lrp.get_params().get('max_iter')!=spec['models']['lr']['max_iter'] or lrp.get_params().get('class_weight')!=spec['models']['lr']['class_weight'] or lrp.get_params().get('random_state')!=spec['models']['lr']['random_state']: errors.append('LR implementation parameters differ from protocol_spec')
 for key in ['rf_model1','rf_shift_decomposition','rf_window_sensitivity','rf_feature_ablation_sensitivity']:
  cfg=spec['models'][key]; rp=common.model('RF',rf_trees=cfg['n_estimators']).get_params()
  if rp.get('n_estimators')!=cfg['n_estimators'] or rp.get('class_weight')!=cfg['class_weight'] or rp.get('random_state')!=cfg['random_state']: errors.append(key+' implementation parameters differ from protocol_spec')
 sig=inspect.signature(common.bootstrap_mean_ci)
 if sig.parameters['n_boot'].default!=spec['models']['bootstrap']['iterations'] or sig.parameters['seed'].default!=spec['models']['bootstrap']['random_state']: errors.append('bootstrap implementation parameters differ from protocol_spec')
except Exception as e: errors.append('cannot verify analysis implementation against protocol_spec: '+str(e))

req_manifest={'host','workload','label','rep','events_jsonl'}
if not req_manifest.issubset(m.columns): errors.append('manifest missing required columns')
hosts=sorted(m.host.unique()); n=len(hosts); observations['environments']=hosts
min_env=spec['reproduction_scope']['minimum_new_environments_for_cross_environment_analysis']
if n<min_env: errors.append(f'cross-environment analysis requires >= {min_env} environments; found {n}')
expected_workloads=set(spec['acquisition']['benign']['profiles']+spec['acquisition']['attack_emulation']['profiles'])
for h,g in m.groupby('host'):
 if set(g.workload.unique())!=expected_workloads: errors.append(f'{h}: workload family set mismatch')
 for w,wg in g.groupby('workload'):
  if set(map(int,wg.rep.unique()))!={1,2,3}: errors.append(f'{h}/{w}: repetitions are not exactly R01-R03')
 if len(g)!=30: errors.append(f'{h}: classification manifest rows={len(g)} expected=30')

features=out/'features_5s.csv'; d=None
if not features.is_file(): errors.append('missing features_5s.csv')
else:
 d=pd.read_csv(features)
 required_meta={'host','workload','label','rep','window'}
 expected_feats=set(spec['features']['non_event_features'])
 for e in spec['features']['event_types']: expected_feats.update([e,e+'_ratio'])
 if not required_meta.issubset(d.columns): errors.append('feature matrix missing metadata columns')
 if not expected_feats.issubset(d.columns): errors.append('feature matrix missing frozen feature columns: '+','.join(sorted(expected_feats-set(d.columns))))
 extras=set(d.columns)-required_meta-expected_feats
 if extras: errors.append('unexpected model feature columns: '+','.join(sorted(extras)))
 if set(d.host.unique())!=set(hosts): errors.append('feature host set differs from manifest')
 expected_per_run=spec['features']['analysis_duration_seconds']//spec['features']['primary_window_seconds']
 expected_rows=len(m)*expected_per_run
 observations['feature_rows']=len(d); observations['expected_feature_rows']=expected_rows; observations['complete_windows_per_run']=expected_per_run
 if len(d)!=expected_rows: errors.append(f'primary feature rows={len(d)} expected={expected_rows} ({expected_per_run} complete windows/run)')
 for key,g in d.groupby(['host','workload','rep']):
  if len(g)!=expected_per_run or set(map(int,g.window))!=set(range(expected_per_run)): errors.append(f'{key}: primary windows are not exactly 0..{expected_per_run-1}')

expected_transfer=n*(n-1); expected_matched=n*(n-1)*25
for fn in ['model1_lr.csv','model1_rf.csv']:
 p=out/fn
 if not p.is_file(): errors.append('missing '+fn)
 else:
  x=pd.read_csv(p); observations[fn+'_rows']=len(x)
  if len(x)!=expected_transfer: errors.append(f'{fn}: transfer cells={len(x)} expected={expected_transfer}')
  if set(x.columns)!={'source','target','model','f1'}: errors.append(f'{fn}: columns mismatch')

expected_metrics=['I','E','B','E+B','delta_E','delta_B','delta_EB','delta_B_minus_delta_E','interaction']
for pref in ['shift_lr','shift_rf']:
 pm=out/(pref+'_matched.csv'); ps=out/(pref+'_summary.csv')
 if not pm.is_file() or not ps.is_file(): errors.append('missing '+pref+' matched/summary output'); continue
 x=pd.read_csv(pm); s=pd.read_csv(ps); observations[pref+'_matched_rows']=len(x)
 if len(x)!=expected_matched: errors.append(f'{pref}: matched cells={len(x)} expected={expected_matched}')
 need={'source','target','held_benign','held_attack','control_benign','control_attack','I','E','B','E+B','delta_E','delta_B','delta_EB','delta_B_minus_delta_E','interaction'}
 if not need.issubset(x.columns): errors.append(pref+': matched columns mismatch')
 if list(s.metric)!=expected_metrics: errors.append(pref+': summary metric order/content mismatch')
 for _,r in x.iterrows():
  if r['held_benign']==r['control_benign'] or r['held_attack']==r['control_attack']: errors.append(pref+': held/control pair collision'); break

ws=out/'window_sensitivity'
for w in spec['features']['window_sensitivity_seconds']:
 fp=ws/f'features_{w}s.csv'
 if not fp.is_file(): errors.append(f'window sensitivity missing features_{w}s.csv')
 else:
  wd=pd.read_csv(fp); exp=len(m)*(spec['features']['analysis_duration_seconds']//w)
  if len(wd)!=exp: errors.append(f'features_{w}s rows={len(wd)} expected={exp}')
 for model in ['lr','rf']:
  pm=ws/f'{model}_{w}s_matched.csv'; ps=ws/f'{model}_{w}s_summary.csv'
  if not pm.is_file() or not ps.is_file(): errors.append(f'window sensitivity missing {model}_{w}s outputs'); continue
  x=pd.read_csv(pm); s=pd.read_csv(ps)
  if len(x)!=expected_matched: errors.append(f'{model}_{w}s matched cells={len(x)} expected={expected_matched}')
  if 'delta_B_minus_delta_E' not in x.columns or 'delta_B_minus_delta_E' not in set(s.metric): errors.append(f'{model}_{w}s missing direct contrast')

abl=out/'ablation'
for name in ['counts_only','ratios_only','timing_only','full']:
 if not (abl/f'{name}_features.csv').is_file(): errors.append(f'ablation missing {name}_features.csv')
 for model in ['LR','RF']:
  pm=abl/f'{name}_{model}_matched.csv'; ps=abl/f'{name}_{model}_summary.csv'
  if not pm.is_file() or not ps.is_file(): errors.append(f'ablation missing {name}_{model} outputs'); continue
  x=pd.read_csv(pm); s=pd.read_csv(ps)
  if len(x)!=expected_matched: errors.append(f'{name}_{model}: matched cells={len(x)} expected={expected_matched}')
  if 'delta_B_minus_delta_E' not in x.columns or 'delta_B_minus_delta_E' not in set(s.metric): errors.append(f'{name}_{model}: missing direct contrast')

env=out/'environment_shift.csv'
if not env.is_file(): errors.append('missing environment_shift.csv')
elif d is not None:
 x=pd.read_csv(env); feature_count=len([c for c in d.columns if c not in {'host','workload','label','rep','window'}]); expected_env=10*(n*(n-1)//2)*feature_count
 observations['environment_shift_rows']=len(x)
 if len(x)!=expected_env: errors.append(f'environment_shift rows={len(x)} expected={expected_env}')
 need={'workload','host_a','host_b','feature','w1','denominator','normalized_w1'}
 if not need.issubset(x.columns): errors.append('environment_shift columns mismatch')

complete=out/'PIPELINE_COMPLETE.json'
if not complete.is_file(): errors.append('missing PIPELINE_COMPLETE.json')
else:
 try:
  c=json.loads(complete.read_text())
  if c.get('completed') is not True: errors.append('analysis pipeline completion marker is not true')
  checks={
   'analysis_duration_seconds':spec['features']['analysis_duration_seconds'],
   'complete_windows_only':True,
   'model1_rf_trees':spec['models']['rf_model1']['n_estimators'],
   'shift_rf_trees':spec['models']['rf_shift_decomposition']['n_estimators'],
   'window_sensitivity_rf_trees':spec['models']['rf_window_sensitivity']['n_estimators'],
   'ablation_rf_trees':spec['models']['rf_feature_ablation_sensitivity']['n_estimators'],
   'bootstrap_iterations':spec['models']['bootstrap']['iterations'],
  }
  for k,v in checks.items():
   if c.get(k)!=v: errors.append(f'PIPELINE_COMPLETE {k}={c.get(k)} expected={v}')
 except Exception as e: errors.append('PIPELINE_COMPLETE parse error: '+str(e))

report={'validation':'XEBPF-ANALYSIS-REPRODUCTION','passed':not errors,'environment_count':n,'expected_model1_transfer_cells':expected_transfer,'expected_shift_matched_cells':expected_matched,'observations':observations,'errors':errors,'important_interpretation':'PASS validates protocol execution and output structure; it does not require new systems to reproduce the original confidential numerical results.'}
print('XEBPF ANALYSIS REPRODUCTION VALIDATION')
print('Environments:',n,hosts); print('Expected MODEL-1 transfer cells:',expected_transfer); print('Expected matched shift cells/model:',expected_matched)
if d is not None: print('Expected complete 5-s windows:',observations.get('expected_feature_rows'))
print('RESULT:','PASS' if not errors else 'FAIL')
for e in errors: print(' - '+e)
if a.report_prefix:
 p=Path(a.report_prefix); p.parent.mkdir(parents=True,exist_ok=True)
 Path(str(p)+'.json').write_text(json.dumps(report,indent=2)+'\n')
 Path(str(p)+'.txt').write_text('\n'.join(['XEBPF ANALYSIS REPRODUCTION VALIDATION',f'passed={report["passed"]}',f'environments={n}',f'expected_model1_transfer_cells={expected_transfer}',f'expected_shift_matched_cells={expected_matched}',f'expected_primary_feature_rows={observations.get("expected_feature_rows")}']+['ERROR: '+e for e in errors])+'\n')
if errors: sys.exit(2)
