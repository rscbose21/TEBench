# JARVIS extract provenance and transport conventions

Prepared 7 November 2026 (IST). Evidence inspected: preserved `original__*`
columns, `units_json`, `conditions_note`, `provenance_pointer` and
`doping_cm3_notebook` in `tebench_jarvis_dft.csv.gz`;
`build_tebench_collection.py` lines 209–244; and
`tebench_collection_summary.json`. No fresh JARVIS data were downloaded.

## Exact local identity
The saved collection manifest identifies `/workspace/thermogpt/jarvis_te.csv`,
28,218,973 bytes, SHA-256
`24ac8e6cb16b57bce54bfae1fb42e6ecc71d9f21408229a6bec70b5647e140a4`.
Its 23,558 JIDs and all 20 original columns are preserved in the harmonized table.
The manifest also identifies extraction notebook
`/workspace/thermogpt/01_jarvis_thermoelectric_dataset.ipynb`, SHA-256
`5e5ef5abdd51da4ea4f3e326d596e13ef39fb14d1b1d69e92b049f2f76c01043`.
These are provenance pointers from the existing manifest, not newly inspected
files outside the allowed task directory. An upstream JARVIS release tag,
retrieval date, source data-object checksum and per-row tensor-reduction method
are absent from the inspected extract. Therefore this is a hash-identified local
extract, not an asserted reproduction of a named upstream database release.

## Column map and numerical policy
- `n-Seebeck`, `p-Seebeck`: n/p carrier-labelled scalar S; notebook-stated µV/K.
  Opposite signs in a carrier-labelled column are retained, not relabelled.
- `n-powerfact`, `p-powerfact`: scalar PF in raw extract units; metadata states
  µW/(m K²). Baselines deliberately use these raw columns.
- `ncond`, `pcond`: conductivity in the original unscaled convention; whether
  this is sigma or sigma/tau cannot be established from the column names alone.
- `nkappa`, `pkappa`: electronic thermal-conductivity transport coefficients,
  notebook-described κ_e/tau in W/(m K s); not lattice or total κ.
- The existing collection builder multiplies raw PF by 1e-6 into extension
  columns named `n_PF_W_m_K2`, `p_PF_W_m_K2`. The relation is checked numerically
  in `jarvis_conversion_checks.json`. This revision does not change any PF
  numerical values. That legacy conversion is conditional on the notebook unit
  convention; the raw values remain the baseline targets and physical unit
  comparisons are not made.

## Conditions and comparison with published methods
The local annotations supply T=600 K and carrier concentration 10^20 cm^-3;
these are constant notebook-supplied annotations, not original per-row transport
settings. No per-row relaxation time, doping sweep, tensor components, averaging
operation or temperature grid is present. The transport paper by Choudhary,
Garrity and Tavazza, J. Phys.: Condens. Matter 32 (2020) 475501,
DOI 10.1088/1361-648X/aba06b, uses BoltzTraP, the constant-relaxation-time and
rigid-band approximations, 600 K and 10^20 cm^-3 for screening, and tau=10^-14 s
for conductivity (tau cancels from S). This supports the annotated screening
conditions but does not verify the local extract's tau or tensor reduction.
The paper reports PF in µW/(m K²), consistent with the notebook annotation;
without a versioned upstream mapping this is not independent per-row unit proof.

Public evidence opened this turn:
- https://arxiv.org/pdf/1906.06024 (author manuscript of the cited transport paper;
  text retained locally for audit).
- https://jarvis-tools.readthedocs.io/en/master/databases.html (lists distinct
  `dft_3d` / `dft_3d_2021` objects and use of `jarvis.db.figshare.data`; does not
  identify this local extract's version or document its PF scaling).

## Structure metadata
`jid`, formula, spacegroup, spacegroup_number and `atoms_json` (lattice matrix,
coordinates, elements, abc, angles) are available. Volume is |det(lattice)| in Å³;
natoms is the number of listed sites; density is the sum of site atomic masses
in u times 1.66053906660 divided by volume in Å³ (g/cm³). Numeric space-group
number is added as a coarse tabular feature; its numeric order is not a physical
metric. No transport targets, band gap, or other property is added as a feature.
Experimental tables have no atomic-coordinate or space-group/crystal-system
columns; workbook lattice a/c values alone are not sufficient for unique
structure matching. Candidate formula→JID pairs are not certified structures.

Unresolved: upstream release identity and exact local sigma/kappa tau convention
and tensor reduction require the original extraction provenance. No guessed
conversion, fabricated version or invented DOI is used.
