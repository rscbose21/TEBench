"""Build PROPOSED leakage-safe split keys for TEBench (paper 1).

These are proposed split assignments only - NOT an official benchmark release.
No models are trained and no data leaves this box.

Main ideas (beginner-friendly):
  * Every record keeps its provenance columns (tebench_id, source, domain, ...).
  * Papers (normalized DOIs) are never split across train/val/test.
  * A paper's train/val/test bucket comes from a seeded hash of its DOI, so the
    SAME DOI lands in the SAME bucket in Starrydata and in the audited sheet.
  * The user's own papers (own hold-out DOIs) are never in train or val.
  * JARVIS DFT is split only within itself (no DOIs exist there).
"""
import hashlib, json
from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd

SEED = 20261107
BUCKETS = (0.70, 0.15, 0.15)  # train / val / test fractions, by paper (group)
N_FAMILY_FOLDS = 5
# Confirmed by the user on 7 Nov 2026: these are his own papers only.
USER_CONFIRMED_OWN_DOIS = ['10.1016/j.jallcom.2020.157828', '10.1016/j.jallcom.2021.158621']
STATUS = 'PROPOSED split keys (not an official benchmark release; no models trained)'
KEEP = ['tebench_id', 'source', 'domain', 'granularity', 'composition', 'doi',
        'paper_id', 'sample_record_id', 'original_file', 'original_sheet', 'original_row']


def doi_key(series):
    # Same rule as build_tebench_collection.py: trim, lowercase, drop doi.org / doi: prefix.
    return (series.fillna('').astype(str).str.strip().str.lower()
            .str.replace(r'^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)', '', regex=True))


def formula_key(series):
    # Whitespace-stripped string only. NOT a chemical parser: Bi2Te3 != Te3Bi2 here.
    return series.fillna('').astype(str).str.replace(r'\s+', '', regex=True)


def hash_fraction(key):
    """Deterministic number in [0, 1) for a group key, using the fixed SEED."""
    h = hashlib.sha256(f'{SEED}|{key}'.encode()).hexdigest()
    return int(h[:12], 16) / 16 ** 12


def bucket(key):
    f = hash_fraction(key)
    return 'train' if f < BUCKETS[0] else ('val' if f < BUCKETS[0] + BUCKETS[1] else 'test')


def counts(roles):
    return {k: int(v) for k, v in roles.value_counts().sort_index().items()}


def save(df, name, scheme_cols):
    out = df[KEEP + ['doi_norm', 'composition_key'] + [c for c in df.columns if c.startswith('extra__')] + scheme_cols].copy()
    out.insert(0, 'split_status', STATUS)
    out.to_csv(f'{name}.csv.gz', index=False, compression='gzip')
    return f'{name}.csv.gz'


summary = {'status': STATUS, 'seed': SEED, 'paper_bucket_fractions_train_val_test': BUCKETS,
           'generated_Asia_Calcutta': datetime.now(ZoneInfo('Asia/Kolkata')).isoformat(),
           'grouping_method': 'seeded sha256 hash of normalized DOI (or formula key for JARVIS); '
                              'fractions are by group count, so record fractions vary',
           'doi_normalization': 'trim + lowercase + remove https://(dx.)doi.org/ or doi: prefix',
           'composition_matching': 'whitespace-stripped string equality only; no chemical parsing, '
                                   'element-order or stoichiometry normalization',
           'schemes': {}, 'files': []}

# ---------------- 1. Audited bulk Bi2Te3 sheet ----------------
bi = pd.read_csv('tebench_bi2te3_bulk_audited.csv.gz', low_memory=False)
bi['doi_norm'] = doi_key(bi.doi)
bi['composition_key'] = formula_key(bi.composition)
bi['extra__is_own_data'] = bi.is_own_data
bi['extra__ml_include'] = bi.ml_include
bi['extra__source_type'] = bi.original__source_type
bi['extra__qc_tier'] = bi.qc_tier

