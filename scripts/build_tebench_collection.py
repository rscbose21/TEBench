#!/usr/bin/env python3
"""Build a LOCAL three-source staging collection, not a modelling dataset.

Run: python3 /workspace/thermogpt/tebench/build_tebench_collection.py
Dependencies: pandas, numpy, openpyxl. No network, training, or splitting.

COMMON_COLUMNS defines the common schema. Blank values mean unavailable or
inapplicable, NEVER zero. Starrydata rows describe whole samples: no averaging
across temperatures/curves, scalar targets remain blank; use original long
points via (SID, sample_id). JARVIS rows describe materials with explicit n/p
extensions: no carrier averaging. Bi2Te3 rows describe original audited records.
All source columns are retained with original__ prefixes (Starrydata metadata,
JARVIS all fields including atoms_json, Bi2Te3 all Data-sheet fields).
CSV row indices are zero-based DATA rows, excluding headers; Excel rows are
one-based worksheet row numbers, including the header at row 1.
"""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from itertools import combinations
import hashlib
import json
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
COMMON_COLUMNS = [
    'tebench_id', 'source', 'domain', 'granularity', 'composition',
    'temperature_K', 'seebeck_uV_K', 'sigma_S_m', 'kappa_total_W_m_K',
    'zT', 'PF_W_m_K2', 'doi', 'paper_id', 'sample_record_id',
    'quality_flags', 'original_file', 'original_sheet', 'original_row',
    'provenance_pointer', 'units_json', 'conditions_note',
]
UNITS = {'temperature_K': 'K', 'seebeck_uV_K': 'uV/K', 'sigma_S_m': 'S/m',
         'kappa_total_W_m_K': 'W/(m K)', 'zT': 'dimensionless',
         'PF_W_m_K2': 'W/(m K^2)'}
FLAGS = ['missing_value', 'missing_temperature', 'composition_missing',
         'composition_mismatch', 'temperature_review', 'physical_sign_review',
         'magnitude_review', 'composition_T_source_repeat', 'sample_T_property_repeat']
PROPS = ['seebeck_uV_K', 'sigma_S_m', 'rho_ohm_m', 'kappa_W_m_K',
         'power_factor_W_m_K2', 'zT']
LONG = HERE / 'starrydata_te_points_experiment.csv.gz'
META = HERE / 'sample_metadata.csv.gz'
JARVIS = PROJECT / 'jarvis_te.csv'
BIO = HERE / 'Bi2Te3_BULK_dataset_v2.xlsx'


