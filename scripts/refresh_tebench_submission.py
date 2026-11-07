"""Refresh submission documents from preserved prior DOCX and completed metrics.
Run only after complete_tebench_revision.py finishes. No external writes.
"""
from pathlib import Path
import json, shutil, re
import numpy as np,pandas as pd
from docx import Document
from docx.shared import Pt,Cm
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
H=Path(__file__).resolve().parent;N=H/'notes/revision_20261107';P=H/'submission_package';F=P/'figures'
C=json.loads((N/'revision_counts.json').read_text());M=pd.read_csv(H/'tebench_baseline_metrics.csv').fillna('')
new=M[M.model.ne('RF_reference_original')]
def fmt(x):return f'{float(x):.5g}'
def metric(src,target,model,role='test',scheme=None):
 d=M[(M.source==src)&(M.target==target)&(M.model==model)&(M.eval_role==role)]
 if scheme:d=d[d.split_scheme==scheme]
 elif src=='jarvis_dft':d=d[d.split_scheme=='formula_random_70_15_15']
 return d.iloc[0]
def summary(m):return f"n={int(m['n']):,}, MAE={fmt(m.RF_MAE)}, RMSE={fmt(m.RF_RMSE)}, R²={fmt(m.RF_R2)}"
def replace_table(d,i,head,rows,size=8):
 old=d.tables[i];t=d.add_table(rows=1,cols=len(head));t.style='Table Grid'
 for c,v in zip(t.rows[0].cells,head):c.text=str(v)
 header=OxmlElement('w:tblHeader');t.rows[0]._tr.get_or_add_trPr().append(header)
 for row in rows:
  for c,v in zip(t.add_row().cells,row):c.text=str(v)
 for ri,row in enumerate(t.rows):
  for c in row.cells:
   for p in c.paragraphs:
    p.paragraph_format.space_after=Pt(0)
    for r in p.runs:r.font.size=Pt(size);r.bold=ri==0
 old._element.addprevious(t._element);old._element.getparent().remove(old._element)
def picture_replace(d,paragraph,path):
 for blip in d.paragraphs[paragraph]._p.xpath('.//a:blip'):
  d.part.related_parts[blip.get(qn('r:embed'))]._blob=Path(path).read_bytes()
def plot_panel(groups,path):
 fig,axes=plt.subplots(1,len(groups),figsize=(5*len(groups),4.4))
 for i,(ax,(g,label)) in enumerate(zip(np.atleast_1d(axes),groups)):
  if len(g)>20000:g=g.sample(20000,random_state=20261107)
  ax.scatter(g.y_true,g.y_pred,s=3,alpha=.25)
  lo=min(g.y_true.min(),g.y_pred.min());hi=max(g.y_true.max(),g.y_pred.max());ax.plot([lo,hi],[lo,hi],'k--',lw=.8)
  ax.set(xlabel='Reported value',ylabel='RF prediction',title=f'({chr(97+i)}) {label}')
 fig.tight_layout();fig.savefig(path,dpi=300);plt.close(fig)
st=pd.read_csv(H/'tebench_baseline_predictions_starrydata_experiment.csv.gz');rv=pd.read_csv(H/'tebench_revision_predictions_starrydata_experiment.csv.gz')
groups=[]
for t,label in [('seebeck_uV_K','Seebeck (µV/K)'),('zT','zT'),('kappa_W_m_K','κ after 0 < κ ≤ 100 (W/m K)')]:
 g=(rv[(rv.target==t)&(rv.model=='RF_QC100')] if t=='kappa_W_m_K' else st[st.target==t]);g=g[g.split_role=='test'];groups.append((g,label))
