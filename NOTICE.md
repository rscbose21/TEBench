# Data licences and attribution

TEBench code in `scripts/` is released under the MIT License (see `LICENSE`).
Copyright (c) 2026 Subash Chandra Bose Rapaka.

The bundled data files have mixed upstream licences. Redistribute each source
only under its own terms, and cite the papers below.

## Audited bulk Bi2Te3 workbook
- File: `data/Bi2Te3_BULK_dataset_v2.xlsx` and `data/tebench_bi2te3_bulk_audited.csv.gz`
- Compiled by Subash Chandra Bose Rapaka.
- Cite: S. C. B. Rapaka, ACS Applied Energy Materials (2026), DOI: 10.1021/acsaem.6c03156

## JARVIS DFT extract
- File: `data/tebench_jarvis_dft.csv.gz`
- Cite: K. Choudhary, K. F. Garrity and F. Tavazza, J. Phys.: Condens. Matter 32, 475501 (2020), DOI: 10.1088/1361-648X/aba06b
- Also cite the JARVIS-DFT database paper: K. Choudhary et al., npj Computational Materials 6, 173 (2020) if that is the database source used in your work. The local extract SHA-256 hash is recorded in `notes/revision_20261107/JARVIS_PROVENANCE.md`; the upstream release identifier is not pinned.

## Starrydata experimental curves
This repository does **not** redistribute raw Starrydata curve or point dumps.
That includes the official ThermoelectricMaterials papers, samples, and curves
files, `starrydata_te_*.csv.gz`, and `tebench_starrydata_experiment.csv.gz`.
Rebuild those tables locally from the official snapshot with
`scripts/build_starrydata.py` and `scripts/build_tebench_collection.py`.
- Official project: https://github.com/starrydata/starrydata_datasets
- Official download instructions: https://starrydata.nims.go.jp/hp/en/manual/download/
- Official download documentation: “Starrydata2 data are free to use for both commercial and non-commercial purposes.”
- NIMS MatDaCs lists Starrydata2 as **CC BY 4.0**: https://mat-dacs.dxmt.nims.go.jp/en/list/392 and https://creativecommons.org/licenses/by/4.0/
- Retrieval: 7 November 2026, from GitHub Releases `latest` (`https://github.com/starrydata/starrydata_datasets/releases/latest/download/ThermoelectricMaterials_{papers,samples,curves}.csv.gz`).
- Snapshot time: 6 November 2026, 22:30:01 IST, which is 7 November 2026, 02:00:01 JST.
- The nearest Figshare monthly archive is `20261101_starrydata2`: https://figshare.com/articles/dataset/20261101_starrydata2/34875318
- These retrieved GitHub Release bytes are not claimed to be byte-identical to that Figshare archive. No Figshare DOI is minted or asserted for this retrieval.
- Cite: Y. Katsura et al., STAM: Methods 5, 2506976 (2025), DOI: 10.1080/27660400.2025.2506976
- Also cite the original source papers (DOIs are preserved in the rebuilt tables).

## Split keys
`splits/tebench_split_starrydata_experiment.csv.gz` contains record identifiers and split roles for the Starrydata experiment collection. It is not the property table itself.
