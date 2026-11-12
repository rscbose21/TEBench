# TEBench release notes

## v1.0.1 (12 November 2026)

This release adds the Starrydata files referenced in the manuscript data
statement, so the public repository matches that statement.

- Adds `data/tebench_starrydata_experiment.csv.gz`, the sample-level
  harmonised Starrydata Experiment table (not the raw curve or point dumps).
- Adds `metrics/tebench_baseline_predictions_starrydata_experiment.csv.gz` and
  `metrics/tebench_revision_predictions_starrydata_experiment.csv.gz`.
- Adds `.zenodo.json` (preprint title, author affiliation, ChemRxiv related
  identifier) for the Zenodo deposit of this version.
- Raw official ThermoelectricMaterials papers, samples and curves files, and
  the intermediate long/point tables, remain unredistributed and are rebuilt
  from the pinned snapshot (SHA-256 hashes in `metrics/download_provenance.json`).
- TEBench v1.0.0 is archived as DOI 10.5281/zenodo.24151805. The concept DOI
  10.5281/zenodo.24151804 always points to the newest version.

See `NOTICE.md` for CC BY 4.0 attribution of the Starrydata-derived files
(Katsura et al., STAM: Methods, 2025, and the original source-paper DOIs) and
for the changes made (harmonisation, flags and predictions).

## v1.0.0 (12 November 2026)

This is the first versioned public snapshot of TEBench, corresponding to the ChemRxiv preprint
S. C. B. Rapaka, *TEBench: a source-labelled thermoelectric data collection with leakage-safe splits
and baselines for machine learning*, ChemRxiv (2026), https://doi.org/10.26434/chemrxiv.15011944.
The manuscript has been submitted to ACS Journal of Chemical Information and Modeling and has not
been accepted. This release is archived on Zenodo as DOI 10.5281/zenodo.24151805
(all versions: 10.5281/zenodo.24151804).

- Sources remain separate: Starrydata Experiment-labelled data, JARVIS DFT,
  and the audited bulk Bi2Te3 workbook; never pool DFT and experiment.
- Seed 20261107; all eight own-paper DOIs remain outside training and validation.
- Canonical pymatgen composition matching, stoichiometric normalization, parse
  failure audit, revised JARVIS formula split, and composition-to-JID candidate table.
- Extra total-kappa flag: kappa <= 0 or kappa > 100 W/(m K); applied to kappa only.
- Original RF scores retained alongside revised RF and validation-selected CPU
  histogram gradient boosting, including structure-derived JARVIS tabular features.
- Extract provenance and unresolved transport-unit/version metadata are explicit.
- Prediction files for JARVIS and Bi2Te3 are in `metrics/`. The Starrydata
  harmonised sample table and Starrydata prediction files were not included in
  v1.0.0; they are added in v1.0.1. The reference files `notes/revision_20261107/reference_metrics.csv`
  and `notes/revision_20261107/reference_jarvis_splits.csv.gz` are included so the
  original RF rows can be reproduced.

See notes/revision_20261107 and metrics/tebench_baseline_metrics.csv for counts,
metrics, model-selection records and limitations. Raw Starrydata dumps are not
redistributed (see NOTICE.md). Upstream licences and attribution are summarised
in NOTICE.md.

## Snapshot candidate (7 November 2026)

Prepared 7 November 2026 (IST) for https://github.com/rscbose21/TEBench.
This section is the original release-metadata note from that date: no tag, GitHub
release, archive deposit or DOI had been created then. The intended snapshot date
in that note was 7 November 2026, not evidence that a release had been published.

- Sources remain separate: Starrydata Experiment-labelled data, JARVIS DFT,
  and the audited bulk Bi2Te3 workbook; never pool DFT and experiment.
- Seed 20261107; all eight own-paper DOIs remain outside training and validation.
- Canonical pymatgen composition matching, stoichiometric normalization, parse
  failure audit, revised JARVIS formula split, and composition-to-JID candidate table.
- Extra total-kappa flag: kappa <= 0 or kappa > 100 W/(m K); applied to kappa only.
- Original RF scores retained alongside revised RF and validation-selected CPU
  histogram gradient boosting, including structure-derived JARVIS tabular features.
- Extract provenance and unresolved transport-unit/version metadata are explicit.

See notes/revision_20261107 and metrics/tebench_baseline_metrics.csv for counts,
metrics, model-selection records and limitations. Raw Starrydata dumps are not
redistributed (see NOTICE.md).

The closing lines of the original 7 November note said that a versioned GitHub
release would later provide a frozen snapshot and that no archival DOI was
asserted yet. That was true on 7 November 2026. It is no longer the current
status: see the v1.0.0 and v1.0.1 sections above for the Zenodo DOIs. Upstream
licences and attribution are summarised in NOTICE.md.