plot_panel(groups,F/'Fig3_Starrydata_test_parity_S_zT_kappa.png')
k=rv[(rv.model=='RF_QC100')&(rv.split_role=='test')];plot_panel([(k,'Starrydata κ; QC100, paper test')],F/'FigS18_parity_starrydata_experiment_kappa_W_m_K_paper_random_70_15_15.png')
shutil.copy2(F/'FigS18_parity_starrydata_experiment_kappa_W_m_K_paper_random_70_15_15.png',H/'baseline_plots/parity_starrydata_experiment_kappa_W_m_K_paper_random_70_15_15.png')
jp=pd.read_csv(H/'tebench_revision_predictions_jarvis_dft.csv.gz')
plot_panel([(jp[(jp.target==t)&(jp.model=='RF_canonical_split')&(jp.split_role=='test')&(jp.split_scheme=='formula_random_70_15_15')],label) for t,label in [('n-Seebeck','n-type S (µV/K)'),('p-Seebeck','p-type S (µV/K)')]],F/'Fig4_JARVIS_DFT_Seebeck_formula_grouped_test_parity.png')
# Refresh all JARVIS SI parity plots, including leave-out schemes.
for path in F.glob('FigS*_parity_jarvis*.png'):
 name=path.name.split('_parity_jarvis_dft_',1)[1].removesuffix('.png')
 for t in ['n-Seebeck','p-Seebeck','n-powerfact','p-powerfact']:
  if name.startswith(t+'_'):
   scheme=name[len(t)+1:];role='test' if scheme.startswith('formula') else 'leaveout_test'
   g=jp[(jp.target==t)&(jp.model=='RF_canonical_split')&(jp.split_scheme==scheme)&(jp.split_role==role)]
   plot_panel([(g,f'JARVIS {t}; canonical {scheme}')],path)
   shutil.copy2(path,H/'baseline_plots'/('parity_jarvis_dft_'+name+'.png'))
# New comparison figure: same split and cohort for reference and HGB.
comparisons=[('bi2te3_bulk_audited','seebeck_uV_K','Bi₂Te₃ S'),('bi2te3_bulk_audited','zT','Bi₂Te₃ zT'),('starrydata_experiment','seebeck_uV_K','Starry S'),('starrydata_experiment','zT','Starry zT'),('starrydata_experiment','kappa_W_m_K','Starry κ QC100'),('jarvis_dft','n-Seebeck','JARVIS n-S'),('jarvis_dft','p-Seebeck','JARVIS p-S')]
fig,ax=plt.subplots(figsize=(9,5));y=np.arange(len(comparisons))
for idx,(src,t,label) in enumerate(comparisons):
 base='RF_canonical_split' if src=='jarvis_dft' else ('RF_QC100' if t=='kappa_W_m_K' else 'RF_reference_original')
 ax.scatter(metric(src,t,base).RF_R2,idx-.12,c='#2864a1',marker='o',label='Reference RF (current task)' if idx==0 else None)
 ax.scatter(metric(src,t,'HGB_tuned').RF_R2,idx+.12,c='#b68016',marker='s',label='Validation-selected HGB' if idx==0 else None)
 if src=='jarvis_dft':ax.scatter(metric(src,t,'HGB_tuned_structure').RF_R2,idx,c='#148b91',marker='^',label='HGB + structure' if t=='n-Seebeck' else None)
