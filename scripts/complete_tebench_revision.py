"""Local scientific revision, 7 Nov 2026. Run from the TEBench directory.
Preserves original metrics, does not publish, and never pools DFT/experiment.
"""
import os
os.environ['OMP_NUM_THREADS']='4'; os.environ['OPENBLAS_NUM_THREADS']='4'
import json, hashlib, warnings, time, gc
from pathlib import Path
from functools import lru_cache
import numpy as np, pandas as pd
from pymatgen.core import Composition
from sklearn.ensemble import RandomForestRegressor,HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error,mean_squared_error,r2_score
from threadpoolctl import threadpool_limits
import run_tebench_baselines as ref
warnings.filterwarnings('ignore');threadpool_limits(4)
H=Path(__file__).resolve().parent; N=H/'notes/revision_20261107'; SEED=20261107
SOURCES=['bi2te3_bulk_audited','starrydata_experiment','jarvis_dft']
@lru_cache(None)
def canonical(v):
 try:
  s=''.join(str(v).split())
  if not s: return ''
  c=Composition(s,strict=True)
  if c.num_atoms<=0 or any(a<=0 for a in c.values()): return ''
  return c.get_integer_formula_and_factor(max_denominator=1000000)[0]
 except Exception:return ''
def bucket(k):
 f=int(hashlib.sha256(f'{SEED}|jarvis_formula|{k}'.encode()).hexdigest()[:12],16)/16**12
 return 'train' if f<.7 else ('val' if f<.85 else 'test')
summary={'seed':SEED,'canonical_method':'pymatgen Composition(strict=True), positive real elements only; get_integer_formula_and_factor(max_denominator=1000000); no token fallback for matching; failures remain unmatched','parse':{},'overlap':[]}
data={}; splits={}
for src in SOURCES:
 d=pd.read_csv(H/f'tebench_{src}.csv.gz',keep_default_na=False,low_memory=False)
 d['canonical_formula']=d.composition.map(canonical)
 summary['parse'][src]={'records':len(d),'failed_records':int(d.canonical_formula.eq('').sum()),'failed_distinct_strings':int(d.loc[d.canonical_formula.eq(''),'composition'].nunique()),'canonical_formulas':int(d.loc[d.canonical_formula.ne(''),'canonical_formula'].nunique())}
 pd.DataFrame({'composition':d.composition.unique()}).assign(canonical_formula=lambda x:x.composition.map(canonical)).to_csv(N/f'composition_parse_{src}.csv',index=False)
 d.to_csv(H/f'tebench_{src}.csv.gz',index=False,compression='gzip')
 s=pd.read_csv(H/f'tebench_split_{src}.csv.gz',keep_default_na=False)
 s['composition']=s.tebench_id.map(d.set_index('tebench_id').composition)
 s['composition_key']=s.composition.map(canonical)
 if src=='jarvis_dft':
  old=pd.read_csv(N/'reference_jarvis_splits.csv.gz',keep_default_na=False).split__formula_random_70_15_15.copy()
  s['split__formula_random_70_15_15']=[bucket(k) if k else 'excluded_unparseable_formula' for k in s.composition_key]
  summary['jarvis_changed_assignments']=int((old!=s.split__formula_random_70_15_15).sum())
  summary['jarvis_split_counts']=s.split__formula_random_70_15_15.value_counts().to_dict()
  pd.DataFrame({'tebench_id':s.tebench_id,'old':old,'canonical':s.split__formula_random_70_15_15}).to_csv(N/'jarvis_assignment_changes.csv',index=False)
 else:
  summary[src+'_paper_split_unchanged']=True
 s.to_csv(H/f'tebench_split_{src}.csv.gz',index=False,compression='gzip')
 data[src]=d;splits[src]=s
flags=[]; overlaps=[]
for i,a in enumerate(SOURCES):
 for b in SOURCES[i+1:]:
  shared=sorted((set(data[a].canonical_formula)&set(data[b].canonical_formula))-{''})
  summary['overlap'].append({'source_a':a,'source_b':b,'canonical_formula_overlap':len(shared)})
  overlaps.extend([{'source_a':a,'source_b':b,'canonical_formula':x} for x in shared])
for a in SOURCES:
 for b in SOURCES:
  if a==b:continue
  for kind,col in [('composition','composition_key'),('doi','doi_norm')]:
   keys=set(splits[b][col])-{''};g=splits[a][splits[a][col].ne('') & splits[a][col].isin(keys)][['tebench_id','source','domain','sample_record_id','doi','composition',col]].copy()
   if len(g):
    g['shared_key_type']=kind;g['shared_key']=g[col];g['also_in_source']=b
    flags.append(g.drop(columns=col))
