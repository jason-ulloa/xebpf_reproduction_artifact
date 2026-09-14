#!/usr/bin/env python3
import argparse, json
from pathlib import Path
import pandas as pd

def summary_map(path):
    d=pd.read_csv(path).set_index('metric')
    return {k:{'mean':float(r['mean']),'ci95_low':float(r['ci95_low']),'ci95_high':float(r['ci95_high'])} for k,r in d.iterrows()}

def main():
    ap=argparse.ArgumentParser(description='Summarize scientific outcomes of a validated XEBPF methodological reproduction')
    ap.add_argument('--outdir',required=True)
    ap.add_argument('--report-prefix',default=None)
    a=ap.parse_args(); out=Path(a.outdir); errors=[]; report={'protocol_note':'Scientific corroboration is observational and is not a protocol PASS criterion.'}
    val=out/'ANALYSIS_REPRODUCTION_VALIDATION.json'
    if not val.is_file(): errors.append('missing ANALYSIS_REPRODUCTION_VALIDATION.json; run validate_analysis_reproduction.py first')
    else:
      v=json.loads(val.read_text()); report['analysis_protocol_pass']=bool(v.get('passed'))
      if not v.get('passed'): errors.append('analysis protocol validation did not pass')
    primary={}
    for model in ['lr','rf']:
      p=out/f'shift_{model}_summary.csv'
      if not p.is_file(): errors.append('missing '+str(p)); continue
      primary[model.upper()]=summary_map(p)
    report['primary_shift']=primary
    if primary:
      report['primary_corroboration']={m:(s['delta_B_minus_delta_E']['ci95_low']>0) for m,s in primary.items()}

    wins={}; win_all=True
    for model in ['lr','rf']:
      wins[model.upper()]={}
      for w in [1,5,10,30]:
        p=out/'window_sensitivity'/f'{model}_{w}s_summary.csv'
        if not p.is_file(): errors.append('missing '+str(p)); win_all=False; continue
        s=summary_map(p); ok=s['delta_B_minus_delta_E']['ci95_low']>0; win_all &= ok
        wins[model.upper()][str(w)]={'delta_E':s['delta_E'],'delta_B':s['delta_B'],'delta_B_minus_delta_E':s['delta_B_minus_delta_E'],'ordering_supported_ci95':ok}
    report['window_sensitivity']=wins; report['window_ordering_supported_all']=bool(win_all)

    abl={}; abl_all=True
    for fs in ['counts_only','ratios_only','timing_only','full']:
      abl[fs]={}
      for model in ['LR','RF']:
        p=out/'ablation'/f'{fs}_{model}_summary.csv'
        if not p.is_file(): errors.append('missing '+str(p)); abl_all=False; continue
        s=summary_map(p); ok=s['delta_B_minus_delta_E']['ci95_low']>0; abl_all &= ok
        abl[fs][model]={'delta_E':s['delta_E'],'delta_B':s['delta_B'],'delta_B_minus_delta_E':s['delta_B_minus_delta_E'],'ordering_supported_ci95':ok}
    report['feature_ablation']=abl; report['ablation_ordering_supported_all']=bool(abl_all)

    ep=out/'environment_shift.csv'
    if not ep.is_file(): errors.append('missing environment_shift.csv')
    else:
      e=pd.read_csv(ep); pairs=sorted({f'{min(a,b)}-{max(a,b)}' for a,b in zip(e.host_a.astype(str),e.host_b.astype(str))})
      nz=int((e.normalized_w1.abs()>1e-12).sum())
      top=(e.groupby('feature').normalized_w1.agg(['mean','median','min','max','count']).sort_values('mean',ascending=False).head(10).reset_index())
      report['environment_shift']={'rows':len(e),'pairs':pairs,'nonzero_distances':nz,'nonzero_fraction':nz/len(e) if len(e) else None,'top_features':top.to_dict(orient='records')}

    report['scientific_corroboration']={
      'primary_ordering_supported_all_models': all(report.get('primary_corroboration',{}).values()) if report.get('primary_corroboration') else False,
      'window_ordering_supported_all':report.get('window_ordering_supported_all',False),
      'ablation_ordering_supported_all':report.get('ablation_ordering_supported_all',False),
      'measurable_environment_shift': report.get('environment_shift',{}).get('nonzero_distances',0)>0,
    }
    report['errors']=errors
    prefix=Path(a.report_prefix) if a.report_prefix else out/'SCIENTIFIC_REPRODUCTION_SUMMARY'
    prefix.parent.mkdir(parents=True,exist_ok=True)
    Path(str(prefix)+'.json').write_text(json.dumps(report,indent=2)+'\n')
    lines=['XEBPF SCIENTIFIC REPRODUCTION SUMMARY','',f'Analysis protocol PASS: {report.get("analysis_protocol_pass",False)}','', 'Primary matched shift:']
    for m,s in primary.items():
      c=s['delta_B_minus_delta_E']; lines.append(f'  {m}: delta_E={s["delta_E"]["mean"]:.6f} delta_B={s["delta_B"]["mean"]:.6f} delta_B-delta_E={c["mean"]:.6f} CI95=[{c["ci95_low"]:.6f},{c["ci95_high"]:.6f}] supported={c["ci95_low"]>0}')
    lines += ['',f'Window sensitivity ordering supported in all 8 model/window combinations: {report.get("window_ordering_supported_all",False)}',f'Feature-ablation ordering supported in all 8 model/representation combinations: {report.get("ablation_ordering_supported_all",False)}']
    if 'environment_shift' in report:
      es=report['environment_shift']; lines += [f'Environment pairs: {", ".join(es["pairs"])}',f'Non-zero normalized W1 distances: {es["nonzero_distances"]}/{es["rows"]} ({100*es["nonzero_fraction"]:.2f}%)']
    lines += ['', 'Interpretation:', '  Scientific corroboration is separate from protocol validation.', '  Different numerical scores on new Linux systems are scientifically valid when the frozen protocol passes.', '  A positive CI95 for delta_B-delta_E means the reproduced data support the same qualitative ordering as the paper.']
    if errors: lines += ['','ERRORS:']+['  - '+e for e in errors]
    Path(str(prefix)+'.txt').write_text('\n'.join(lines)+'\n')
    print('\n'.join(lines))
    if errors: raise SystemExit(2)

if __name__=='__main__': main()