ax.set_yticks(y,[z[2] for z in comparisons]);ax.axvline(0,c='gray',ls='--',lw=.7);ax.set_xlabel('Test R² (source-specific tasks; not a cross-source ranking)');ax.legend(fontsize=8);fig.tight_layout();fig.savefig(F/'Fig5_model_comparison.png',dpi=300);plt.close(fig)
parse='; '.join(f"{s}: {v['failed_records']:,}/{v['records']:,} records fail ({v['failed_distinct_strings']:,} distinct strings), {v['canonical_formulas']:,} matched-key formulas" for s,v in C['parse'].items())
canon='Canonical matching uses pymatgen Composition(strict=True) and get_integer_formula_and_factor(max_denominator=1000000), requiring positive real-element amounts. Whole strings only are parsed: annotations, variables and parse failures remain unmatched; no guessed dopants or leading-token fallback is used for identity. Fractional stoichiometries are rationalised to integer ratios with the stated denominator bound. Verbatim compositions are preserved. '+parse+'.'
structure='Composition-to-JID candidates were enumerated, retaining JARVIS space group, lattice-derived volume, site count and density. '
for src,v in C['structure_matches'].items():structure+=f"{src}: {v['matched_experimental_formulas']:,} matched formulas covering {v['matched_experimental_records']:,} experimental records and {v['candidate_formula_jid_pairs']:,} formula–JID pairs; {v['formulas_with_multiple_jids']:,} formulas have multiple JIDs. "
structure+='Neither experimental table contains atomic coordinates, space group or crystal system (zero evaluable secondary-key comparisons). Workbook lattice a/c alone cannot identify a structure. These are composition candidates, not unique structure matches; no experimental crystal structures were invented.'
qc=f"Starrydata total κ: a new kappa_physical_QC100 flag excludes κ ≤ 0 or κ > 100 W m⁻¹ K⁻¹ from κ-target fitting/evaluation only. This task-specific screening bound is motivated by typical bulk thermoelectric κ of about 0.1–10 W m⁻¹ K⁻¹, rarely above a few tens; thousands suggest unit/digitisation errors. It is not a universal law for all solids, and flagged points are retained in the original data for audit. Of {C['kappa_QC']['all_kappa']:,} κ points, {C['kappa_QC']['all_kappa_new_flag']:,} trigger the new flag. Of 259,059 passing the prior flags, 1,412 exceed 100, 123 exceed 1000 and none are non-positive; 257,647 remain before split join and feature parsing. Other targets and paper/family split roles are unchanged. The point-provenance-only flag index is supplied separately."
prov='The hash-identified local JARVIS extract is jarvis_te.csv (23,558 JIDs; SHA-256 24ac8e6cb16b57bce54bfae1fb42e6ecc71d9f21408229a6bec70b5647e140a4, as recorded in the collection manifest). Its upstream release tag and retrieval date are absent. Preserved original columns are n/p-Seebeck (notebook µV/K), n/p-powerfact (raw PF; notebook µW m⁻¹ K⁻²), ncond/pcond (σ convention unverified), and nkappa/pkappa (electronic κ/τ, not total κ). Existing annotations supply 600 K and 10²⁰ cm⁻³; no per-row τ or tensor-reduction metadata is present. Ref. 7 reports BoltzTraP, CRTA/RBA and τ = 10⁻¹⁴ s for conductivity at the same screening conditions, consistent with but not proof of this extract. No PF numbers were changed: baselines use raw PF; legacy PF extension columns equal raw × 10⁻⁶, conditional on the notebook units. Upstream version, exact σ/κ τ convention and tensor reduction remain unverified; no physical PF magnitude comparison is made. Full evidence and column mapping are supplied in JARVIS_PROVENANCE.md.'
k_test=metric('starrydata_experiment','kappa_W_m_K','RF_QC100');k_own=metric('starrydata_experiment','kappa_W_m_K','RF_QC100','own_paper_holdout')
kr=f"After κ-specific QC, the reference RF gives test {summary(k_test)} and own-paper hold-out {summary(k_own)}. The original failed κ rows are retained as legacy QC-failure results, not overwritten or used as current-task scores. "
strong='A validation-selected HistGradientBoostingRegressor (HGB) was added on the same current splits and the same feature-valid rows: max_leaf_nodes ∈ {15,31}, max_iter 150, learning_rate 0.08, l2_regularization 1, min_samples_leaf 20, early_stopping False, seed 20261107. The lower validation MAE selects the model; only train rows are fitted, with no train+validation refit. For JARVIS a separate two-candidate HGB adds |det(lattice)| volume, number of sites, mass/volume density and numeric space-group number to Magpie (all 23,558 rows have these features). Numeric space group is a coarse code, not a physical distance. The exact chosen hyperparameters and both validation trials are provided in model_selection.json and the metrics CSV. RF_* metric column names are retained for backward compatibility; the model column identifies the actual estimator.'
# Main text
D=Document(N/'manuscript_before_revision.docx');p=D.paragraphs
p[6].text='Machine-learning thermoelectric scores are difficult to compare when source provenance and split groups differ. TEBench organises Starrydata Experiment-labelled curves (30,530 samples, 1,648,315 points, 6,045 papers), a JARVIS-DFT extract (23,558 structures) and an audited bulk Bi₂Te₃ workbook (740 records, 151 DOIs) as separate domains. DFT and experiment are never pooled. Canonical composition keys, paper/family/formula grouping and an eight-paper own-data hold-out support leakage review. The original Bi₂Te₃ Seebeck random forest reaches test R² = 0.935 but own-paper R² = −1.21. A κ-specific physical screening rule retains 257,647 Starrydata points before composition parsing and split joining; the rerun gives test R² = '+fmt(k_test.RF_R2)+'. Validation-selected CPU gradient boosting and structure-derived JARVIS tabular features are evaluated beside preserved random-forest references. Composition-to-JID candidate matches are explicitly distinguished from unique structure identity. Extract hashes and transport-unit limitations are documented. These are proposed tasks and transparent baseline comparisons, not a released benchmark or a claim of state-of-the-art prediction.'
p[22].text='Table 1 Source inventory. Composition counts are distinct successful canonical keys; verbatim strings remain stored. Parse failures are enumerated in ESI S5.'
p[28].text=prov
p[33].text='Table 2 Pairwise overlap using canonical composition keys and normalised DOIs; neither composition nor DOI equality establishes sample or structure identity. JARVIS has no per-material DOI.'
p[35].text='Bi2Te3 and Bi2Te2Se occur in all three sources after canonicalisation. '+structure+' The Starrydata Bi2Te3 family still contains 1,725 samples, 73,314 points and 408 DOIs; 30 DOIs overlap the audited sheet. Both own JALCOM DOIs remain in own_paper_holdout.'
p[37].text=p[37].text.replace('formula string for JARVIS','canonical composition key for JARVIS')+f" Canonicalisation changed {C['jarvis_changed_assignments']:,} JARVIS role assignments; all dependent JARVIS reference tasks, including leave-out training pools, were rerun. Experimental paper and family roles were not reshuffled."
p[38].text='Table 3 Proposed split counts. On the Bi₂Te₃ sheet 25 records are excluded by ML inclusion. The literal NaN composition (Na + N) is preserved and parsed, not mistaken for a missing formula.'
p[42].text='Features. 132 Magpie descriptors (refs. 12–14) plus temperature for experiment; no other transport target is a feature. To preserve the original modelling cohort, the reference leading-formula-token feature fallback is retained for annotated strings; still-unparsable feature rows are counted per target in the metrics. That legacy feature fallback is never used for canonical identity or matching. '+canon
p[43].text='Models. Random forests (ref. 15) and HGB use scikit-learn (ref. 16). The original untuned RF settings and scores are retained (200 trees for Bi₂Te₃/JARVIS; Starrydata 100 trees, 20% bootstrap samples, minimum leaf size 2; seed 20261107). '+strong
p[45].text=qc
p[46].text='Evaluation reports MAE, RMSE and R² for validation, test, own-paper and JARVIS leave-out sets (minimum 10 rows). HGB selection uses validation MAE only; test and own-paper data never enter model selection or fitting. JARVIS leave-out training removes the hold-out from the current canonical formula-training pool. Composition-only HGB is also run on the two JARVIS leave-out tasks; structure-aware HGB is run on the primary formula split only.'
p[48].text='All new runs used local CPU only. Tables retain the original RF reference and add revised RF or validation-selected HGB rows; current versus original JARVIS split versions and legacy versus QC100 κ tasks are labelled. Full-precision metrics and selected hyperparameters are supplied in the ESI and machine-readable CSV/JSON. Fig. 5 compares current-task test R² values within each source.'
p[50].text='Table 4 Audited Bi₂Te₃ paper-split baselines: original RF plus validation-selected HGB for S and zT, on unchanged roles and feature-valid cohorts. MAE columns refer to the named model.'
p[52].text=p[52].text+' Tuned HGB Seebeck test '+summary(metric('bi2te3_bulk_audited','seebeck_uV_K','HGB_tuned'))+'; own-paper '+summary(metric('bi2te3_bulk_audited','seebeck_uV_K','HGB_tuned','own_paper_holdout'))+'. Hyperparameter tuning is not assumed to improve transfer.'
p[56].text='Table 5 Starrydata point-level paper-split baselines. Original κ rows are labelled legacy QC-failure; current κ rows apply 0 < κ ≤ 100 W m⁻¹ K⁻¹. HGB uses the same current rows as its RF comparator; original S/zT references remain unchanged.'
p[58].text=kr+'For κ the training-mean test R² is '+fmt(k_test.mean_R2)+'. HGB test κ '+summary(metric('starrydata_experiment','kappa_W_m_K','HGB_tuned'))+'. S and zT references are unchanged; own-paper sample sizes (36/12/28 points) remain too small for strong transfer claims.'
p[60].text='Fig. 3 Paper-grouped test parity plots for Starrydata reference RF: (a) S (µV K⁻¹), (b) zT, (c) κ after the κ-only 0 < κ ≤ 100 W m⁻¹ K⁻¹ screening rule. Dashed line y = x. Panel (c) is the QC rerun, not the legacy failed baseline.'
p[62].text='Table 6 JARVIS: preserved original-string RF test rows, rerun canonical-split RF and validation-selected composition/structure HGB. S in µV K⁻¹; PF in raw extract units (notebook µW m⁻¹ K⁻²; not independently verified). Original and canonical split scores are different tasks and are not direct algorithm comparisons.'
p[64].text='On the revised canonical formula split, reference RF n-/p-Seebeck test R² values are '+fmt(metric('jarvis_dft','n-Seebeck','RF_canonical_split').RF_R2)+' and '+fmt(metric('jarvis_dft','p-Seebeck','RF_canonical_split').RF_R2)+'. Structure-tabular HGB n-/p-Seebeck gives '+fmt(metric('jarvis_dft','n-Seebeck','HGB_tuned_structure').RF_R2)+' and '+fmt(metric('jarvis_dft','p-Seebeck','HGB_tuned_structure').RF_R2)+'. Both PF carrier targets were also run. The tiny leave-out sets remain indicative only. These DFT scores are not comparable with experimental scores.'
p[69].text='The κ-specific screening removes implausible high values without changing any Seebeck, conductivity or zT selection or split assignment. '+kr+'A screening threshold is a reproducible task definition, not validation of every retained point: source-paper verification, units, anisotropy and material-domain suitability still require review.'
p[70].text='Limitations. The splits remain proposals, and Starrydata Experiment labels have not been source-paper audited. Canonical formula agreement is not specimen identity, and no experimental atomic structures are available for unique polymorph matching. Own-paper exclusion does not prove a laboratory is absent from all training papers. Small own-paper and leave-family test sets give uncertain estimates. The added CPU grid is modest, not an exhaustive model search; structure-aware tabular models are not graph networks.'
p[71].text='Remaining unresolved work is limited to an actual archival deposit/DOI and published frozen release; recovery of the upstream JARVIS release identifier, tensor-reduction and σ/κ relaxation-time conventions; and source-paper/laboratory-provenance validation, including κ-threshold sensitivity. Unique structure matching cannot be completed without experimental atomic structures. These unavailable provenance/structure facts have not been guessed. Large graph-network baselines, exhaustive tuning and matched reruns of prior external benchmarks were not attempted.'
p[73].text='TEBench now includes strict canonical composition matching, a documented κ-specific QC rerun, explicit composition-to-JARVIS candidate multiplicity, local versioned citation metadata and validation-selected CPU baselines including structure-tabular JARVIS models. Original RF references remain preserved. The own-paper Bi₂Te₃ transfer gap motivates reporting independent hold-outs beside grouped tests. Data provenance and small external test sets remain limiting; neither a DOI nor a public v1.0.0 release is claimed by this local revision.'
p[79].text=p[79].text.replace('A DOI for an archived copy of that repository can be added at journal acceptance.','A versioned GitHub release will provide a frozen snapshot, and a DOI will be added when an archive is deposited; local CITATION.cff and RELEASE_NOTES.md prepare v1.0.0 (7 November 2026), but no release or archival DOI has been created. These revision outputs are supplied locally and have not been pushed to the repository.').replace('the exact extract version will be stated if a later revision requires it.','the exact local file hash is reported above, while its upstream release identifier remains unavailable.')
p[81].text+=' The local revision adds complete_tebench_revision.py and refresh_tebench_submission.py, supplied in this package; these additions have not been pushed. Model-selection records, composition/structure audits and exact new metrics are supplied alongside the documents.'
p[107].text='Fig. 3 Starrydata reference RF test parity: S, zT and κ after κ-only QC100 filtering; no other target rows changed.'
# Counts / overlap tables
for idx,src in [(1,'starrydata_experiment'),(2,'jarvis_dft'),(3,'bi2te3_bulk_audited')]:D.tables[0].rows[idx].cells[4].text=f"{C['parse'][src]['canonical_formulas']:,}"
D.tables[0].rows[0].cells[4].text='Canonical formulas'
pair={frozenset([r['source_a'],r['source_b']]):r['canonical_formula_overlap'] for r in C['overlap']}
for i,ab in enumerate([('starrydata_experiment','jarvis_dft'),('starrydata_experiment','bi2te3_bulk_audited'),('jarvis_dft','bi2te3_bulk_audited')],1):D.tables[1].rows[i].cells[1].text=str(pair[frozenset(ab)])
for col,role in [(1,'train'),(2,'val'),(3,'test')]:D.tables[2].rows[4].cells[col].text=f"{C['jarvis_split_counts'][role]:,}"
# New rows beside original baseline tables.
for ti,src in [(3,'bi2te3_bulk_audited'),(4,'starrydata_experiment')]:
 rows=[[c.text for c in r.cells] for r in D.tables[ti].rows][1:]
 if ti==4:
  rows[-2][0]='Legacy κ, test (QC-failure)';rows[-1][0]='Legacy κ, own (QC-failure)'
 for _,m in new[(new.source==src)&new.eval_role.isin(['test','own_paper_holdout'])].iterrows():
  rows.append([f"{m.model}: {m.target} / {m.eval_role}",f"{int(m['n']):,}",fmt(m.RF_MAE),fmt(m.RF_R2),fmt(m.mean_MAE),fmt(m.mean_R2)])
 replace_table(D,ti,['Model / target / set','n','Model MAE','Model R²','Mean MAE','Mean R²'],rows)
