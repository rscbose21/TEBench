# TEBench

Source-labelled thermoelectric data collection with leakage-safe splits and CPU baselines for machine learning.

**Author:** Subash Chandra Bose Rapaka, Scientist C, Centre for Materials for Electronics Technology (C-MET), Thrissur, Kerala, India ([ORCID 0000-0002-6499-8741](https://orcid.org/0000-0002-6499-8741)).

TEBench keeps three sources in one schema but **does not pool DFT and experiment into one training table**:

1. **Starrydata experiment** (rebuild from the official snapshot; not redistributed here)
2. **JARVIS DFT** thermoelectric/transport extract
3. **Audited bulk Bi₂Te₃** workbook (literature plus an own-paper hold-out)

The collection date for the files in this repository is 7 November 2026 (Asia/Calcutta). Random seeds used for splits and baselines: `20261107`.

This repository is the public code and derived-file companion to the TEBench manuscript (preprint/journal submission in preparation). It is not a claim that the three sources may be mixed as if they were one experiment.

## Contents

- [What is included](#what-is-included)
- [What is not included](#what-is-not-included)
- [Key design choices](#key-design-choices)
- [Install](#install)
- [Layout and how to run](#layout-and-how-to-run)
- [Citation](#citation)

## What is included

- `scripts/` — collection, validation, leakage-safe splits, and Random Forest baselines
- `data/` — audited Bi₂Te₃ table (Excel + CSV) and the JARVIS DFT extract
- `splits/` — paper-grouped / formula-grouped / own-paper hold-out keys, including Starrydata record identifiers and split roles (not the property table)
- `metrics/` — baseline metrics, summaries, and Bi₂Te₃/JARVIS prediction files
- `plots/` — parity plots from the CPU baselines
- `notes/` — relation notes for the Bi₂Te₃ sheet versus Starrydata

## What is not included

Raw Starrydata curve and point dumps are **not** in this repository. Rebuild them from the official [Starrydata ThermoelectricMaterials](https://github.com/starrydata/starrydata_datasets) snapshot (see `NOTICE.md`) before running the Starrydata parts of the collection and baseline scripts.

Pin the archived snapshot DOI and re-check the licence before any public redistribution of derived Starrydata files. NIMS MatDaCs currently lists Starrydata2 as CC BY 4.0; that listing is not a substitute for the pin (`NOTICE.md`).

The publisher PDF of the related ACS Applied Energy Materials paper is also not included; please use [DOI 10.1021/acsaem.6c03156](https://doi.org/10.1021/acsaem.6c03156).

## Key design choices

- DFT and experiment are never trained as one target.
- Own-paper DOIs are forced out of train/validation, including two JALCOM papers that also appear in Starrydata and are the author's own work.
- Paper-grouped literature scores can look strong while the own-paper hold-out fails. For bulk Bi₂Te₃ Seebeck, the paper-grouped test R² was 0.935 and the own-paper hold-out R² was −1.21 (see `metrics/tebench_baseline_metrics.csv`).
- The Starrydata thermal-conductivity baseline fails because unflagged extremes remain (values up to about 8200 W m⁻¹ K⁻¹). Treat that κ result as a quality-control warning, not a successful benchmark.

## Install

From the repository root:

```bash
python3 -m pip install -r requirements.txt
```

## Layout and how to run

Checked-in results live under `data/`, `splits/`, `metrics/`, `plots/`, and `notes/`. The scripts still expect the original local working directory. They read and write next to themselves (or in the current working directory), not from those published folders. A clean clone does not contain the Starrydata point tables or the local `jarvis_te.csv` input, so the numbered rebuild below cannot finish until those files are supplied locally.

1. Download the official Starrydata ThermoelectricMaterials `papers`, `samples`, and `curves` archives. `scripts/build_starrydata.py` reads `scripts/raw/manifest.json` and the three archives named in that manifest, then writes tables into `scripts/`. Do not commit those point or curve dumps.
2. `python3 scripts/build_starrydata.py`
3. `python3 scripts/build_tebench_collection.py` reads, from `scripts/`, `starrydata_te_points_experiment.csv.gz`, `sample_metadata.csv.gz`, `starrydata_te_points_candidates.csv.gz`, `starrydata_te_experiment_exact_T_wide.csv.gz`, and `Bi2Te3_BULK_dataset_v2.xlsx` (the published workbook is `data/Bi2Te3_BULK_dataset_v2.xlsx`). It also opens `jarvis_te.csv` and `01_jarvis_thermoelectric_dataset.ipynb` in the parent of `scripts/` (the repository root in this layout). It writes `tebench_*.csv.gz` beside the script. The published JARVIS file `data/tebench_jarvis_dft.csv.gz` is the harmonized extract, not that `jarvis_te.csv` input.
4. `python3 scripts/validate_tebench_collection.py` (imports `build_tebench_collection` from the script directory and re-checks the input paths recorded in the collection summary).
5. `python3 build_tebench_splits.py` reads and writes `tebench_*.csv.gz` in the **current working directory**. Run it from the directory that holds the collection outputs.
6. `python3 scripts/run_tebench_baselines.py` reads the collection and split files from `scripts/`, reads `jarvis_te.csv` from the repository root, and writes metrics beside the script plus plots under `scripts/baseline_plots/`. The copies in `metrics/` and `plots/` are the recorded outputs of that run.

## Citation

If you use TEBench, please cite this repository and:

- S. C. B. Rapaka, *ACS Appl. Energy Mater.* (2026), DOI: [10.1021/acsaem.6c03156](https://doi.org/10.1021/acsaem.6c03156)
- Y. Katsura et al., *Sci. Technol. Adv. Mater. Methods* (2025), DOI: [10.1080/27660400.2025.2506976](https://doi.org/10.1080/27660400.2025.2506976)
- K. Choudhary, K. F. Garrity and F. Tavazza, *J. Phys.: Condens. Matter* 32, 475501 (2020), DOI: [10.1088/1361-648X/aba06b](https://doi.org/10.1088/1361-648X/aba06b)

See `NOTICE.md` for data-licence details.