pd.DataFrame(overlaps).to_csv(H/'tebench_overlap_keys.csv',index=False)
f=pd.concat(flags,ignore_index=True);f.insert(0,'note','canonical composition / DOI leakage cue only; not sample or structure identity')
f.to_csv(H/'tebench_cross_source_leakage_flags.csv.gz',index=False,compression='gzip')
summary['leakage_flags']={f'{k[0]}:{k[1]}->{k[2]}':int(v) for k,v in f.groupby(['shared_key_type','source','also_in_source']).size().items()}
# Actual structure-derived features from preserved atoms_json; no experiment structures invented.
j=data['jarvis_dft'];feat=[]
for _,r in j.iterrows():
 try:
  a=json.loads(r.original__atoms_json);vol=abs(float(np.linalg.det(a['lattice_mat'])));nat=len(a['elements']);mass=sum(float(Composition({e:1}).weight) for e in a['elements']);density=mass*1.66053906660/vol
  feat.append((vol,nat,density,float(r.original__spacegroup_number)))
 except Exception:feat.append((np.nan,np.nan,np.nan,np.nan))
j[['structure_volume_A3','structure_natoms','structure_density_g_cm3','structure_spacegroup_number']]=feat
j.to_csv(H/'tebench_jarvis_dft.csv.gz',index=False,compression='gzip')
js=j[j.canonical_formula.ne('')][['canonical_formula','sample_record_id','original__spacegroup','original__spacegroup_number','structure_volume_A3','structure_natoms','structure_density_g_cm3']].copy()
js['jarvis_multiplicity']=js.groupby('canonical_formula').sample_record_id.transform('size')
match=[]
for src in SOURCES[:2]:
 e=data[src];e=e[e.canonical_formula.ne('')].groupby('canonical_formula').agg(experimental_records=('tebench_id','size')).reset_index()
 m=e.merge(js,on='canonical_formula');m.insert(0,'experimental_source',src);m['match_type']='composition candidate only; experimental atomic structure / space group unavailable';match.append(m)
m=pd.concat(match,ignore_index=True);m.to_csv(N/'experimental_jarvis_structure_candidates.csv',index=False)
summary['structure_matches']={src:{'matched_experimental_formulas':int(g.canonical_formula.nunique()),'matched_experimental_records':int(g.drop_duplicates('canonical_formula').experimental_records.sum()),'candidate_formula_jid_pairs':len(g),'matched_jids':int(g.sample_record_id.nunique()),'formulas_with_multiple_jids':int(g[g.jarvis_multiplicity>1].canonical_formula.nunique())} for src,g in m.groupby('experimental_source')}
summary['structure_secondary_key']={'experimental_records_with_space_group_or_crystal_system':0,'agreement_evaluable_pairs':0,'reason':'No experimental space-group/crystal-system or atomic-coordinate columns in either local experimental table; lattice a/c alone do not determine a crystal structure.'}
summary['structure_features_missing_rows']=int(j.structure_volume_A3.isna().sum())
# Verify own-paper exclusions.
own={'10.1007/s00339-022-05662-2','10.1016/j.jallcom.2020.157828','10.1016/j.jallcom.2021.158621','10.1016/j.jallcom.2022.163767','10.1021/acsaenm.3c00649','10.1039/d1ra04886d','10.1088/1361-6463/abeb3e','10.1088/2053-1591/ace30b'}
for src in SOURCES[:2]:
 s=splits[src];assert not s.loc[s.doi_norm.isin(own),'split__paper_random_70_15_15'].isin(['train','val']).any()
