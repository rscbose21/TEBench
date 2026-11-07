"""Rebuild local first-pass tables from hash-verified official CSV snapshots. No interpolation."""
from pathlib import Path
import pandas as pd, numpy as np, json, hashlib
P=Path(__file__).parent;R=P/'raw'
m=json.loads((R/'manifest.json').read_text())
for v in [m['projects']['ThermoelectricMaterials'][k] for k in ['papers','samples','curves']]:
 assert hashlib.sha256((R/v['filename']).read_bytes()).hexdigest()==v['sha256']
s=pd.read_csv(R/'ThermoelectricMaterials_samples.csv.gz').fillna('')
c=pd.read_csv(R/'ThermoelectricMaterials_curves.csv.gz').fillna('')
papers=pd.read_csv(R/'ThermoelectricMaterials_papers.csv.gz')
assert not s.duplicated(['SID','sample_id']).any()
def cat(x,k):
 v=json.loads(x or '{}').get(k,{})
 return v.get('category','') if isinstance(v,dict) else str(v or '')
for k in ['DataType','MaterialFamily','Form','FabricationProcess','ElectricalMeasurement','ThermalMeasurement']:
 s[k]=s.sample_info.map(lambda x:cat(x,k))
s.to_csv(P/'sample_metadata.csv.gz',index=False)
c.groupby(['prop_x','unit_x','prop_y','unit_y']).size().rename('curves').to_csv(P/'property_unit_inventory.csv')
# Exact labels only: uncertain aliases, log properties, inverse-T axes, and lattice/electronic kappa excluded.
mapping={
 'Seebeck coefficient':('seebeck_uV_K',{'V*K^(-1)':1e6,'V/K':1e6,'uV/K':1,'μV/K':1}),
 'Electrical conductivity':('sigma_S_m',{'ohm^(-1)*m^(-1)':1,'S/m':1,'S/cm':100}),
 'Electrical resistivity':('rho_ohm_m',{'ohm*m':1,'ohm*cm':.01}),
 'Thermal conductivity':('kappa_W_m_K',{'W*m^(-1)*K^(-1)':1}),
 'total thermal conductivity':('kappa_W_m_K',{'W*m^(-1)*K^(-1)':1}),
 'Power factor':('power_factor_W_m_K2',{'W*m^(-1)*K^(-2)':1}),
 'ZT':('zT',{'-':1})}
rows=[];excluded=[]
for r in c.itertuples(index=True):
 i=r.Index
 reason=''
 if r.prop_x!='Temperature' or r.unit_x!='K':reason='noncanonical_temperature_axis'
 elif r.prop_y not in mapping:reason='noncanonical_property'
 elif r.unit_y not in mapping[r.prop_y][1]:reason='unrecognized_unit'
 if reason:
  excluded.append((i,reason));continue
 try:x=json.loads(r.x);y=json.loads(r.y)
 except Exception:excluded.append((i,'invalid_array_json'));continue
 if len(x)!=len(y):excluded.append((i,'unequal_array_length'));continue
 prop,units=mapping[r.prop_y]
 for j,(t,v) in enumerate(zip(x,y)):
  rows.append((i,j,r.SID,r.sample_id,r.figure_id,r.DOI,r.composition,t,prop,v,r.unit_y,units[r.unit_y]))
d=pd.DataFrame(rows,columns=['curve_row','point_index','SID','sample_id','figure_id','DOI','composition','temperature_K','property','raw_value','raw_unit','conversion_factor'])
for k in ['temperature_K','raw_value']:d[k]=pd.to_numeric(d[k],errors='coerce')
d['value']=d.raw_value*d.conversion_factor
meta=s[['SID','sample_id','sample_name','composition','DataType','MaterialFamily','Form']].rename(columns={'composition':'sample_composition'})
d=d.merge(meta,on=['SID','sample_id'],how='left',validate='many_to_one')
d['missing_value']=~np.isfinite(d.value);d['missing_temperature']=~np.isfinite(d.temperature_K)
d['composition_missing']=d.composition.eq('');d['composition_mismatch']=d.composition.ne(d.sample_composition)
d['temperature_review']=((d.temperature_K<=0)|(d.temperature_K>2000))
d['physical_sign_review']=d.property.isin(['sigma_S_m','rho_ohm_m','kappa_W_m_K'])&d.value.le(0) | d.property.isin(['zT','power_factor_W_m_K2'])&d.value.lt(0)
d['magnitude_review']=d.property.eq('seebeck_uV_K')&d.value.abs().gt(1000) | d.property.eq('zT')&d.value.gt(5)
# Sign of S is not an experimental n/p label. Large positive S alone is NOT invalid.
key=['SID','sample_id','curve_row','property','temperature_K','value']
dup=d.duplicated(key,keep='first');d.loc[dup].to_csv(P/'removed_exact_duplicate_points.csv.gz',index=False);d=d.loc[~dup].copy()
# Composition/T/source is deliberately coarse: different specimens must NOT be collapsed.
d['composition_T_source_repeat']=d.duplicated(['composition','temperature_K','DOI','property'],keep=False)
d['sample_T_property_repeat']=d.duplicated(['SID','sample_id','temperature_K','property'],keep=False)
d['experimental_label']=d.DataType.eq('Experiment')
d.to_csv(P/'starrydata_te_points_candidates.csv.gz',index=False)
e=d[d.experimental_label].copy();e.to_csv(P/'starrydata_te_points_experiment.csv.gz',index=False)
pd.DataFrame(excluded,columns=['curve_row','reason']).to_csv(P/'excluded_curves.csv.gz',index=False)
# Strict experimental wide table: exact T only, conflicts excluded, no averaging/interpolation.
keys=['SID','sample_id','temperature_K'];valid=e[~(e.missing_value|e.missing_temperature)].copy()
g=valid.groupby(keys+['property']).value.agg(['nunique','first']).reset_index()
g[g['nunique']>1].to_csv(P/'conflicting_sample_T_properties.csv.gz',index=False)
g=g[g['nunique']==1]
w=g.pivot(index=keys,columns='property',values='first').reset_index();w.columns.name=None
for k in ['seebeck_uV_K','sigma_S_m','rho_ohm_m','kappa_W_m_K','zT','power_factor_W_m_K2']:
 if k not in w:w[k]=np.nan
