# TEBench — source-labelled thermoelectric data collection, proposed splits and CPU baselines

TEBench keeps three thermoelectric sources as separate source- and domain-labelled tables: Starrydata
Experiment-labelled curves (ThermoelectricMaterials project), a JARVIS-DFT transport extract and an audited bulk
Bi2Te3 workbook. It provides proposed leakage-safe split keys (paper-, family- and formula-grouped, plus an
own-paper hold-out that is never used for fitting), cross-source leakage flags and CPU baselines. DFT and
experimental targets are never pooled. It is a research collection with proposed tasks, not a released benchmark.

Manuscript: S. C. B. Rapaka, *TEBench: a source-labelled thermoelectric data collection with leakage-safe splits
and baselines for machine learning*.

## Current state: revision of 7 November 2026

- **Composition identity.** Whole composition strings are parsed with pymatgen `Composition(strict=True)` and
  normalised with `get_integer_formula_and_factor(max_denominator=1000000)`. Strings that cannot be parsed
  (annotations such as `Bi0.5Sb1.5Te3 + 2 mass% Te`, variables, dopant notes) stay unmatched; nothing is guessed.
  Canonical keys are in the `canonical_formula` column; per-string results are in
  `notes/revision_20261107/composition_parse_*.csv`. This replaces the whitespace-stripped string matching
  described in the first-pass notes below.
- **Splits.** JARVIS formula groups were regenerated from canonical keys (seed 20261107; 1,221 role changes).
  Experimental paper and family roles are unchanged. All eight own-paper DOIs stay out of training and
  validation in every source and scheme.
- **κ screening.** For the Starrydata total-κ task only, the flag `kappa_physical_QC100` excludes κ ≤ 0 or
  κ > 100 W m⁻¹ K⁻¹ (1,412 of the 259,059 points that pass the earlier flags). The flag index is
  `notes/revision_20261107/kappa_QC100_flag_index.csv`; flagged points are not deleted.
- **Baselines.** `metrics/tebench_baseline_metrics.csv` holds 114 rows: the 40 original random-forest rows
  (`RF_reference_original`) and 74 revision rows (revised RF, validation-selected HistGradientBoosting and, for
  JARVIS, HistGradientBoosting with structure-derived features). The `model` column names the estimator; the
  `RF_*` metric column names are kept for backward compatibility. Selection records are in
  `notes/revision_20261107/model_selection.json`.
- **Structure candidates.** Composition-to-JID candidates, with multiplicity, are in
  `notes/revision_20261107/experimental_jarvis_structure_candidates.csv`. They are composition candidates, not
  unique structure matches.
- **Release.** `CITATION.cff` and `RELEASE_NOTES.md` describe v1.0.0 (7 November 2026). No tagged release or
  archival DOI exists yet; an archived snapshot with a DOI will be added later.

The first-pass staging notes further down are kept for provenance. Where they describe whitespace-stripped
string matching, string-grouped JARVIS splits, the unscreened κ baseline or "no tuning", the revision above
supersedes them.

## Repository layout

| Path | Contents |
|---|---|
| `data/` | Audited Bi2Te3 workbook; harmonised JARVIS and Bi2Te3 tables; composition/DOI overlap keys |
| `splits/` | Split keys for all three sources and cross-source leakage flags |
| `metrics/` | Metrics, JARVIS and Bi2Te3 predictions, collection and split summaries, download provenance |
| `notes/revision_20261107/` | Revision audits: composition parsing, structure candidates, κ flag index, model selection, JARVIS provenance |
| `plots/` | Parity plots |
| `scripts/` | Collection, split, baseline and revision scripts |

Raw Starrydata curve and point tables are not redistributed; `NOTICE.md` gives the licences, the pinned
snapshot and how to rebuild them.

## Reproducing the results

The scripts were run with all inputs and outputs in one working folder: each script reads and writes files next
to itself. A rerun therefore needs the files from `data/`, `splits/` and `metrics/` copied next to the scripts,
with `notes/revision_20261107/` as a subfolder, plus inputs that are not in this repository:

- the raw Starrydata ThermoelectricMaterials files of the pinned snapshot (`metrics/download_provenance.json`),
  rebuilt with `build_starrydata.py` and `build_tebench_collection.py`;
- the local JARVIS extract `jarvis_te.csv` (size and SHA-256 in `notes/revision_20261107/JARVIS_PROVENANCE.md`);
- `notes/revision_20261107/reference_metrics.csv` and `reference_jarvis_splits.csv.gz`, which
  `complete_tebench_revision.py` reads to keep the original RF rows.

Order: `build_tebench_collection.py`, `validate_tebench_collection.py`, `build_tebench_splits.py`, then
`complete_tebench_revision.py`. Do not run `run_tebench_baselines.py` on its own after the revision: it
regenerates only the original RF rows and overwrites `tebench_baseline_metrics.csv`.
`refresh_tebench_submission.py` only rebuilds manuscript documents and figures.

## First-pass staging notes (7 November 2026)

The notes below record how the collection was first built. Counts and file names are those of the first pass.

### Official sources and reproducibility
- Web system: https://www.starrydata2.org/
- Official download instructions: https://starrydata.nims.go.jp/hp/en/manual/download/
- Daily download portal: https://starrydata.github.io/starrydata_datasets/
- Official repository: https://github.com/starrydata/starrydata_datasets
- Frozen monthly archives: https://figshare.com/projects/Starrydata_datasets/155129
- Citation: https://starrydata.nims.go.jp/hp/cite/

Downloaded only the official `ThermoelectricMaterials` project, not every project in the database (organic thermoelectrics are a separate project and are not included here). Three public `.csv.gz` files: papers, samples, curves. No login required. Download URLs: `https://github.com/starrydata/starrydata_datasets/releases/latest/download/ThermoelectricMaterials_{papers,samples,curves}.csv.gz`. Raw files and manifest were retained locally (not redistributed); all three SHA-256 hashes were verified against the saved manifest (`metrics/download_provenance.json`). The latest URL changes, so reuse these saved bytes/hashes, not an unpinned future download. The manifest records the exact snapshot and original counts. Snapshot time converted from its JST value: **6 November 2026, 22:30:01 IST**. Manifest generation: **7 November 2026, 04:27:48 IST**.

The documented `latest` release route was used. No monthly Figshare snapshot DOI is claimed for these GitHub bytes; the nearest monthly archive (`20261101_starrydata2`) is listed in `NOTICE.md`.

### License and attribution
Official manual verbatim: “Starrydata2 data are free to use for both commercial and non-commercial purposes.”
NIMS MatDaCs directory explicitly lists **“License | CC BY 4.0”**: https://mat-dacs.dxmt.nims.go.jp/en/list/392 . CC BY 4.0: https://creativecommons.org/licenses/by/4.0/ . This permits reuse and sharing with attribution, a license link, and indication of changes. The daily files themselves do not carry a separate attached license in the download; retain this provenance and verify the license on the eventual archived release before public redistribution.

Official citation instruction: “To use the Starrydata2 web system and datasets, please cite one of the following papers and, if necessary, cite the original source papers.” For individual samples/curves, the official citation page further requests the original source paper (DOI is preserved here).

Preferred project citation, copied from official citation page:
Yukari Katsura, Masaya Kumagai, Tomoya Mato, Yu Takada, Yuki Ando, Erina Fujita, Fumikazu Hosono, Eiji Koyama, Farhan Mudasar, Ton Nu Thanh Phuong, Naoto Saito, Yoshihiro Sakamoto, Atsumi Tanaka, Dewi Yana, Kaoru Kimura, Koji Tsuda, Masahiko Demura. **Starrydata: from published plots to shared materials data.** Science and Technology of Advanced Materials: Methods **5**, 1 (2025), 2506976. https://doi.org/10.1080/27660400.2025.2506976

Earlier project paper: Yukari Katsura et al. **Data-driven analysis of electron relaxation times in PbTe-type thermoelectric materials.** Science and Technology of Advanced Materials **20** (2019), 511–520. https://doi.org/10.1080/14686996.2019.1603885

