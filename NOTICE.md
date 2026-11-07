# Data licences and attribution

TEBench code in `scripts/` is released under the MIT License (see `LICENSE`).

The bundled data files have mixed upstream licences. Redistribute each source
only under its own terms, and cite the papers below.

## Audited bulk Bi2Te3 workbook
- File: `data/Bi2Te3_BULK_dataset_v2.xlsx` and `data/tebench_bi2te3_bulk_audited.csv.gz`
- Compiled by Subash Chandra Bose Rapaka.
- Cite: S. C. B. Rapaka, ACS Applied Energy Materials (2026), DOI: 10.1021/acsaem.6c03156

## JARVIS DFT extract
- File: `data/tebench_jarvis_dft.csv.gz`
- Cite: K. Choudhary, K. F. Garrity and F. Tavazza, J. Phys.: Condens. Matter 32, 475501 (2020), DOI: 10.1088/1361-648X/aba06b
- Also cite the JARVIS-DFT database paper: K. Choudhary et al., npj Computational Materials 6, 173 (2020) if that is the database source used in your work. Confirm the exact JARVIS extract version before publication.

## Starrydata experimental curves
This repository does **not** redistribute Starrydata point dumps.
Rebuild them from the official ThermoelectricMaterials snapshot using `scripts/build_starrydata.py` and `scripts/build_tebench_collection.py`.
- Official project: https://github.com/starrydata/starrydata_datasets
- Cite: Y. Katsura et al., STAM: Methods 5, 2506976 (2025), DOI: 10.1080/27660400.2025.2506976
- NIMS MatDaCs currently lists Starrydata2 as CC BY 4.0; pin the archived snapshot DOI and re-check the licence before any public redistribution of derived Starrydata files.
- Also cite the original source papers (DOIs are preserved in the rebuilt tables).

## Split keys
`splits/tebench_split_starrydata_experiment.csv.gz` contains record identifiers and split roles for the Starrydata experiment collection. It is not the property table itself.
