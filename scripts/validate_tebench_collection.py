#!/usr/bin/env python3
"""Read-only scientific/provenance checks; writes a local validation report only."""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd
from build_tebench_collection import COMMON_COLUMNS, FLAGS, PROPS, formula_key, doi_key

HERE = Path(__file__).resolve().parent
summary = json.loads((HERE / 'tebench_collection_summary.json').read_text())
checks = {}
tables = {}
for source in ['starrydata_experiment', 'jarvis_dft', 'bi2te3_bulk_audited']:
    table = pd.read_csv(HERE / f'tebench_{source}.csv.gz', keep_default_na=False)
    tables[source] = table
    assert set(COMMON_COLUMNS).issubset(table.columns)
    assert table.tebench_id.is_unique
    assert table.source.eq(source).all()
    assert len(table) == summary['sources'][source]['harmonized_rows']
    checks[source + '_schema_unique_ids_rowcount'] = True

# Check every original source column, not just a selection. Numeric comparison
# permits only float CSV round-trip noise; all text/metadata must match exactly.
def assert_original_columns(raw, output):
    assert len(raw) == len(output)
    for col in raw.columns:
        original = raw[col]
        preserved = output['original__' + col]
        if pd.api.types.is_numeric_dtype(original):
            assert np.allclose(original, pd.to_numeric(preserved), rtol=1e-12, atol=1e-12), col
        else:
            assert original.astype(str).equals(preserved.astype(str)), col

jarvis = tables['jarvis_dft']
jraw = pd.read_csv(HERE.parent / 'jarvis_te.csv', keep_default_na=False)
assert_original_columns(jraw, jarvis)
assert jarvis.paper_id.eq('').all() and jarvis.doi.eq('').all()
assert jarvis.loc[jarvis.sample_record_id.eq('JVASP-36327'), 'composition'].iloc[0] == 'NaN'
assert set(json.loads(jraw.loc[jraw.jid.eq('JVASP-36327'), 'atoms_json'].iloc[0])['elements']) == {'Na', 'N'}
for carrier in ['n', 'p']:
    for new, old, factor in [(f'{carrier}_seebeck_uV_K', f'{carrier}-Seebeck', 1),
        (f'{carrier}_PF_W_m_K2', f'{carrier}-powerfact', 1e-6),
        (f'{carrier}_sigma_raw_unit_unverified', f'{carrier}cond', 1),
        (f'{carrier}_electronic_kappa_over_tau_raw', f'{carrier}kappa', 1)]:
        assert np.allclose(pd.to_numeric(jarvis[new], errors='coerce'),
            pd.to_numeric(jraw[old], errors='coerce') * factor, equal_nan=True)
assert jarvis[['seebeck_uV_K', 'sigma_S_m', 'kappa_total_W_m_K', 'zT', 'PF_W_m_K2']].eq('').all().all()
checks['jarvis_all_original_columns_and_carrier_conversions'] = True
checks['literal_NaN_formula_is_Na_plus_N_not_missing'] = True

bi = tables['bi2te3_bulk_audited']
braw = pd.read_excel(HERE / 'Bi2Te3_BULK_dataset_v2.xlsx', sheet_name='Data', keep_default_na=False)
assert_original_columns(braw, bi)
assert bi.original_row.tolist() == list(range(2, len(braw) + 2))
for new, old, factor in [('temperature_K', 'meas_temp_K', 1), ('seebeck_uV_K', 'seebeck_uV_K', 1),
    ('sigma_S_m', 'sigma_S_cm', 100), ('kappa_total_W_m_K', 'kappa_total_W_mK', 1),
    ('zT', 'zT_at_meas_T', 1), ('PF_W_m_K2', 'PF_uW_cmK2', 1e-4)]:
    assert np.allclose(pd.to_numeric(bi[new], errors='coerce'),
        pd.to_numeric(braw[old], errors='coerce') * factor, equal_nan=True)
assert bi.loc[bi.is_own_data.eq(1), 'ml_include'].eq(0).all()
checks['bi2te3_all_89_original_columns_conversions_holdout_and_excel_rows'] = True

star = tables['starrydata_experiment']
meta = pd.read_csv(HERE / 'sample_metadata.csv.gz', keep_default_na=False)
selected = meta.iloc[star.original_row].reset_index(drop=True)
assert_original_columns(selected, star)
assert star.SID.equals(selected.SID) and star.sample_id.equals(selected.sample_id)
assert star[['temperature_K', 'seebeck_uV_K', 'sigma_S_m', 'kappa_total_W_m_K', 'zT', 'PF_W_m_K2']].eq('').all().all()
# Independently recount source point flags, properties and sample keys.
n = 0
properties = {p: 0 for p in PROPS}
flags = {f: 0 for f in FLAGS}
keys = set()
for c in pd.read_csv(HERE / 'starrydata_te_points_experiment.csv.gz', chunksize=200000,
    usecols=['SID', 'sample_id', 'property', 'DataType'] + FLAGS):
    n += len(c)
    assert c.DataType.eq('Experiment').all()
    keys.update(map(tuple, c[['SID', 'sample_id']].drop_duplicates().to_numpy()))
    for p in PROPS: properties[p] += int(c.property.eq(p).sum())
    for f in FLAGS: flags[f] += int(c[f].sum())
assert keys == set(map(tuple, star[['SID', 'sample_id']].to_numpy()))
assert n == int(star.point_count.sum())
for p in PROPS: assert properties[p] == int(star['point_count__' + p].sum())
for f in FLAGS: assert flags[f] == int(star['flag_count__' + f].sum())
checks['starrydata_original_metadata_rows_and_point_property_flag_conservation'] = True

for entry in summary['inputs']:
    digest = hashlib.sha256()
    with Path(entry['path']).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''): digest.update(block)
    assert digest.hexdigest() == entry['sha256'], entry['path']
checks['all_input_hashes_match_builder_manifest'] = True

for pair in summary['overlap']['pairwise']:
    a, b = tables[pair['source_a']], tables[pair['source_b']]
    for key, column, normalize in [('formula_string_overlap', 'composition', formula_key),
                                    ('normalized_DOI_overlap', 'doi', doi_key)]:
        shared = (set(normalize(a[column])) - {''}) & (set(normalize(b[column])) - {''})
        assert len(shared) == pair[key]
checks['pairwise_overlap_recount'] = True
report = {'all_checks_passed': True, 'checks': checks,
          'scope': 'File/schema/row/provenance/conversion conservation only; not a source-paper or scientific validity audit.'}
(HERE / 'tebench_collection_validation.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