own_dois_workbook = set(bi.loc[bi.is_own_data.eq(1), 'doi_norm']) - {''}
own_dois = sorted(own_dois_workbook | set(USER_CONFIRMED_OWN_DOIS))
summary['own_paper_dois_forced_out_of_train_and_val'] = own_dois
summary['user_confirmed_own_dois'] = USER_CONFIRMED_OWN_DOIS
summary['user_confirmed_dois_present_in_workbook_own_rows'] = [d for d in USER_CONFIRMED_OWN_DOIS if d in own_dois_workbook]
summary['own_rows_with_blank_doi'] = int((bi.is_own_data.eq(1) & bi.doi_norm.eq('')).sum())
lit_on_own_doi = bi.is_own_data.eq(0) & bi.doi_norm.isin(own_dois)
summary['literature_rows_on_own_dois'] = int(lit_on_own_doi.sum())


def bi_role_default(r):
    if r.is_own_data == 1 or r.doi_norm in own_dois:
        return 'own_paper_holdout'          # independent test = the user's own data
    if r.ml_include != 1:
        return 'excluded_ml_include_0'      # workbook already flags these
    if r.doi_norm == '':
        return 'excluded_no_doi'
    return 'train_pool'                     # literature used for training


bi['split__own_holdout_default'] = bi.apply(bi_role_default, axis=1)
bi['split__paper_random_70_15_15'] = [
    role if role != 'train_pool' else bucket(d)
    for role, d in zip(bi.split__own_holdout_default, bi.doi_norm)]
f = save(bi, 'tebench_split_bi2te3_bulk_audited', ['split__own_holdout_default', 'split__paper_random_70_15_15'])
summary['files'].append(f)
for s in ['split__own_holdout_default', 'split__paper_random_70_15_15']:
    summary['schemes'][f'bi2te3_bulk_audited:{s}'] = {
        'records': counts(bi[s]),
        'papers': {k: int(v) for k, v in bi[bi.doi_norm.ne('')].groupby(s).doi_norm.nunique().items()}}
summary['bi2te3_records_on_user_confirmed_dois'] = {
    d: int(bi.doi_norm.eq(d).sum()) for d in USER_CONFIRMED_OWN_DOIS}

# ---------------- 2. Starrydata experiment samples ----------------
st = pd.read_csv('tebench_starrydata_experiment.csv.gz', low_memory=False)
st['doi_norm'] = doi_key(st.doi)
st['composition_key'] = formula_key(st.composition)
st['extra__point_count'] = st.point_count
st['extra__MaterialFamily'] = st.original__MaterialFamily.fillna('')
# A sample can list curve DOIs too; treat it as own-paper if ANY of its DOIs is own.
curve_dois = st.curve_DOIs_json.fillna('[]').map(json.loads)
st['extra__all_dois_norm'] = [
    sorted(set(doi_key(pd.Series([d] + list(c))).tolist()) - {''}) for d, c in zip(st.doi, curve_dois)]
st['is_own_paper'] = [any(d in own_dois for d in ds) for ds in st.extra__all_dois_norm]
st['extra__multi_doi_sample'] = st.extra__all_dois_norm.map(len) > 1
st['extra__all_dois_norm'] = st.extra__all_dois_norm.map(json.dumps)
summary['starrydata_samples_with_more_than_one_doi'] = int(st.extra__multi_doi_sample.sum())


def st_base(r):
    if r.is_own_paper:
        return 'own_paper_holdout'
    if r.doi_norm == '':
        return 'excluded_no_doi'
    return None


base = st.apply(st_base, axis=1)
st['split__paper_random_70_15_15'] = [b if isinstance(b, str) else bucket(d) for b, d in zip(base, st.doi_norm)]

# Leave-Bi2Te3-family-out: curator MaterialFamily label, not a chemistry parser.
fam = st.extra__MaterialFamily
st['split__leave_Bi2Te3_family_out'] = [
    'own_paper_holdout' if o else ('excluded_no_family_label' if f_ == '' else ('test' if f_ == 'Bi2Te3' else 'train'))
    for o, f_ in zip(st.is_own_paper, fam)]