### Raw schema and joins
- Papers: SID, DOI, URL, issued, author, title, journal, volume, issue, pages, ISSN, publisher, project names, creation date.
- Samples: SID, sample_id, sample_name, composition, composition_details, DOI, dates, sample_info (JSON).
- Curves: SID, sample_id, DOI, composition, figure_id, figure_name, prop_x, prop_y, unit_x, unit_y, x/y JSON arrays, dates, project_names, comments. One row is a digitized curve, not a measurement point.
- Use **(SID, sample_id)**, never composition alone, to join samples and curves. Validate many-to-one. Historical April–September 2026 exports had sample-id collisions; the selected snapshot is after the official correction. Figures should be identified by (SID, figure_id).
- `sample_info` includes MaterialFamily, DataType, Form, FabricationProcess, electrical/thermal measurement metadata, density/grain-size fields where supplied. These are incomplete and retained in `sample_metadata.csv.gz`. There are no guaranteed crystallographic coordinates or unique structure mappings.

### Cleaning and files
Rebuild: `python3 build_starrydata.py` (requires pandas/numpy). Script reads only the three official raw tables and the formula column of the local JARVIS extract `jarvis_te.csv`.

1. Select only `prop_x == Temperature`, `unit_x == K` and canonical Seebeck coefficient, Electrical conductivity, Electrical resistivity, Thermal conductivity / total thermal conductivity, Power factor, ZT labels. Do NOT confuse lattice/electronic κ with total κ; do NOT treat dimensional Z (K^-1) as zT.
2. Explode paired x/y arrays, retaining curve-row and point-index provenance. Numeric failures are missing, not zeros. Noncanonical axes/labels, inverse-T/log properties, unknown units, invalid arrays are excluded with reasons (`excluded_curves.csv.gz`). Inventory: `property_unit_inventory.csv`. Broad aliases need later manual review; this is a conservative subset.
3. Unit conversions: S V/K → μV/K ×10^6; conductivity ohm^-1 m^-1 = S/m; S/cm → S/m ×100; resistivity Ω cm → Ω m ×0.01; κ in W m^-1 K^-1; PF in W m^-1 K^-2; zT dimensionless. Only recognized actual unit strings are used. Stored raw value/unit/factor makes conversions auditable. No sign changes.
4. `starrydata_te_points_candidates.csv.gz`: all selected points, including unknown/reference DataType. **Do not call all these confirmed experimental data.** `starrydata_te_points_experiment.csv.gz`: only samples explicitly labelled `DataType = Experiment`. This is metadata-based, not a source-paper audit; comments can still contain mixed/calculated data.
5. Primary long schema: curve_row (zero-based original CSV row), point_index, SID, sample_id, figure_id, DOI, curve composition, temperature_K, property, raw_value, raw_unit, conversion_factor, converted value, sample name/composition, DataType/MaterialFamily/Form, and quality flags.
6. Remove only repeated identical (T,value,property) points **within the same sample/curve**; audit `removed_exact_duplicate_points.csv.gz`. Coarse (composition,T,source DOI,property) repeats and sample/T/property repeats are FLAGGED, not blindly discarded: distinct specimens, orientations and processing conditions must not be collapsed. Equivalent curves across figures/papers still need source-aware review.
7. Flags: missing/nonfinite T or value; missing/mismatching curve/sample compositions; T≤0 or T>2000 K; σ/ρ/κ≤0; PF/zT<0; |S|>1000 μV/K or zT>5. These are review heuristics, not proof of erroneous measurements. Positive Seebeck above +700 μV/K is NOT inherently invalid; experimental carrier labels are not assigned from DFT n/p conventions. Flagged values remain, not silently deleted.
8. `starrydata_te_experiment_exact_T_wide.csv.gz`: explicitly labelled experimental sample+exact-T pivot. Conflicting values for a property at the same sample/T are not averaged; excluded from that pivot cell and logged in `conflicting_sample_T_properties.csv.gz`. Missing σ may be calculated as 1/ρ only when ρ>0, flagged `sigma_derived_from_rho`. No interpolation, rounded-temperature matching, or computed zT/PF. All-property coverage at exact T will be sparse because separate digitized curves have slightly different T coordinates. Wide table is a convenience, not a QC-approved training set: consult long-table flags and metadata.

