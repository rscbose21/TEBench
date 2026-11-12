# TEBench release notes

## v1.0.0 (12 November 2026)

This is the first versioned public snapshot of TEBench, corresponding to the ChemRxiv preprint
S. C. B. Rapaka, *TEBench: a source-labelled thermoelectric data collection with leakage-safe splits
and baselines for machine learning*, ChemRxiv (2026), https://doi.org/10.26434/chemrxiv.15011944.
The manuscript has been submitted to ACS Journal of Chemical Information and Modeling and has not
been accepted. A Zenodo DOI will be minted from this GitHub release; no archival DOI is asserted here.

- Sources remain separate: Starrydata Experiment-labelled data, JARVIS DFT,
  and the audited bulk Bi2Te3 workbook; never pool DFT and experiment.
- Seed 20261107; all eight own-paper DOIs remain outside training and validation.
- Canonical pymatgen composition matching, stoichiometric normalization, parse
  failure audit, revised JARVIS formula split, and composition-to-JID candidate table.
- Extra total-kappa flag: kappa <= 0 or kappa > 100 W/(m K); applied to kappa only.
- Original RF scores retained alongside revised RF and validation-selected CPU
  histogram gradient boosting, including structure-derived JARVIS tabular features.
- Extract provenance and unresolved transport-unit/version metadata are explicit.
- Prediction files for the Starrydata experiment baselines and revision are included
  in `metrics/`. The reference files `notes/revision_20261107/reference_metrics.csv`
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

A versioned GitHub release will provide a frozen snapshot. An archival DOI will
be added when an archive is deposited. No DOI is asserted here. Upstream
licences and attribution are summarised in NOTICE.md.
