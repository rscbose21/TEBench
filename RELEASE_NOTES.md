# TEBench v1.0.0 — snapshot candidate

Prepared 7 November 2026 (IST) for https://github.com/rscbose21/TEBench.
This file and CITATION.cff prepare release metadata only: no tag, GitHub release,
archive deposit or DOI has been created. The release date is the intended snapshot
date, not evidence that a release has been published.

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