rows=[]
for _,m in M[(M.source=='jarvis_dft')&(M.eval_role=='test')].iterrows():rows.append([f"{m.model}: {m.target}",int(m['n']),fmt(m.RF_MAE),fmt(m.RF_R2),fmt(m.mean_MAE),fmt(m.mean_R2)])
replace_table(D,5,['Model / target (test)','n','Model MAE','Model R²','Mean MAE','Mean R²'],rows)
picture_replace(D,59,F/'Fig3_Starrydata_test_parity_S_zT_kappa.png');picture_replace(D,65,F/'Fig4_JARVIS_DFT_Seebeck_formula_grouped_test_parity.png')
D.add_heading('Additional model comparison',level=2);D.add_picture(str(F/'Fig5_model_comparison.png'),width=Cm(16));D.add_paragraph('Fig. 5 Test R² comparison within source-specific current tasks. RF references for Bi₂Te₃/Starrydata S and zT are unchanged; κ uses QC100 and JARVIS uses the canonical formula split. No cross-domain ranking is implied.')
D.save(P/'TEBench_manuscript.docx')
# ESI
D=Document(N/'SI_before_revision.docx');p=D.paragraphs
p[21].text=prov.replace('Ref. 7 reports','The cited JARVIS transport paper (ESI ref. S2) reports')
p[24].text='Seed 20261107; original experimental DOI/paper/family roles unchanged. JARVIS formula grouping is regenerated from canonical keys, changing '+str(C['jarvis_changed_assignments'])+' roles relative to the original string split. Literal NaN is a valid Na–N composition, not missing. '+canon
p[34].text='Table S8 Canonical composition overlap (successful whole-formula parses only) and normalised DOI overlap.'
p[42].text+=' New scripts: complete_tebench_revision.py and refresh_tebench_submission.py (local revision; no upload). '+strong
p[51].text=qc+' '+kr
p[55].text=canon+' '+structure
p[61].text='Fig. S1–S20 show reference RF parity plots. JARVIS panels use the rerun canonical split and corresponding leave-out training pools; Starrydata S18 uses κ-only QC100. Original scores remain in Tables S11–S13 as RF_reference_original. The added comparison panel is Fig. 5 in the main manuscript.'
for i in [44,46,48]:p[i].text=p[i].text.replace('Full baseline metrics','Full original and revised baseline metrics').replace('RF','model')+' The model field distinguishes original RF, revised RF, tuned HGB and structure-tabular HGB. Values shown to five significant digits; CSV contains full precision.'
# Updated S5 counts: recompute from all current split files.
s=json.loads((H/'tebench_splits_summary.json').read_text());ss=pd.read_csv(H/'tebench_split_jarvis_dft.csv.gz',keep_default_na=False)
rows=[]
for key,v in s['schemes'].items():
 for unit,counts in v.items():
  if key.startswith('jarvis_dft:'):
   col=key.split(':')[1]
   counts=(ss[col].value_counts().to_dict() if unit=='materials' else ss.groupby(col).composition_key.nunique().to_dict())
  rows.append([key,unit,'; '.join(f'{k}: {v:,}' for k,v in counts.items())])