`summary.json` gives auditable counts, property availability, flags, material-family labels, and overlap. `jarvis_exact_formula_overlap.csv` is whitespace-stripped exact-string overlap with all raw Starrydata samples; not structural validation or chemically canonical composition matching. Formula strings such as Bi2Te3 and Bi2Te3.0 may fail this conservative match. Formula equivalence, isotope/variable/dopant parsing and polymorphism remain unresolved.

### Still needed before publication / modelling (first-pass list)
Several items were addressed later (canonical parsing, splits, baselines); see *Current state* above.
- The supplied `Bi2Te3_BULK_dataset_v2.xlsx` is now staged (740 audited records, including 30 own experimental hold-out records). Its supplied units, sample IDs, processing, QC and inclusion flags are preserved. Remaining needs include source-paper/uncertainty/repeat review and explicit permission before any external release.
- DOI/source audit of conflicts, composition/sample-name inconsistencies, unknown DataType, digitization and physical outliers. Some source records have sample names apparently inconsistent with composition; do not silently correct these.
- Source-aware de-duplication across review/reference papers, canonical composition parsing, and complete processing metadata.
- Crystallographic structure matching (experiment does not uniquely specify a DFT structure).
- Temperature alignment policy with uncertainty; exact-T coverage is not the number of experimentally complete samples.
- Fixed paper/sample-aware and composition/family-held-out splits; leave-Bi-Sb-Te-Se-out files; no splits or models had been run at this stage. Keep related specimens and paper-derived duplicate curves from leaking across splits.
- DFT→experiment is not a direct apples-to-apples task: JARVIS transport uses fixed temperature/doping and approximations; experimental T, carrier concentration, microstructure, direction, and κ contributions vary. Do not pool DFT/experimental target values without explicit domain labels.
- Hypotheses in the outline (e.g. noise imposes a ceiling, graphs never help new formulas) are NOT established conclusions from these data. A novel benchmark claim needs literature review and repeated baseline tests.

### Observed counts in this first pass

These retain the first-pass context; composition counts here are as-provided strings unless specified. The recomputed three-source counts and whitespace-stripped matching keys are distinguished below.
- Official downloaded project: **9,558 papers; 55,743 samples; 158,401 curves; 28,507 nonempty composition strings**.
- Selected canonical thermoelectric candidates: **2,342,194 points / 47,797 samples**. These include unspecified/reference DataType and must not all be presented as verified experiments.
- Explicit Experiment-labelled selection: **1,648,315 points; 30,530 samples; 6,045 papers; 18,724 nonempty composition strings**.
- Experiment-labelled zT: **222,838 points from 15,670 samples**.
- All S, reported σ or resistivity, total κ and zT somewhere on a sample's curves: **13,198 samples**. This is sample-level availability before QC, NOT matching-temperature completeness; resistivity must be positive to be converted. The strict exact-T pivot contains only **62 four-property rows**, before QC review.
- Experiment-labelled raw retained T range **−18.20086 to 2013.663 K** is visibly not all physical: 64 temperature-review points. Never report the negative minimum as a valid measurement temperature. After removing all three numerical review-flag classes: **0.000869844 to 1999.76 K**, 1,639,376 points (still not source-audited).
- Experiment-labelled flags: 4,093 physical-sign, 4,784 magnitude, 1,138 missing-composition points. Flags can overlap. No selected numeric values/T were missing; other properties are often absent. 64,291 coarse composition/T/source-repeat points were flagged; 3,721 sample/T/property-repeat points. These counts concern repeated rows, not proven erroneous records.
- Exactly duplicated points removed within curves: **340**, across the candidate selection.
- Most frequent specified material-family labels in selected experiments: Bi2Te3 1,725; Perovskite 1,694; Oxide 1,647; Skutterudite 1,580; Half-Heusler 1,374; Cobaltite 1,019; PbTe 933. Family label missing in 10,942 selected samples. Labels are curator categories and are not disjoint chemical superfamilies.
- Exact-string JARVIS overlap: **650 formulas** with all raw sample compositions; **475** with selected Experiment-labelled compositions. JARVIS extract contains **18,475** distinct formula strings when literal `NaN` (Na + N) is preserved; the earlier default-pandas count of 18,474 incorrectly treated that formula as missing. See the three-source parsing note below. These are conservative string matches, NOT structure matches.