w['sigma_derived_from_rho']=w.sigma_S_m.isna()&w.rho_ohm_m.gt(0)
w.loc[w.sigma_derived_from_rho,'sigma_S_m']=1/w.loc[w.sigma_derived_from_rho,'rho_ohm_m']
w=w.merge(s[['SID','sample_id','DOI','composition','sample_name','MaterialFamily']],on=['SID','sample_id'],validate='many_to_one')
w.to_csv(P/'starrydata_te_experiment_exact_T_wide.csv.gz',index=False)
def counts(df):
 return {'points':len(df),'samples':len(df[['SID','sample_id']].drop_duplicates()),'papers':df.SID.nunique(),'unique_nonempty_composition_strings':df.loc[df.composition.ne(''),'composition'].nunique(),'temperature_K_min':float(df.temperature_K.min()),'temperature_K_max':float(df.temperature_K.max()),'property_point_counts':df.property.value_counts().to_dict(),'property_sample_counts':{str(k):len(z[['SID','sample_id']].drop_duplicates()) for k,z in df.groupby('property')},'flag_counts':{k:int(df[k].sum()) for k in ['missing_value','missing_temperature','composition_missing','composition_mismatch','temperature_review','physical_sign_review','magnitude_review','composition_T_source_repeat','sample_T_property_repeat']}}
summary={'raw':{'papers':len(papers),'samples':len(s),'curves':len(c),'unique_nonempty_composition_strings':s.loc[s.composition.ne(''),'composition'].nunique(),'datatype_sample_counts':s.DataType.value_counts().to_dict()},'candidate_selected':counts(d),'experiment_label_selected':counts(e),'removed_exact_duplicate_points':int(dup.sum()),'excluded_curves':pd.Series([v for _,v in excluded]).value_counts().to_dict(),'exact_T_wide_rows':len(w),'exact_T_all_S_sigma_kappa_zT_rows':int(w[['seebeck_uV_K','sigma_S_m','kappa_W_m_K','zT']].notna().all(axis=1).sum())}
coverage=e.groupby(['SID','sample_id']).property.agg(set)
summary['experiment_samples_with_all_four_somewhere_on_curves']=int(coverage.map(lambda x:('seebeck_uV_K' in x and ('sigma_S_m' in x or 'rho_ohm_m' in x) and 'kappa_W_m_K' in x and 'zT' in x)).sum())
fam=s[s.set_index(['SID','sample_id']).index.isin(pd.MultiIndex.from_frame(e[['SID','sample_id']].drop_duplicates()))].MaterialFamily.value_counts()
summary['experimental_top_families_including_missing']=fam.head(16).to_dict()
jpath=P.parent/'jarvis_te.csv'
if jpath.exists():
 jf=set(pd.read_csv(jpath,usecols=['formula']).formula.dropna().str.replace(' ','',regex=False));sf=set(s.composition.str.replace(' ','',regex=False))- {''};ef=set(e.composition.str.replace(' ','',regex=False))- {''}
 common=sorted(jf&sf);pd.DataFrame({'formula':common}).to_csv(P/'jarvis_exact_formula_overlap.csv',index=False)
 summary['jarvis_overlap']={'jarvis_formula_strings':len(jf),'all_raw_sample_exact_formula_overlap':len(common),'experiment_selected_exact_formula_overlap':len(jf&ef),'method':'string match after removing spaces only, no reduction/element reordering'}
(P/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