# Leave-family-out k-fold: each whole MaterialFamily goes to one fold (seeded hash).
st['split__family_fold_5'] = [
    'own_paper_holdout' if o else ('excluded_no_family_label' if f_ == '' else f'fold_{int(hash_fraction("family|" + f_) * N_FAMILY_FOLDS)}')
    for o, f_ in zip(st.is_own_paper, fam)]
# Papers spanning >1 family can leak between family folds: flag them.
pf = st[st.doi_norm.ne('') & fam.ne('')].groupby('doi_norm').extra__MaterialFamily.nunique()
st['extra__doi_spans_multiple_families'] = st.doi_norm.isin(pf[pf > 1].index)

schemes = ['split__paper_random_70_15_15', 'split__leave_Bi2Te3_family_out', 'split__family_fold_5']
f = save(st, 'tebench_split_starrydata_experiment', schemes)
summary['files'].append(f)
for s in schemes:
    summary['schemes'][f'starrydata_experiment:{s}'] = {
        'samples': counts(st[s]),
        'points': {k: int(v) for k, v in st.groupby(s).point_count.sum().items()},
        'papers': {k: int(v) for k, v in st[st.doi_norm.ne('')].groupby(s).doi_norm.nunique().items()}}
summary['starrydata_family_fold_members'] = {
    f'fold_{i}': sorted({f_ for f_ in fam.unique() if f_ and int(hash_fraction('family|' + f_) * N_FAMILY_FOLDS) == i})
    for i in range(N_FAMILY_FOLDS)}
summary['starrydata_family_note'] = 'MaterialFamily is the Starrydata curator label; no chemistry was inferred.'
summary['starrydata_samples_missing_family_label'] = int(fam.eq('').sum())
summary['starrydata_papers_spanning_multiple_families'] = int((pf > 1).sum())
own_st = st[st.is_own_paper]
summary['starrydata_own_paper_holdout'] = {
    'samples': int(len(own_st)), 'points': int(own_st.point_count.sum()),
    'by_doi': {d: {'samples': int(st.extra__all_dois_norm.str.contains(d, regex=False).sum()),
                   'points': int(st.loc[st.extra__all_dois_norm.str.contains(d, regex=False), 'point_count'].sum())}
               for d in own_dois}}

# ---------------- 3. JARVIS DFT (own domain only) ----------------
ja = pd.read_csv('tebench_jarvis_dft.csv.gz', low_memory=False)
ja['doi_norm'] = ''
ja['composition_key'] = formula_key(ja.composition)
ja['extra__BiSbTeSe_only'] = ja.original__BiSbTeSe_only
ja['extra__contains_Bi_and_Te'] = ja.original__contains_Bi_and_Te
ja['split__formula_random_70_15_15'] = [
    'excluded_no_formula' if k == '' else bucket('jarvis_formula|' + k) for k in ja.composition_key]
ja['split__leave_contains_Bi_and_Te_out'] = ['test' if v else 'train' for v in ja.original__contains_Bi_and_Te.astype(bool)]
ja['split__leave_BiSbTeSe_only_out'] = ['test' if v else 'train' for v in ja.original__BiSbTeSe_only.astype(bool)]
schemes = ['split__formula_random_70_15_15', 'split__leave_contains_Bi_and_Te_out', 'split__leave_BiSbTeSe_only_out']
f = save(ja, 'tebench_split_jarvis_dft', schemes)
summary['files'].append(f)
for s in schemes:
    summary['schemes'][f'jarvis_dft:{s}'] = {
        'materials': counts(ja[s]),
        'formula_groups': {k: int(v) for k, v in ja.groupby(s).composition_key.nunique().items()}}
# Leave-out schemes: check formula groups do not straddle train/test (polymorphs share formula).
summary['jarvis_note'] = ('DFT domain only; never mix with experimental targets. No DOI grouping possible. '
                          'Leave-out flags come from existing columns in jarvis_te.csv.')