### Three-source collection

This is a research collection, **not a finished benchmark**, and not a new model
or novelty result. Starrydata curve and point tables are not redistributed (see
`NOTICE.md`). Its official free-use / NIMS CC BY 4.0 notes and frozen
snapshot provenance remain above. Cite Katsura et al., STAM Methods (2025),
DOI **10.1080/27660400.2025.2506976**, and original source-paper DOIs as appropriate.

#### Rebuild and files

```bash
# run in the working folder described under 'Reproducing the results'
python3 build_tebench_collection.py
python3 validate_tebench_collection.py
```

Dependencies: Python 3, pandas, numpy, openpyxl. Both scripts operate locally.
The builder reads the existing inputs, hashes their bytes, recomputes counts,
and writes separate source-labelled tables, without changing source files.
Rebuilding replaces **only its generated staging outputs**. Text is read with
`keep_default_na=False`: chemical formula `NaN` must not be mistaken for a
missing-value token. Missing numeric cells are explicitly converted to missing.

Files written by the collection builder (in this repository under `data/`, `metrics/` and `notes/`; the Starrydata table is not redistributed):

- `build_tebench_collection.py`: readable source-specific staging builder.
- `tebench_starrydata_experiment.csv.gz`: one sample per row; existing long-table pointers.
- `tebench_jarvis_dft.csv.gz`: one DFT material per row; n/p targets in separate extensions.
- `tebench_bi2te3_bulk_audited.csv.gz`: one supplied audited record per row, including exclusions/hold-outs.
- `tebench_collection_summary.json`: recomputed counts, flags, units, input column inventory, SHA-256 hashes, overlaps.
- `tebench_overlap_keys.csv`: pairwise matched composition-string / normalized DOI keys, not sample matches.
- `tebench_bi2te3_relation_notes.md`: labelled-family and own-data hold-out caveats.
- `validate_tebench_collection.py`, `tebench_collection_validation.json`: reproducible conservation/provenance checks; not source-paper validation.

#### Recomputed source inventory

| Source label | Domain / granularity | Rows / records | Papers / DOIs | Composition strings, as supplied / whitespace removed |
|---|---|---:|---|---:|
| `starrydata_experiment` | experiment / sample | 30,530 samples pointing to 1,648,315 retained points | 6,045 SIDs / 6,045 DOI keys | 18,724 / 18,674 |
| `jarvis_dft` | DFT / material | 23,558 unique JIDs | Material-specific paper DOI absent; no paper count inferred | 18,475 / 18,475 |
| `bi2te3_bulk_audited` | experiment / audited record | 740 unique record IDs | 151 DOI keys | 646 / 644 |

Input column counts: Starrydata long table **28**, sample metadata **15**
(**55,743** total metadata rows, no duplicate SID/sample_id keys); JARVIS
**20** columns; workbook `Data` **89** columns. Workbook auxiliary sheets are
not added as extra measurements: `Summary` 39 rows, `CHANGELOG` 101,
`QC_flagged` 48, `Vocab_map` 265. Their originals stay in the unchanged workbook.

The **2,342,194 candidate points / 47,797 samples / 8,557 SIDs** are inventoried
only, NOT all designated experimental and NOT added to the harmonized experiment
selection. Candidate point labels: Experiment 1,648,315; blank 676,143;
Reference 14,298; Unknown 1,928; NeedCheck 909; Other 601.

#### Property availability, before new source-paper QC

Starrydata availability means somewhere on a sample's curves, not simultaneous
measurement, aligned temperature, or physically validated completeness:

| Property | Retained points | Samples |
|---|---:|---:|
| Seebeck (uV/K) | 486,762 | 25,537 |
| Conductivity (S/m) | 185,422 | 12,766 |
| Resistivity (ohm m) | 294,214 | 11,850 |
| Total thermal conductivity (W/(m K)) | 259,110 | 17,152 |
| Power factor (W/(m K^2)) | 199,969 | 13,568 |
| zT (dimensionless) | 222,838 | 15,670 |