def dumps(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def formula_key(series):
    # Only remove whitespace: NOT canonical chemical identity or structure match.
    return series.fillna('').astype(str).str.replace(r'\s+', '', regex=True)


def doi_key(series):
    # Normalize DOI case, whitespace, and standard resolver/doi: prefixes only.
    return (series.fillna('').astype(str).str.strip().str.lower()
            .str.replace(r'^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)', '', regex=True))


def nonempty_set(series, key=formula_key):
    return set(key(series)) - {''}


def counts(series):
    return {str(k): int(v) for k, v in series.fillna('<missing>').value_counts().items()}


def base_table(n, source, domain, granularity):
    out = pd.DataFrame(index=range(n), columns=COMMON_COLUMNS)
    out['source'], out['domain'], out['granularity'] = source, domain, granularity
    out['units_json'] = dumps(UNITS)
    return out


def save_table(table, name):
    assert table.tebench_id.notna().all() and table.tebench_id.is_unique
    path = HERE / name
    table.to_csv(path, index=False, compression={'method': 'gzip', 'mtime': 0})
    return str(path)


def source_stats(table):
    return {'harmonized_rows': len(table),
            'distinct_sample_record_ids': int(table.sample_record_id.nunique()),
            'distinct_nonempty_composition_strings_as_provided': int(table.loc[formula_key(table.composition).ne(''), 'composition'].nunique()),
            'distinct_nonempty_composition_strings_whitespace_stripped': len(nonempty_set(table.composition)),
            'distinct_normalized_DOIs': len(nonempty_set(table.doi, doi_key)),
            'common_scalar_property_nonmissing': {
                c: int(table[c].notna().sum()) for c in UNITS}}


def build_starrydata():
    metadata = pd.read_csv(META, keep_default_na=False)
    assert not metadata.duplicated(['SID', 'sample_id']).any()
    metadata['metadata_csv_row0'] = np.arange(len(metadata))
    aggregates, property_counts, distinct_details = [], [], []
    row_offset = 0
    for chunk in pd.read_csv(LONG, chunksize=200000, keep_default_na=False):
        chunk['long_row0'] = np.arange(row_offset, row_offset + len(chunk))
        row_offset += len(chunk)
        chunk['temperature_K'] = pd.to_numeric(chunk.temperature_K, errors='coerce')
        assert chunk.DataType.eq('Experiment').all()
        for flag in FLAGS:
            # Explicit conversion also supports csvs read as text rather than bool.
            chunk[flag] = chunk[flag].astype(str).str.lower().eq('true').astype(int)
        chunk['any_quality_flag'] = chunk[FLAGS].any(axis=1).astype(int)
        grouped = chunk.groupby(['SID', 'sample_id'], sort=False)
        spec = {'point_count': ('property', 'size'),
                'temperature_min_K': ('temperature_K', 'min'),
                'temperature_max_K': ('temperature_K', 'max'),
                'long_row0_min': ('long_row0', 'min'),
                'long_row0_max': ('long_row0', 'max'),
                'points_with_any_quality_flag': ('any_quality_flag', 'sum')}
        spec.update({f'flag_count__{f}': (f, 'sum') for f in FLAGS})
        aggregates.append(grouped.agg(**spec).reset_index())
        property_counts.append(chunk.groupby(['SID', 'sample_id', 'property']).size().rename('n').reset_index())
        distinct_details.append(chunk[['SID', 'sample_id', 'composition', 'DOI', 'raw_unit', 'property']].drop_duplicates())
    combined = pd.concat(aggregates, ignore_index=True)
    aggregations = {c: ('min' if c.endswith('_min') or c == 'temperature_min_K' else
                        'max' if c.endswith('_max') or c == 'temperature_max_K' else 'sum')
                    for c in combined.columns if c not in ['SID', 'sample_id']}
    samples = combined.groupby(['SID', 'sample_id'], as_index=False).agg(aggregations)
    pc = pd.concat(property_counts).groupby(['SID', 'sample_id', 'property'])['n'].sum().unstack(fill_value=0)
    pc = pc.reindex(columns=PROPS, fill_value=0).rename(columns=lambda p: 'point_count__' + p)
    samples = samples.merge(pc.reset_index(), on=['SID', 'sample_id'], validate='one_to_one')
    details = pd.concat(distinct_details, ignore_index=True).drop_duplicates()
    strings = details.groupby(['SID', 'sample_id']).agg(
        curve_compositions_json=('composition', lambda s: dumps(sorted(set(s)))),
        curve_DOIs_json=('DOI', lambda s: dumps(sorted(set(s)))))
    samples = samples.merge(strings, on=['SID', 'sample_id'], validate='one_to_one')
    joined = samples.merge(metadata, on=['SID', 'sample_id'], how='left',
                           validate='one_to_one', indicator=True)
    assert joined['_merge'].eq('both').all()
    out = base_table(len(joined), 'starrydata_experiment', 'experiment', 'sample')
    out['tebench_id'] = 'starrydata_experiment:SID=' + joined.SID.astype(str) + ':sample=' + joined.sample_id.astype(str)
    out['composition'], out['doi'] = joined.composition, joined.DOI
    out['paper_id'], out['sample_record_id'] = joined.SID.astype(str), joined.sample_id.astype(str)
    out['original_file'], out['original_row'] = str(META), joined.metadata_csv_row0
    out['provenance_pointer'] = [dumps({'metadata_csv_row0': int(r.metadata_csv_row0),
        'long_file': str(LONG), 'SID': int(r.SID), 'sample_id': int(r.sample_id),
        'long_row0_min': int(r.long_row0_min), 'long_row0_max': int(r.long_row0_max),
        'row_bounds_are_not_contiguous_selection': True,
        'original_raw_curve_row_and_point_index_are_in_long_file': True}) for r in joined.itertuples()]
    out['quality_flags'] = [dumps({f: int(r['flag_count__' + f]) for f in FLAGS}) for _, r in joined.iterrows()]
    out['conditions_note'] = 'Metadata-labelled Experiment, not source-paper audited. Scalar T/targets intentionally blank: use long points; no averaging or alignment.'
    extras = samples.drop(columns=['SID', 'sample_id'])
    out = pd.concat([out, joined[['SID', 'sample_id']], extras.reset_index(drop=True),
                     joined[metadata.columns].add_prefix('original__')], axis=1)
    # samples and joined have identical sorted key order; enforce before concatenation.
    assert samples[['SID', 'sample_id']].equals(joined[['SID', 'sample_id']])
    stats = source_stats(out)
    stats.update({'point_rows': row_offset, 'papers_by_SID': int(joined.SID.nunique()),
        'point_DOIs': len(nonempty_set(details.DOI, doi_key)),
        'curve_composition_strings': len(nonempty_set(details.composition)),
        'sample_metadata_total_rows': len(metadata),
        'sample_metadata_duplicate_keys': int(metadata.duplicated(['SID', 'sample_id']).sum()),
        'samples_with_missing_composition': int(formula_key(out.composition).eq('').sum()),
        'property_coverage': {p: {'points': int(out['point_count__'+p].sum()),
                                      'samples': int(out['point_count__'+p].gt(0).sum())} for p in PROPS},
        'flag_point_counts': {f: int(out['flag_count__'+f].sum()) for f in FLAGS},
        'flagged_points_any_flag': int(out.points_with_any_quality_flag.sum()),
        'samples_with_any_flag': int(out.points_with_any_quality_flag.gt(0).sum()),
        'material_family_counts': counts(joined.MaterialFamily.replace('', np.nan)),
        'temperature_bounds_retained_not_validated_K': [float(out.temperature_min_K.min()), float(out.temperature_max_K.max())],
        'raw_property_unit_pairs': details[['property', 'raw_unit']].drop_duplicates().to_dict('records')})
    availability = {p: out['point_count__' + p].gt(0) for p in PROPS}
    stats['samples_S_and_sigma_or_rho_and_total_kappa_and_zT_anywhere_not_aligned'] = int((
        availability['seebeck_uV_K'] & (availability['sigma_S_m'] | availability['rho_ohm_m']) &
        availability['kappa_W_m_K'] & availability['zT']).sum())
    return out, stats, metadata, details


def inspect_candidates():
    # Inventory only: do not assign these mixed/unknown-label points to experiment.
    n = 0
    pairs, papers, comps = set(), set(), set()
    prop_counts, labels = {}, {}
    path = HERE / 'starrydata_te_points_candidates.csv.gz'
    for c in pd.read_csv(path, chunksize=200000, keep_default_na=False,
                         usecols=['SID', 'sample_id', 'composition', 'DataType', 'property']):
        n += len(c)
        pairs.update(map(tuple, c[['SID', 'sample_id']].drop_duplicates().to_numpy()))
        papers.update(c.SID.unique().tolist())
        comps.update(nonempty_set(c.composition))
        for dest, column in [(prop_counts, 'property'), (labels, 'DataType')]:
            for k, v in c[column].value_counts().items(): dest[str(k)] = dest.get(str(k), 0) + int(v)
    return {'file': str(path), 'point_rows': n, 'samples': len(pairs), 'papers_by_SID': len(papers),
            'composition_strings': len(comps), 'point_counts_by_property': prop_counts,
            'point_counts_by_DataType': labels, 'included_in_harmonized_experiment': False}


def inspect_wide():
    path = HERE / 'starrydata_te_experiment_exact_T_wide.csv.gz'
    totals = {p: 0 for p in PROPS}
    n, four = 0, 0
    for c in pd.read_csv(path, chunksize=200000):
        n += len(c)
        for p in PROPS: totals[p] += int(c[p].notna().sum())
        four += int(c[['seebeck_uV_K', 'sigma_S_m', 'kappa_W_m_K', 'zT']].notna().all(axis=1).sum())
    return {'file': str(path), 'rows': n, 'nonmissing_by_property': totals,
            'four_property_exact_T_rows_before_QC': four,
            'warning': 'Existing convenience pivot; conflicting cells omitted, flags remain in long file. Not a training table.'}


def build_jarvis():
    # NaN is also a real formula string (Na + N); do NOT use pandas default NA tokens.
    raw = pd.read_csv(JARVIS, keep_default_na=False)
    out = base_table(len(raw), 'jarvis_dft', 'dft', 'DFT_material_n_and_p_extensions')
    out['tebench_id'] = 'jarvis_dft:' + raw.jid
    out['composition'], out['sample_record_id'], out['paper_id'] = raw.formula, raw.jid, ''
    out['doi'] = ''  # no per-material source-paper DOI exists in this local extract
    out['temperature_K'] = 600.0
    out['original_file'], out['original_row'] = str(JARVIS), np.arange(len(raw))
    out['provenance_pointer'] = [dumps({'csv_row0': i, 'jid': jid,
        'conditions_reference': str(PROJECT / '01_jarvis_thermoelectric_dataset.ipynb')})
        for i, jid in enumerate(raw.jid)]
    out['conditions_note'] = ('600 K and 1e20 cm^-3 from local extraction notebook, not per-row verified. '
        'BoltzTraP constant-relaxation-time / rigid-band approximation; n/p kept separate. '
        'Conductivity units require verification; electronic kappa/tau is NOT total kappa. No zT.')
    target_cols = []
    for carrier in ['n', 'p']:
        mapping = {f'{carrier}_seebeck_uV_K': (f'{carrier}-Seebeck', 1),
                   f'{carrier}_PF_W_m_K2': (f'{carrier}-powerfact', 1e-6),
                   f'{carrier}_sigma_raw_unit_unverified': (f'{carrier}cond', 1),
                   f'{carrier}_electronic_kappa_over_tau_raw': (f'{carrier}kappa', 1)}
        for name, (old, factor) in mapping.items():
            out[name] = pd.to_numeric(raw[old], errors='coerce') * factor
            target_cols.append(name)
    out['doping_cm3_notebook'] = 1e20
    out['quality_flags'] = [dumps({'conditions_and_conductivity_units_not_independently_verified': True,
        'electronic_kappa_over_tau_not_total': True,
        'missing_formula': not bool(formula_key(pd.Series([r.formula])).iloc[0]),
        'no_transport_targets': all(pd.isna(out.loc[i, c]) for c in target_cols),
        'n_Seebeck_positive_review_not_error': bool(out.loc[i, 'n_seebeck_uV_K'] > 0),
        'p_Seebeck_negative_review_not_error': bool(out.loc[i, 'p_seebeck_uV_K'] < 0)})
        for i, r in raw.iterrows()]
    out['units_json'] = dumps({**UNITS, 'n/p_seebeck_uV_K': 'uV/K; local notebook',
        'n/p_PF_W_m_K2': 'W/(m K^2); raw uW/(m K^2) times 1e-6 per notebook',
        'n/p_sigma_raw_unit_unverified': 'as stored; units/tau convention require verification',
        'n/p_electronic_kappa_over_tau_raw': 'notebook describes W/(m K s); unscaled, requires verification'})
    out = pd.concat([out, raw.add_prefix('original__')], axis=1)
    stats = source_stats(out)
    stats.update({'input_records': len(raw), 'unique_jids': int(raw.jid.nunique()),
        'missing_formula_records': int(formula_key(raw.formula).eq('').sum()),
        'papers': None, 'papers_note': 'No material-specific paper DOI in local extract; doi and paper_id are blank. jid is sample_record_id.',
        'property_nonmissing_records': {c: int(out[c].notna().sum()) for c in target_cols},
        'records_without_transport': int(out[target_cols].isna().all(axis=1).sum()),
        'scalar_transport_columns_intentionally_blank': True,
        'n_Seebeck_positive_review_not_error': int(out.n_seebeck_uV_K.gt(0).sum()),
        'p_Seebeck_negative_review_not_error': int(out.p_seebeck_uV_K.lt(0).sum())})
    return out, stats, raw


def build_bi2te3():
    raw = pd.read_excel(BIO, sheet_name='Data', keep_default_na=False)
    out = base_table(len(raw), 'bi2te3_bulk_audited', 'experiment', 'audited_record')
    out['tebench_id'] = 'bi2te3_bulk_audited:' + raw.sample_id
    out['composition'], out['doi'] = raw.composition_formula, raw.reference_doi
    out['paper_id'], out['sample_record_id'] = raw.reference_doi, raw.sample_id
    for new, old, factor in [('temperature_K', 'meas_temp_K', 1),
        ('seebeck_uV_K', 'seebeck_uV_K', 1), ('sigma_S_m', 'sigma_S_cm', 100),
        ('kappa_total_W_m_K', 'kappa_total_W_mK', 1), ('zT', 'zT_at_meas_T', 1),
        ('PF_W_m_K2', 'PF_uW_cmK2', 1e-4)]:
        out[new] = pd.to_numeric(raw[old], errors='coerce') * factor
    out['original_file'], out['original_sheet'], out['original_row'] = str(BIO), 'Data', np.arange(len(raw)) + 2
    out['provenance_pointer'] = [dumps({'workbook': str(BIO), 'sheet': 'Data',
        'excel_row_1based': i + 2, 'sample_id': sid}) for i, sid in enumerate(raw.sample_id)]
    out['quality_flags'] = [dumps({c: r[c] for c in ['qc_flag', 'qc_flag_v2', 'qc_action', 'qc_tier',
        'ml_include', 'is_own_data', 'dir_mismatch']}) for _, r in raw.iterrows()]
    for c in ['is_own_data', 'ml_include', 'qc_tier', 'qc_flag_v2']:
        out[c] = raw[c]
    out['preserved_holdout_label'] = np.where(raw.is_own_data.eq(1), 'own_experiment_holdout_as_supplied',
        np.where(raw.ml_include.eq(1), 'literature_ml_included_as_supplied', 'literature_excluded_as_supplied'))
    out['conditions_note'] = 'Supplied physics-audited bulk-Bi2Te3 record; audit and hold-out preserved unchanged. zT_max is retained only as an original field, not substituted for zT_at_meas_T.'
    out = pd.concat([out, raw.add_prefix('original__')], axis=1)
    stats = source_stats(out)
    stats.update({'input_records': len(raw), 'source_type_counts': counts(raw.source_type),
        'is_own_data_counts': counts(raw.is_own_data), 'ml_include_counts': counts(raw.ml_include),
        'qc_tier_counts': counts(raw.qc_tier), 'direction_mismatch_records': int(raw.dir_mismatch.eq(1).sum()),
        'papers_by_group': {}, 'own_DOIs_also_in_literature': sorted(
            nonempty_set(raw.loc[raw.is_own_data.eq(1), 'reference_doi'], doi_key) &
            nonempty_set(raw.loc[raw.is_own_data.eq(0), 'reference_doi'], doi_key)),
        'own_DOIs_also_in_ml_include_1': sorted(
            nonempty_set(raw.loc[raw.is_own_data.eq(1), 'reference_doi'], doi_key) &
            nonempty_set(raw.loc[raw.ml_include.eq(1), 'reference_doi'], doi_key)),
        'own_records_ml_include_true': int((raw.is_own_data.eq(1) & raw.ml_include.eq(1)).sum()),
        'workbook_sheets': {s: list(pd.read_excel(BIO, sheet_name=s).shape) for s in pd.ExcelFile(BIO).sheet_names}})
    for label, mask in [('literature', raw.is_own_data.eq(0)), ('own_holdout', raw.is_own_data.eq(1)),
                        ('ml_include_1', raw.ml_include.eq(1))]:
        stats['papers_by_group'][label] = {'records': int(mask.sum()),
            'normalized_DOIs': len(nonempty_set(raw.loc[mask, 'reference_doi'], doi_key))}
    return out, stats, raw


def overlap_reports(tables, star_details):
    sets, rows, pair_stats = {}, [], []
    for name, table in tables.items():
        sets[name] = {'formula_string': nonempty_set(table.composition),
                      'normalized_DOI': nonempty_set(table.doi, doi_key)}
    # Primary comparison uses each harmonized source's composition field.
    for a, b in combinations(tables, 2):
        pair = {'source_a': a, 'source_b': b}
        for kind in ['formula_string', 'normalized_DOI']:
            shared = sorted(sets[a][kind] & sets[b][kind])
            pair[kind + '_overlap'] = len(shared)
            for key in shared:
                rows.append({'source_a': a, 'source_b': b, 'key_type': kind, 'shared_key': key,
                    'method': 'remove all whitespace, case-sensitive' if kind == 'formula_string' else
                    'trim + lowercase + remove standard DOI URL/doi: prefix',
                    'not_a_structure_or_record_duplicate_match': True})
        pair_stats.append(pair)
    path = HERE / 'tebench_overlap_keys.csv'
    pd.DataFrame(rows, columns=['source_a', 'source_b', 'key_type', 'shared_key', 'method',
                              'not_a_structure_or_record_duplicate_match']).to_csv(path, index=False)
    return {'matching_basis': 'Harmonized composition field: Starrydata sample_metadata composition, JARVIS formula, Bi2Te3 composition_formula; whitespace removed only.',
        'DOI_method': 'trim/lowercase/remove standard resolver or doi: prefix; exclude blanks; no citation or duplicate audit',
        'pairwise': pair_stats,
        'all_three_formula_strings': sorted(set.intersection(*(s['formula_string'] for s in sets.values()))),
        'all_three_normalized_DOIs': sorted(set.intersection(*(s['normalized_DOI'] for s in sets.values()))),
        'alternate_Starrydata_curve_composition_vs_JARVIS_formula_overlap': len(
            nonempty_set(star_details.composition) & sets['jarvis_dft']['formula_string']),
        'detail_file': str(path)}


def main():
    star, star_stats, meta, details = build_starrydata()
    jarvis, jarvis_stats, jarvis_raw = build_jarvis()
    bi, bi_stats, bi_raw = build_bi2te3()
    tables = {'starrydata_experiment': star, 'jarvis_dft': jarvis, 'bi2te3_bulk_audited': bi}
    outputs = [save_table(t, f'tebench_{name}.csv.gz') for name, t in tables.items()]
    overlap = overlap_reports(tables, details)
    # Family means curator label only, not a parser-verified chemical selection.
    family = star.loc[star['original__MaterialFamily'].eq('Bi2Te3')]
    shared_dois = nonempty_set(bi.doi, doi_key) & nonempty_set(family.doi, doi_key)
    family_note = {'selection_method': 'Starrydata metadata MaterialFamily exactly equals Bi2Te3; not chemical parsing',
        'selected_experiment_samples': len(family),
        'selected_experiment_points': int(family.point_count.sum()),
        'selected_experiment_DOIs': len(nonempty_set(family.doi, doi_key)),
        'shared_normalized_DOIs_with_audited_sheet': len(shared_dois),
        'shared_DOIs': sorted(shared_dois),
        'own_holdout_DOIs_present_in_selected_Starrydata': sorted(
            nonempty_set(bi.loc[bi.is_own_data.eq(1), 'doi'], doi_key) & nonempty_set(star.doi, doi_key)),
        'audited_records_on_shared_DOIs': int(doi_key(bi.doi).isin(shared_dois).sum()),
        'family_samples_on_shared_DOIs': int(doi_key(family.doi).isin(shared_dois).sum()),
        'interpretation': 'Publication/string overlap is a leakage-review cue, not independent experiments or identical records. No merging, overwriting, or averaging.'}
    input_paths = [META, LONG, JARVIS, BIO, HERE/'starrydata_te_points_candidates.csv.gz',
                   HERE/'starrydata_te_experiment_exact_T_wide.csv.gz', PROJECT/'01_jarvis_thermoelectric_dataset.ipynb']
    manifest = []
    for path in input_paths:
        digest = hashlib.sha256()
        with path.open('rb') as f:
            for block in iter(lambda: f.read(1024*1024), b''): digest.update(block)
        manifest.append({'path': str(path), 'bytes': path.stat().st_size, 'sha256': digest.hexdigest()})
    summary = {'stage': 'local collection only; no benchmark/model/split claims',
        'generated_Asia_Calcutta': datetime.now(ZoneInfo('Asia/Calcutta')).isoformat(),
        'common_columns': COMMON_COLUMNS, 'units': UNITS, 'inputs': manifest,
        'input_columns': {'sample_metadata': list(pd.read_csv(META, nrows=0).columns),
            'starrydata_experiment_long': list(pd.read_csv(LONG, nrows=0).columns),
            'jarvis': list(jarvis_raw.columns), 'bi2te3_Data_sheet': list(bi_raw.columns)},
        'csv_text_parsing_note': 'keep_default_na=False preserves literal chemical formulas such as NaN (Na + N). Empty numeric cells are explicitly coerced to missing.',
        'sources': {'starrydata_experiment': star_stats, 'jarvis_dft': jarvis_stats,
                    'bi2te3_bulk_audited': bi_stats},
        'candidate_inventory_not_all_experiment': inspect_candidates(),
        'existing_exact_T_pivot_inventory': inspect_wide(),
        'overlap': overlap, 'bi2te3_family_relation': family_note,
        'outputs': outputs + [overlap['detail_file'], str(HERE/'tebench_bi2te3_relation_notes.md')],
        'not_done': ['canonical composition parsing', 'source-aware deduplication', 'structure matching',
                     'leakage-safe split creation', 'temperature alignment', 'ML training', 'publication/upload']}
    (HERE/'tebench_collection_summary.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    notes = f'''# Audited Bi2Te3 subset and Starrydata family: local staging notes

The supplied workbook has {len(bi)} audited records. It is one labelled subset, not
TEBench as a whole, and is associated with the already-published sole-author
ACS Applied Energy Materials paper (DOI 10.1021/acsaem.6c03156; accepted
22 October 2026). This collection does not rebuild that paper's tabular ML work.
All original Data-sheet fields, QC tiers, inclusion and own-data flags remain.
Its other workbook sheets remain untouched in the source workbook.

Starrydata family selection is the curator label `MaterialFamily == Bi2Te3`,
not a chemical parser: {len(family)} selected Experiment-labelled samples,
{int(family.point_count.sum())} points, {len(nonempty_set(family.doi, doi_key))} normalized DOIs.
There are {len(shared_dois)} shared normalized DOIs with the audited sheet,
covering {family_note['audited_records_on_shared_DOIs']} audited records and
{family_note['family_samples_on_shared_DOIs']} family-labelled Starrydata samples.
The workbook's own and literature DOI sets overlap in
{len(bi_stats['own_DOIs_also_in_literature'])} DOI(s); preserving own-row hold-out
alone is therefore not proof of paper-disjoint evaluation. However, none of
the own-data DOI keys occurs in the supplied `ml_include=1` literature rows;
the shared literature rows are already excluded.

Two own-data DOI keys also occur in the selected Starrydata experiments:
{', '.join(family_note['own_holdout_DOIs_present_in_selected_Starrydata'])}.
Preserve this cross-source leakage-review warning before constructing any splits.

No sample identity, structure identity, independent replication, or equivalence
of Bi2Te3 vs Bi2Te3.00 is inferred. Shared papers can carry distinct specimens,
temperatures or directions; those require source-paper review before deduplication.
Starrydata has metadata labels rather than the supplied workbook's physics audit.
Its values never replace or average with audited values. JARVIS stays DFT-only.

Starrydata: local research staging only; no external sharing/upload. Official
free-use statement / NIMS CC BY 4.0 listing and snapshot details are in README.
Cite Katsura et al., STAM Methods (2025), DOI 10.1080/27660400.2025.2506976,
and the original source-paper DOIs as appropriate.

Shared DOI keys (case/prefix normalized; not a duplicate-record verdict):
''' + '\n'.join('- ' + d for d in sorted(shared_dois)) + '\n'
    (HERE/'tebench_bi2te3_relation_notes.md').write_text(notes)
    print(json.dumps({'source_counts': {k: {'rows': len(v), 'file': outputs[i]} for i,(k,v) in enumerate(tables.items())},
                      'overlap': overlap['pairwise'], 'summary': str(HERE/'tebench_collection_summary.json')}, indent=2))


if __name__ == '__main__':
    main()