replace_table(D,4,['Scheme','Unit','Counts by role'],rows)
for i,ab in enumerate([('starrydata_experiment','jarvis_dft'),('starrydata_experiment','bi2te3_bulk_audited'),('jarvis_dft','bi2te3_bulk_audited')],1):D.tables[7].rows[i].cells[1].text=str(pair[frozenset(ab)])
D.tables[7].rows[0].cells[1].text='Canonical formulas'
replace_table(D,8,['Flag type: source → other source','Flagged rows'],list(C['leakage_flags'].items()))
replace_table(D,9,['Setting','Value'],[['Reference RF','Original settings retained; canonical JARVIS and QC100 κ rerun'],['New model / selection',strong],['κ filter',qc],['Composition identity',canon],['Structure candidate audit',structure],['Parameter selection','Both grid trials and selected parameters are in model_selection.json; chosen leaf counts listed in Table S15 below'],['Own-paper protection','Train mask always role == train; validation used only for HGB selection; eight own DOIs unchanged']])
for idx,src in [(10,'bi2te3_bulk_audited'),(11,'starrydata_experiment'),(12,'jarvis_dft')]:
 rows=[]
 for _,m in M[M.source==src].iterrows():rows.append([f'{m.target}\n{m.model}',f'{m.split_scheme}\n{m.eval_role}',f"{int(m.n_train)}/{int(m['n'])}",fmt(m.RF_MAE),fmt(m.RF_RMSE),fmt(m.RF_R2),f'{fmt(m.mean_MAE)} / {fmt(m.mean_RMSE)} / {fmt(m.mean_R2)}'])
 replace_table(D,idx,['Target / model','Split / set','n train / n','MAE','RMSE','R²','Mean MAE / RMSE / R²'],rows,size=7)