**13,198** samples have S + (sigma or rho) + total kappa + zT somewhere, not
necessarily at the same T. The existing exact-T wide file was recounted:
**1,634,273 rows**, only **62** rows with S/sigma/total-kappa/zT before QC.
No new long-point copy or pivot was created. All original point-level flags,
raw units, SIDs, sample_ids, DOI, curve_row and point_index stay in the existing
long table. The staging sample table supplies flag counts and pointers, not
averaged point values. **73,696** points / **7,370** samples carry at least one
of the nine retained flags (repeat flags included); no such rows were dropped.

JARVIS has **23,218** nonmissing records for each of n/p Seebeck, PF,
conductivity and electronic kappa/tau; **340** records have no transport values.
There is no total kappa or zT target. The local notebook documents 600 K and
10^20 cm^-3, constant-relaxation-time / rigid-band approximations; these are
annotated as notebook-supplied conditions, not newly verified per-row metadata.
Seebeck and PF units follow that notebook. Conductivity units/tau conventions
need verification, so conductivity remains explicitly `raw_unit_unverified`;
electronic kappa/tau is unscaled, NEVER total experimental kappa.

Audited Bi2Te3 nonmissing properties: T **740**, S **715**, sigma **710**,
total kappa **688**, zT_at_meas_T **687**, PF **711**. There are **710** literature
records / **144** DOI keys and **30** own experimental records / **8** DOI keys.
The supplied `ml_include=1` population is **681** records / **141** DOI keys;
all **59** excluded records remain in the staging table, including all own data.
QC tiers: **692 A**, **19 B**, **29 C**; **25** directional mismatches remain flagged.
These counts are descriptive of the supplied audit, not new audit conclusions.

#### Common schema and missing-value semantics

Every harmonized table has the following columns:

```
tebench_id, source, domain, granularity, composition, temperature_K, seebeck_uV_K, sigma_S_m, kappa_total_W_m_K, zT, PF_W_m_K2, doi, paper_id, sample_record_id, quality_flags, original_file, original_sheet, original_row, provenance_pointer, units_json, conditions_note
```

- `source` and `domain` prevent pooling unlabeled DFT and experimental targets.
  `granularity` distinguishes samples, DFT materials and audited records.
- `composition` is verbatim from sample metadata / JARVIS formula / workbook
  composition_formula. Starrydata curve composition strings are also retained
  separately as JSON; no canonical chemistry is inferred.
- Scalar units: T K; S uV/K; sigma S/m; total kappa W/(m K); zT dimensionless;
  PF W/(m K^2). `units_json` records units and source-specific caveats.
- Starrydata sample scalar T/target cells intentionally stay blank; use
  `temperature_min_K`, `temperature_max_K`, `point_count__*` and the exact long
  file selection `(SID, sample_id)`. Bounds in `long_row0_min/max` are not a
  contiguous selection. Point flags are not cleared by the sample aggregation.
- JARVIS scalar target cells intentionally stay blank rather than averaging n/p.
  Extensions: `n_seebeck_uV_K`, `p_seebeck_uV_K`, `n_PF_W_m_K2`, `p_PF_W_m_K2`,
  `n_sigma_raw_unit_unverified`, `p_sigma_raw_unit_unverified`,
  `n_electronic_kappa_over_tau_raw`, `p_electronic_kappa_over_tau_raw`,
  `doping_cm3_notebook`. Raw PF is multiplied by 1e-6 from notebook-stated
  uW/(m K^2); no kappa/tau scaling or zT calculation is attempted.
- JARVIS `doi` and `paper_id` are blank (no per-material paper data); its JID is
  `sample_record_id`. A zero shared DOI-key count with JARVIS means unavailable
  paper metadata, NOT demonstrated publication independence.
- Bi2Te3 conversions: sigma S/cm x100 -> S/m; PF uW/(cm K^2) x1e-4 -> W/(m K^2).
  S, total kappa and zT_at_meas_T pass through; zT_max is not substituted.
  All **89** original columns are retained as `original__*`, including processing,
  original units, notes, QC fields, inclusion flags, lattice/electronic quantities.