# ---------------- 4. Cross-source leakage flags (no merged values) ----------------
rows = []
srcs = {'starrydata_experiment': st, 'bi2te3_bulk_audited': bi, 'jarvis_dft': ja}
for kind, col in [('doi', 'doi_norm'), ('composition', 'composition_key')]:
    sets = {n: set(d[col]) - {''} for n, d in srcs.items()}
    for n, d in srcs.items():
        others = {m: s for m, s in sets.items() if m != n}
        sub = d[d[col].ne('')][['tebench_id', 'source', 'domain', 'sample_record_id', 'doi', 'composition', col]]
        for m, s in others.items():
            hit = sub[sub[col].isin(s)].copy()
            if len(hit):
                hit['shared_key_type'] = kind
                hit['shared_key'] = hit[col]
                hit['also_in_source'] = m
                rows.append(hit.drop(columns=[col]))
flags = pd.concat(rows, ignore_index=True)
flags.insert(0, 'note', 'leakage flag only; values not merged, averaged or overwritten')
flags.to_csv('tebench_cross_source_leakage_flags.csv.gz', index=False, compression='gzip')
summary['files'].append('tebench_cross_source_leakage_flags.csv.gz')
shared_doi = sorted(set(st.doi_norm) & set(bi.doi_norm) - {''})
bi_roles = bi.groupby('doi_norm').split__paper_random_70_15_15.agg(lambda x: sorted(set(x)))
st_roles = st.groupby('doi_norm').split__paper_random_70_15_15.agg(lambda x: sorted(set(x)))
summary['cross_source'] = {
    'flag_rows_by_type_and_pair': {f'{a}:{b}->{c}': int(v) for (a, b, c), v in
                                   flags.groupby(['shared_key_type', 'source', 'also_in_source']).size().items()},
    'shared_dois_starrydata_vs_audited': len(shared_doi),
    'shared_dois_in_Starrydata_Bi2Te3_family': len(set(shared_doi) & set(st.loc[fam.eq('Bi2Te3'), 'doi_norm'])),
    'shared_dois_with_same_role_both_sources_paper_random': int(sum(bi_roles[d] == st_roles[d] for d in shared_doi)),
    'shared_dois_with_role_mismatch': [d for d in shared_doi if bi_roles[d] != st_roles[d]],
}

# ---------------- 5. Sanity checks ----------------
checks = {
    'no_own_doi_in_train_or_val_bi2te3': not bi[bi.doi_norm.isin(own_dois)].split__paper_random_70_15_15.isin(['train', 'val']).any(),
    'no_own_doi_in_train_or_val_starrydata': not st[st.is_own_paper].split__paper_random_70_15_15.isin(['train', 'val']).any(),
    'each_doi_one_role_starrydata_ignoring_excluded': bool((st[st.doi_norm.ne('') & ~st.split__paper_random_70_15_15.str.startswith('excluded')].groupby('doi_norm').split__paper_random_70_15_15.nunique() == 1).all()),
    'each_doi_one_role_bi2te3_ignoring_excluded': bool((bi[bi.doi_norm.ne('') & ~bi.split__paper_random_70_15_15.str.startswith('excluded')].groupby('doi_norm').split__paper_random_70_15_15.nunique() == 1).all()),
    'each_formula_one_role_jarvis': bool((ja.groupby('composition_key').split__formula_random_70_15_15.nunique() == 1).all()),
    'row_counts_preserved': {'starrydata': len(st), 'bi2te3': len(bi), 'jarvis': len(ja)},
}
summary['checks'] = {k: (bool(v) if isinstance(v, (bool,)) or hasattr(v, 'item') else v) for k, v in checks.items()}
with open('tebench_splits_summary.json', 'w') as fh:
    json.dump(summary, fh, indent=2, default=str)
print(json.dumps(summary, indent=1, default=str))