# Current revision validation supersedes the original string-overlap recount.
p[58].text='Table S14 Revision validation. Original collection-builder checks remain historical in the preserved reference summaries; these checks validate current canonical splits and saved prediction metrics.'
validation=json.loads((N/'revision_validation.json').read_text())
replace_table(D,13,['Current revision check','Result'],list(validation.items()))
# Replace SI figures embedded at known original image paragraphs.
for pi,fn in [(72,'FigS6_parity_jarvis_dft_n-Seebeck_formula_random_70_15_15.png'),(74,'FigS7_parity_jarvis_dft_n-Seebeck_leave_BiSbTeSe_only_out.png'),(76,'FigS8_parity_jarvis_dft_n-Seebeck_leave_contains_Bi_and_Te_out.png'),(78,'FigS9_parity_jarvis_dft_n-powerfact_formula_random_70_15_15.png'),(80,'FigS10_parity_jarvis_dft_n-powerfact_leave_BiSbTeSe_only_out.png'),(82,'FigS11_parity_jarvis_dft_n-powerfact_leave_contains_Bi_and_Te_out.png'),(84,'FigS12_parity_jarvis_dft_p-Seebeck_formula_random_70_15_15.png'),(86,'FigS13_parity_jarvis_dft_p-Seebeck_leave_BiSbTeSe_only_out.png'),(88,'FigS14_parity_jarvis_dft_p-Seebeck_leave_contains_Bi_and_Te_out.png'),(90,'FigS15_parity_jarvis_dft_p-powerfact_formula_random_70_15_15.png'),(92,'FigS16_parity_jarvis_dft_p-powerfact_leave_BiSbTeSe_only_out.png'),(94,'FigS17_parity_jarvis_dft_p-powerfact_leave_contains_Bi_and_Te_out.png'),(96,'FigS18_parity_starrydata_experiment_kappa_W_m_K_paper_random_70_15_15.png')]:picture_replace(D,pi,F/fn)
D.add_heading('S11 Revision audits and selected hyperparameters',level=1);D.add_paragraph(canon);D.add_paragraph(structure)
D.add_paragraph('Table S15 Selected HGB hyperparameters. All models share max_iter=150, learning_rate=0.08, l2_regularization=1, min_samples_leaf=20, early_stopping=False, seed=20261107. Leaf count chosen by lower validation MAE on the documented two-candidate grid; no own-paper/test tuning.')
rows=[]
for _,m in new[new.model.str.startswith('HGB')].drop_duplicates(['source','target','model','split_scheme']).iterrows():rows.append([m.source,m.target,m.model,m.split_scheme,json.loads(m.hyperparameters)['max_leaf_nodes']])
t=D.add_table(rows=1,cols=5);t.style='Table Grid'
for c,v in zip(t.rows[0].cells,['Source','Target','Model','Split','Chosen leaves']):c.text=v
for row in rows:
 for c,v in zip(t.add_row().cells,row):c.text=str(v)