- Starrydata metadata and all **20** original JARVIS columns (including structures
  in atoms_json) are likewise retained with `original__` prefixes. Audited
  `is_own_data`, `ml_include`, `qc_tier`, `qc_flag_v2` are also easy-access columns.
  `preserved_holdout_label` only describes supplied labels; it is NOT a new split.
- `original_row` uses zero-based data rows for CSV, but **one-based Excel worksheet
  rows (header included)** for the workbook; `original_sheet` specifies `Data`.
  `provenance_pointer` states the convention explicitly. Blanks are missing or
  inapplicable, never zero. Read formula/metadata text without default NA tokens.

#### Conservative overlap and Bi2Te3 relation (first pass: string matching, superseded by canonical keys)

Composition matching removes all whitespace, otherwise preserves strings and
case. It does not equate Bi2Te3, Bi2Te3.0 and Bi2Te3.00. DOI matching trims,
lowercases, and removes a standard `doi:` or DOI resolver prefix only; blank
keys are excluded. These are string/publication overlaps, not structure or
record-duplicate matches.

| Source pair | Shared composition-string keys | Shared DOI keys |
|---|---:|---:|
| starrydata_experiment / jarvis_dft | 475 | 0 |
| starrydata_experiment / bi2te3_bulk_audited | 37 | 46 |
| jarvis_dft / bi2te3_bulk_audited | 1 | 0 |

The only composition-string key shared by all three is **Bi2Te3**.
The earlier JARVIS count of 18,474 was a pandas missing-token artefact:
`JVASP-36327` has literal formula **NaN**, and its retained atoms_json contains
**Na and N**. There are 18,475 nonempty JARVIS formula strings. Starrydata
18,724 as-supplied strings become 18,674 whitespace-stripped keys; this reduction
is string normalization, not a chemical deduplication.

Starrydata's exact curator family label `MaterialFamily == Bi2Te3` selects
**1,725** samples / **73,314** points / **408** DOI keys. This is not a parsed
chemical family. **30** of those DOI keys overlap the audited workbook,
covering **150** audited records and **169** family-labelled samples; all
selected Starrydata experiments, including other family labels, overlap **46**
audited DOI keys. Nothing is merged, averaged, or overwritten.

The workbook's own and literature sets share **one DOI**,
`10.1021/acsaenm.3c00649`: the four literature records on that DOI are already
`ml_include=0`. No own-data DOI overlaps supplied `ml_include=1` literature.
However, **two own-data DOI keys also occur in selected Starrydata experiments**:
`10.1016/j.jallcom.2021.158621` and `10.1016/j.jallcom.2020.157828`.
Preserve this cross-source leakage warning before designing combined experiments.
A supplied row-level hold-out is not a benchmark-wide leakage-safe split.

The audited sheet is **one experimental subset**, not the entire benchmark.
TEBench does not recreate the author's ACS Applied Energy Materials
bulk-Bi2Te3 tabular ML paper, DOI **10.1021/acsaem.6c03156**, nor claim that
previously published work as a new contribution.

#### Not claimed / remaining work

No finished benchmark, independent-test claim, canonical chemical identity,
structure equivalence, model score, noise ceiling, graph-model conclusion, or
novelty claim follows from this collection. Before modelling/publication:

1. Implement/document canonical composition parsing and unresolved variables/dopants.
2. Audit original papers and perform source-aware, sample-aware deduplication,
   including the cross-source own-data DOI overlaps; do not discard distinct specimens.
3. Match structures explicitly; formula overlap does not identify a polymorph.
4. Design paper/sample/composition/family leakage-safe splits, respecting existing
   own-data and QC exclusions. No final train/test files or proposed split files were created in this collection step.
5. Define temperature/carrier/direction alignment and uncertainty policies, and
   independently verify JARVIS transport units, relaxation-time conventions and conditions.
6. Review retained Starrydata physical, temperature, magnitude and repeat flags;
   Experiment is a metadata label, not a source-paper audit. The retained range
   includes -18.20086 K and 2013.663 K; those bounds are not valid measurement claims.