(N/'revision_counts.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2),flush=True)
# Read only target columns from Starrydata, in chunks, to keep CPU memory bounded.
cols=['SID','sample_id','composition','sample_composition','temperature_K','property','value','missing_value','missing_temperature','composition_missing','magnitude_review','physical_sign_review','temperature_review']
parts=[];kcounts={'all_kappa':0,'prior_QC_kappa':0,'prior_QC_kappa_gt100':0,'prior_QC_kappa_gt1000':0,'prior_QC_kappa_le0':0,'all_kappa_new_flag':0}
for p in pd.read_csv(H/'starrydata_te_points_experiment.csv.gz',usecols=cols,chunksize=150000,keep_default_na=False):
 for c in ['value','temperature_K']:p[c]=pd.to_numeric(p[c],errors='coerce')
 kap=p.property.eq('kappa_W_m_K');new=kap&((p.value<=0)|(p.value>100))
 kcounts['all_kappa']+=int(kap.sum());kcounts['all_kappa_new_flag']+=int(new.sum())
 ok=~p[['missing_value','missing_temperature','composition_missing','magnitude_review','physical_sign_review','temperature_review']].any(axis=1)&p.value.notna()&p.temperature_K.notna()
 kcounts['prior_QC_kappa']+=int((kap&ok).sum());kcounts['prior_QC_kappa_gt100']+=int((kap&ok&(p.value>100)).sum());kcounts['prior_QC_kappa_gt1000']+=int((kap&ok&(p.value>1000)).sum());kcounts['prior_QC_kappa_le0']+=int((kap&ok&(p.value<=0)).sum())
 # Save only compact QC provenance, never a raw dump in the submission package.
 select=ok & p.property.isin(['seebeck_uV_K','zT','kappa_W_m_K']) & ~new
 p=p[select].copy();p['composition']=p.composition.where(p.composition.ne(''),p.sample_composition)
 parts.append(p[['SID','sample_id','composition','temperature_K','property','value']])
kcounts['kappa_after_new_rule_before_join_and_feature_parse']=kcounts['prior_QC_kappa']-kcounts['prior_QC_kappa_gt100']-kcounts['prior_QC_kappa_le0']
p=pd.concat(parts,ignore_index=True);del parts
s=splits['starrydata_experiment'][['tebench_id','paper_id','sample_record_id','split__paper_random_70_15_15']].rename(columns={'paper_id':'SID','sample_record_id':'sample_id','split__paper_random_70_15_15':'role'})
p=p.merge(s,on=['SID','sample_id']);summary['kappa_QC']=kcounts
(N/'revision_counts.json').write_text(json.dumps(summary,indent=2))
print('QC',kcounts,flush=True)
# Preserve all old metric rows and add explicit model/split version columns.
old=pd.read_csv(N/'reference_metrics.csv');old['model']='RF_reference_original';old['split_version']='original_string';old['qc_version']='prior_review_flags'
rows=[];preds=[];selection=[]
def score(y,p):return {'MAE':float(mean_absolute_error(y,p)),'RMSE':float(np.sqrt(mean_squared_error(y,p))),'R2':float(r2_score(y,p))}
def run(src,t,d,scheme,struct=None,reference=False):
 d=d.copy();d['y']=pd.to_numeric(d.y,errors='coerce');d=d[d.y.notna()]
 X=ref.feature_matrix(d.composition,d.temperature_K if 'temperature_K' in d else None).astype('float32')
 ok=np.isfinite(X).all(axis=1);bad=int((~ok).sum());d=d[ok];X=X[ok];y=d.y.to_numpy(float);roles=d.role.to_numpy();tr=roles=='train';va=roles=='val'
 if struct:
  extra=d[struct].apply(pd.to_numeric,errors='coerce').to_numpy(np.float32);X=np.column_stack([X,extra])
 if tr.sum()<10 or va.sum()<10:return
 models=[]
 if reference:
  params=(ref.RF_LARGE if src=='starrydata_experiment' else ref.RF_SMALL).copy();params['n_jobs']=4
  model=RandomForestRegressor(**params);t0=time.time();model.fit(X[tr],y[tr]);models.append(('RF_QC100' if src=='starrydata_experiment' else 'RF_canonical_split',model,params,time.time()-t0))
 # Two-candidate predeclared grid; validation MAE only; do not refit on val.
 best=None
 for leaf in [15,31]:
  hp=dict(max_iter=150,max_leaf_nodes=leaf,learning_rate=.08,l2_regularization=1.,min_samples_leaf=20,early_stopping=False,random_state=SEED)
  h=HistGradientBoostingRegressor(**hp);t0=time.time();h.fit(X[tr],y[tr]);elapsed=time.time()-t0;v=float(mean_absolute_error(y[va],h.predict(X[va])))
  selection.append(dict(source=src,target=t,scheme=scheme,structure_features=bool(struct),params=hp,validation_MAE=v,fit_seconds=elapsed))
  if best is None or v<best[0]:best=(v,h,hp,elapsed)
 models.append(('HGB_tuned_structure' if struct else 'HGB_tuned',best[1],best[2],best[3]))
 mean=y[tr].mean()
 for name,model,hp,elapsed in models:
  for role in ['val','test','own_paper_holdout','leaveout_test']:
   ev=roles==role
   if ev.sum()<10:continue
   pr=model.predict(X[ev]);a=score(y[ev],pr);b=score(y[ev],np.full(ev.sum(),mean))
   rows.append(dict(source=src,target=t,split_scheme=scheme,eval_role=role,n_train=int(tr.sum()),n=int(ev.sum()),RF_MAE=a['MAE'],RF_RMSE=a['RMSE'],RF_R2=a['R2'],mean_MAE=b['MAE'],mean_RMSE=b['RMSE'],mean_R2=b['R2'],train_mean=float(mean),rows_dropped_unparsable_composition=bad,fit_seconds=round(elapsed,2),model=name,split_version='canonical_20261107' if src=='jarvis_dft' else 'paper_unchanged',qc_version='kappa_0_lt_kappa_le_100' if src=='starrydata_experiment' and t.startswith('kappa') else 'prior_review_flags',hyperparameters=json.dumps(hp)))
   # Raw Starrydata point predictions remain local, outside submission package.
   out=d.loc[ev,['tebench_id','composition']].copy();out['source']=src;out['target']=t;out['model']=name;out['split_scheme']=scheme;out['split_role']=role;out['y_true']=y[ev];out['y_pred']=pr;preds.append(out)
  print('FIT',src,t,scheme,name,'train',tr.sum(),'valMAE',best[0],flush=True)
 pd.concat([old,pd.DataFrame(rows)],ignore_index=True).to_csv(H/'tebench_baseline_metrics.csv',index=False)
 (N/'model_selection.json').write_text(json.dumps(selection,indent=2))
 del X;gc.collect()
bi=data['bi2te3_bulk_audited'].merge(splits['bi2te3_bulk_audited'][['tebench_id','split__paper_random_70_15_15']],on='tebench_id').rename(columns={'split__paper_random_70_15_15':'role'})
bi=bi[~bi.role.str.startswith('excluded')]
for t in ['seebeck_uV_K','zT']:
 run('bi2te3_bulk_audited',t,bi[['tebench_id','composition','temperature_K','role']].assign(y=bi[t]),'paper_random_70_15_15')
for t in ['seebeck_uV_K','zT','kappa_W_m_K']:
 q=p[p.property.eq(t)];run('starrydata_experiment',t,q[['tebench_id','composition','temperature_K','role']].assign(y=q.value),'paper_random_70_15_15 (point-level)',reference=t=='kappa_W_m_K')
del p;gc.collect()
j=j.merge(splits['jarvis_dft'][['tebench_id','split__formula_random_70_15_15','split__leave_contains_Bi_and_Te_out','split__leave_BiSbTeSe_only_out']],on='tebench_id')
struct=['structure_volume_A3','structure_natoms','structure_density_g_cm3','structure_spacegroup_number']
for t in ['n-Seebeck','p-Seebeck','n-powerfact','p-powerfact']:
 base=j[['tebench_id','composition']+struct].assign(y=j['original__'+t])
 d=base.assign(role=j.split__formula_random_70_15_15)
 run('jarvis_dft',t,d,'formula_random_70_15_15',reference=True)
 run('jarvis_dft',t,d,'formula_random_70_15_15',struct=struct)
 for scheme in ['leave_contains_Bi_and_Te_out','leave_BiSbTeSe_only_out']:
  hold=j['split__'+scheme].eq('test');role=np.where(hold,'leaveout_test',np.where(j.split__formula_random_70_15_15.eq('train'),'train',np.where(j.split__formula_random_70_15_15.eq('val'),'val','unused')))
  run('jarvis_dft',t,base.assign(role=role),scheme,reference=True)
# Save reproducible predictions and unified summary; all old metric rows retained.
pr=pd.concat(preds,ignore_index=True)
for src,g in pr.groupby('source'):g.to_csv(H/f'tebench_revision_predictions_{src}.csv.gz',index=False,compression='gzip')
summary['model_grid']='HGB max_leaf_nodes=[15,31], max_iter=150, learning_rate=.08, l2_regularization=1, min_samples_leaf=20; select by validation MAE; fit on train only; early_stopping=False'
summary['selected_hyperparameters']=selection;summary['new_metrics']=rows
(N/'revision_counts.json').write_text(json.dumps({k:v for k,v in summary.items() if k not in ['selected_hyperparameters','new_metrics']},indent=2))
original=json.loads((N/'reference_summary.json').read_text());original['revision_20261107']=summary;original['metrics']=pd.concat([old,pd.DataFrame(rows)],ignore_index=True).fillna('').to_dict('records')
(H/'tebench_baseline_summary.json').write_text(json.dumps(original,indent=2));print('COMPLETE',len(rows),'new metric rows',flush=True)