for row in t.rows:
 for c in row.cells:
  for r in c.paragraphs[0].runs:r.font.size=Pt(8)
D.add_paragraph('Outstanding provenance: '+prov.replace('Ref. 7 reports','The cited JARVIS transport paper (ESI ref. S2) reports'))
D.save(P/'TEBench_SI.docx')
# Cover letters: change only relevant data-availability sentences if present.
for fn in ['Cover_letter_Digital_Discovery.docx','Cover_letter_ChemRxiv.docx']:
 d=Document(P/fn)
 for p in d.paragraphs:
  if p.text.startswith('Data and code.'):
   p.text=p.text+' Revised metrics, canonical split keys, QC audits and citation metadata are supplied locally with this submission package and have not been pushed. A versioned GitHub release will provide a frozen snapshot; a DOI will be added when an archive is deposited. No archival DOI has been minted.'
  if 'The study also reports a failed thermal-conductivity baseline' in p.text:
   p.text=p.text.split('The study also reports')[0]+'The revised study adds a kappa-only physical screening rule and rerun (test R² = '+fmt(k_test.RF_R2)+'), canonical composition and structure-candidate audits, and validation-selected CPU composition/structure-tabular baselines. The original failed kappa result remains documented as a legacy QC failure.'
  if not p.text.startswith('Data and code.') and ('archival DOI' in p.text or 'journal acceptance' in p.text):
   p.text=p.text+' Local v1.0.0 citation/release metadata are prepared; a versioned GitHub release will provide a frozen snapshot and a DOI will be added when an archive is deposited. No DOI has been minted and this revision has not been pushed.'
 d.save(P/fn)
# Store exact paragraph text for internal cross-checking and parent reporting.
for fn in ['TEBench_manuscript.docx','TEBench_SI.docx']:
 d=Document(P/fn);(N/(fn+'.txt')).write_text('\n'.join(p.text for p in d.paragraphs))
print('Refreshed DOCX and figures; metrics',len(M),'new rows',len(new))