7. Confirm release permissions and pinned Starrydata archive attribution before
   any future external sharing.

### Proposed leakage-safe splits (first pass; JARVIS groups later regenerated from canonical keys)

Built by `build_tebench_splits.py` (seed `20261107`). Not an official benchmark release.
Summary with all counts: `tebench_splits_summary.json`.

How it works: each paper's (normalized DOI) train/val/test bucket comes from a seeded SHA-256 hash of the DOI
(~70/15/15 by paper), so the same DOI gets the same bucket in Starrydata and in the audited sheet. Whole papers
never straddle splits. Own-paper DOIs (all 8 `is_own_data==1` DOIs in the workbook, including the two JALCOM
papers 10.1016/j.jallcom.2020.157828 and 10.1016/j.jallcom.2021.158621) are role
`own_paper_holdout` and never train/val, in every scheme and source.

Files:
- `tebench_split_bi2te3_bulk_audited.csv.gz`: `split__own_holdout_default` (own = independent test; literature
  `ml_include=0` excluded as flagged) and `split__paper_random_70_15_15`.
- `tebench_split_starrydata_experiment.csv.gz`: `split__paper_random_70_15_15`, `split__leave_Bi2Te3_family_out`,
  `split__family_fold_5` (whole Starrydata `MaterialFamily` curator labels per fold; label-based, not a chemical parser;
  samples with no label excluded; 206 papers span >1 family, flagged in `extra__doi_spans_multiple_families`).
- `tebench_split_jarvis_dft.csv.gz`: DFT-only. `split__formula_random_70_15_15` (grouped by formula string),
  `split__leave_contains_Bi_and_Te_out`, `split__leave_BiSbTeSe_only_out`. Never mixed with experimental targets.
- `tebench_cross_source_leakage_flags.csv.gz`: records sharing a normalized DOI or whitespace-stripped composition
  string with another source. Flags only; no values merged/averaged/overwritten.

Limitations: composition matching is string equality after whitespace removal only. Starrydata family labels are used
verbatim (e.g. " Tetrahedrite" vs "tetrahedrites", "Germinide" vs "Germanide" are separate labels).
4 workbook rows marked Literature (BLK-644..647) carry own DOI 10.1021/acsaenm.3c00649 and were placed in
`own_paper_holdout`.

### CPU baselines (first pass: untuned RF; see Current state for the revision)

Script: `run_tebench_baselines.py` (CPU only, ~5 min on 8 cores). Outputs: `tebench_baseline_metrics.csv`,
`tebench_baseline_summary.json`, `tebench_baseline_predictions_<source>.csv.gz`, `baseline_plots/*.png` (parity plots from real test predictions).

- Model: sklearn 1.9.1 `RandomForestRegressor`, random_state=20261107, no tuning (val reported only).
  Bi2Te3 + JARVIS: 200 trees. Starrydata (point-level, 155k-333k training points): 100 trees, min_samples_leaf=2, max_samples=0.2.
- Features: matminer Magpie (132 composition descriptors) + temperature_K for experimental sources; JARVIS composition only.
  If a composition string does not parse, only its leading formula token is used (additives like "+ 2 mass% Te" or notes in brackets are ignored); still-unparsable rows are dropped and counted. No other transport property is used as a feature.
- One model per source and target; DFT and experiment never pooled. Mean-of-train baseline reported beside each score.
- Bi2Te3 audited: `split__paper_random_70_15_15`, excluded_ml_include_0 skipped; own_paper_holdout is an extra test only.
- JARVIS: n/p-Seebeck and n/p-powerfact on `split__formula_random_70_15_15`; leave-out tests train on formula-random train rows minus the hold-out formulas.
- Starrydata: point-level (every measured T point is a row; no averaging or interpolation) for Seebeck, zT and Starrydata thermal conductivity; points with missing/magnitude/sign/temperature review flags dropped; unflagged extreme values kept.
- Not done: no tuning, no graph/structure models, no GPU, no zT from DFT, no reproduction of the published ACS AEM Bi2Te3 study. Scores are baselines under PROPOSED splits only.
