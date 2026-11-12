# Audited Bi2Te3 subset and Starrydata family notes

The supplied workbook has 740 audited records. It is one labelled subset, not
TEBench as a whole, and is associated with the already-published sole-author
ACS Applied Energy Materials paper (DOI 10.1021/acsaem.6c03156; accepted
22 October 2026). This collection does not rebuild that paper's tabular ML work.
All original Data-sheet fields, QC tiers, inclusion and own-data flags remain.
Its other workbook sheets remain untouched in the source workbook.

Starrydata family selection is the curator label `MaterialFamily == Bi2Te3`,
not a chemical parser: 1725 selected Experiment-labelled samples,
73314 points, 408 normalized DOIs.
There are 30 shared normalized DOIs with the audited sheet,
covering 150 audited records and
169 family-labelled Starrydata samples.
The workbook's own and literature DOI sets overlap in
1 DOI(s); preserving own-row hold-out
alone is therefore not proof of paper-disjoint evaluation. However, none of
the own-data DOI keys occurs in the supplied `ml_include=1` literature rows;
the shared literature rows are already excluded.

Two own-data DOI keys also occur in the selected Starrydata experiments:
10.1016/j.jallcom.2020.157828, 10.1016/j.jallcom.2021.158621.
Preserve this cross-source leakage-review warning before constructing any splits.

No sample identity, structure identity, independent replication, or equivalence
of Bi2Te3 vs Bi2Te3.00 is inferred. Shared papers can carry distinct specimens,
temperatures or directions; those require source-paper review before deduplication.
Starrydata has metadata labels rather than the supplied workbook's physics audit.
Its values never replace or average with audited values. JARVIS stays DFT-only.

Starrydata: official free-use statement / NIMS CC BY 4.0 listing and snapshot
details are in README. Raw Starrydata curve and point files are not redistributed.
Cite Katsura et al., STAM Methods (2025), DOI 10.1080/27660400.2025.2506976,
and the original source-paper DOIs as appropriate.

Shared DOI keys (case/prefix normalized; not a duplicate-record verdict):
- 10.1002/adfm.201400474
- 10.1002/adfm.201402663
- 10.1002/aenm.201100338
- 10.1002/aenm.201401391
- 10.1002/aenm.201500411
- 10.1007/s11664-012-2003-z
- 10.1007/s11664-013-2565-4
- 10.1007/s11664-014-3038-0
- 10.1007/s11664-015-4297-0
- 10.1007/s11664-016-4828-3
- 10.1007/s13391-014-4139-x
- 10.1016/j.carbon.2012.10.008
- 10.1016/j.pnsc.2017.02.009
- 10.1021/acsami.0c02408
- 10.1021/acsami.3c11235
- 10.1038/am.2013.86
- 10.1039/c0ee00012d
- 10.1039/c0jm01424a
- 10.1039/c1jm10163c
- 10.1039/c1jm13880d
- 10.1039/c2jm32916f
- 10.1039/c2jm34608g
- 10.1039/c3ta12764h
- 10.1039/c5tc02263k
- 10.1063/1.4737898
- 10.1063/1.4861727
- 10.1088/0957-4484/24/28/285702
- 10.1126/science.1156446
- 10.1155/2013/210767
- 10.3390/en81112323
