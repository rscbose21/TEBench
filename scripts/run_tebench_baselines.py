"""
TEBench paper 1 -- simple CPU-only Random Forest baselines.

Beginner notes
--------------
* Each data SOURCE (Bi2Te3 audited sheet, JARVIS DFT, Starrydata experiment) and each
  TARGET property gets its OWN model. DFT and experiment are never mixed.
* Features = Magpie composition descriptors (matminer ElementProperty 'magpie' preset,
  132 numbers per composition) + temperature_K for the experimental sources.
  JARVIS has no temperature column, so it uses composition only.
  No other transport property is ever used as a feature.
* Models are fit on the 'train' role only. 'val' is only reported (no tuning).
  'test' and the extra hold-outs (own_paper_holdout, leave-family-out) are evaluated
  with the same fixed model.
* Every metric is computed from saved predictions. A "mean baseline" (predict the
  training-set mean) is reported next to each RF score for context.
* These are baseline scores under PROPOSED splits, not an official benchmark release.
Run:  python3 run_tebench_baselines.py
"""
import json, re, time, warnings
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from pymatgen.core import Composition
from matminer.featurizers.composition import ElementProperty
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
SEED = 20261107          # same seed as the split keys
MIN_ROWS = 10            # skip any evaluation set smaller than this
RF_SMALL = dict(n_estimators=200, min_samples_leaf=1, n_jobs=8, random_state=SEED)
# Starrydata point-level training set is large (~10^5-10^6 rows): use fewer trees and
# bootstrap 20% of training rows per tree so it fits in CPU time/memory. Documented below.
RF_LARGE = dict(n_estimators=100, min_samples_leaf=2, max_samples=0.2, n_jobs=8, random_state=SEED)

FEAT = ElementProperty.from_preset("magpie")
FEAT_NAMES = FEAT.feature_labels()
_cache = {}
def magpie(comp_str):
    """Magpie vector for one composition string; NaN vector if it cannot be parsed."""
    if comp_str in _cache: return _cache[comp_str]
    # Step 1: parse the whole string. Step 2 (fallback, documented): if that fails, parse only the
    # leading formula token, e.g. "Bi0.5Sb1.5Te3 + 2 mass% Te" -> "Bi0.5Sb1.5Te3",
    # "Bi2Te3 (Undoped Baseline)" -> "Bi2Te3". Additives/notes after the token are IGNORED by features.
    try:
        try:
            c = Composition(str(comp_str).replace(" ", ""))
        except Exception:
            m = re.match(r"\s*([A-Z][A-Za-z0-9.]*)", str(comp_str))
            c = Composition(m.group(1))
        v = np.array(FEAT.featurize(c), dtype=float) if c.num_atoms > 0 else None
    except Exception:
        v = None
    if v is None: v = np.full(len(FEAT_NAMES), np.nan)
    _cache[comp_str] = v
    return v

def feature_matrix(comps, temps=None):
    X = np.vstack([magpie(c) for c in comps])
    if temps is not None: X = np.column_stack([X, np.asarray(temps, float)])
    return X

def metrics(y, p):
    return dict(n=int(len(y)), MAE=float(mean_absolute_error(y, p)),
                RMSE=float(np.sqrt(mean_squared_error(y, p))), R2=float(r2_score(y, p)))

ROWS, PRED_FRAMES, NOTES = [], [], {}

def fit_eval(source, target, df, roles_eval, rf_params, scheme, has_T, train_mask=None):
    """df has columns: tebench_id, composition, [temperature_K], y, role."""
    df = df.dropna(subset=["y"]).copy()
    X = feature_matrix(df.composition, df.temperature_K if has_T else None)
    ok = ~np.isnan(X).any(axis=1)
    n_bad = int((~ok).sum())
    df, X = df[ok], X[ok]
    tr = (df.role == "train").values if train_mask is None else train_mask(df)
    if tr.sum() < MIN_ROWS:
        NOTES[f"{source}|{target}|{scheme}"] = f"skipped: only {tr.sum()} train rows"; return
    t0 = time.time()
    rf = RandomForestRegressor(**rf_params).fit(X[tr], df.y.values[tr])
    fit_s = time.time() - t0
    ymean = float(df.y.values[tr].mean())
    for role in roles_eval:
        m = (df.role == role).values & ~tr
        if m.sum() < MIN_ROWS:
            NOTES[f"{source}|{target}|{scheme}|{role}"] = f"skipped: n={int(m.sum())} < {MIN_ROWS}"; continue
        y, p = df.y.values[m], rf.predict(X[m])
        rfm, bm = metrics(y, p), metrics(y, np.full(len(y), ymean))
        ROWS.append(dict(source=source, target=target, split_scheme=scheme, eval_role=role,
                         n_train=int(tr.sum()), n=rfm["n"], RF_MAE=rfm["MAE"], RF_RMSE=rfm["RMSE"], RF_R2=rfm["R2"],
                         mean_MAE=bm["MAE"], mean_RMSE=bm["RMSE"], mean_R2=bm["R2"], train_mean=ymean,
                         rows_dropped_unparsable_composition=n_bad, fit_seconds=round(fit_s, 1)))
        out = df[m][["tebench_id", "composition"] + (["temperature_K"] if has_T else [])].copy()
        out.insert(0, "source", source); out["target"] = target; out["split_scheme"] = scheme
        out["split_role"] = role; out["y_true"] = y; out["y_pred"] = p
        PRED_FRAMES.append(out)
    print(f"  {source} {target} [{scheme}] train={tr.sum()} fit={fit_s:.0f}s", flush=True)
    return rf

# ---------------------------------------------------------------- 1. Bi2Te3 audited
def run_bi2te3():
    d = pd.read_csv(HERE / "tebench_bi2te3_bulk_audited.csv.gz")
    s = pd.read_csv(HERE / "tebench_split_bi2te3_bulk_audited.csv.gz")[["tebench_id", "split__paper_random_70_15_15"]]
    d = d.merge(s, on="tebench_id", how="inner").rename(columns={"split__paper_random_70_15_15": "role"})
    d = d[d.role != "excluded_ml_include_0"]
    for t in ["seebeck_uV_K", "sigma_S_m", "kappa_total_W_m_K", "PF_W_m_K2", "zT"]:
        x = d[["tebench_id", "composition", "temperature_K", "role"]].assign(y=d[t])
        fit_eval("bi2te3_bulk_audited", t, x, ["val", "test", "own_paper_holdout"], RF_SMALL,
                 "paper_random_70_15_15", True)
    return int((d.role == "own_paper_holdout").sum())

# ---------------------------------------------------------------- 2. JARVIS DFT
def run_jarvis():
    j = pd.read_csv(HERE.parent / "jarvis_te.csv", usecols=["jid", "formula", "n-Seebeck", "p-Seebeck", "n-powerfact", "p-powerfact"])
    s = pd.read_csv(HERE / "tebench_split_jarvis_dft.csv.gz")
    s["jid"] = s.sample_record_id
    j = j.merge(s[["jid", "tebench_id", "split__formula_random_70_15_15", "split__leave_contains_Bi_and_Te_out",
                   "split__leave_BiSbTeSe_only_out"]], on="jid", how="inner")
    j = j.rename(columns={"formula": "composition"})
    inter = {}
    for t in ["n-Seebeck", "p-Seebeck", "n-powerfact", "p-powerfact"]:
        base = j[["tebench_id", "composition"]].assign(y=j[t])
        fit_eval("jarvis_dft", t, base.assign(role=j.split__formula_random_70_15_15),
                 ["val", "test"], RF_SMALL, "formula_random_70_15_15", False)
        for col, name in [("split__leave_contains_Bi_and_Te_out", "leave_contains_Bi_and_Te_out"),
                          ("split__leave_BiSbTeSe_only_out", "leave_BiSbTeSe_only_out")]:
            hold = j[col] == "test"
            # extra test: ALL hold-out formulas; train = formula-random 'train' rows NOT in hold-out
            role = np.where(hold, "leaveout_test", np.where(j.split__formula_random_70_15_15 == "train", "train", "unused"))
            inter[name] = dict(holdout_rows=int(hold.sum()),
                               holdout_rows_that_were_formula_random_train=int((hold & (j.split__formula_random_70_15_15 == "train")).sum()),
                               train_rows_used=int(((j.split__formula_random_70_15_15 == "train") & ~hold).sum()))
            fit_eval("jarvis_dft", t, base.assign(role=role), ["leaveout_test"], RF_SMALL, name, False)
    NOTES["jarvis_leaveout_intersections"] = inter

# ---------------------------------------------------------------- 3. Starrydata experiment
def run_starry():
    cols = ["SID", "sample_id", "composition", "sample_composition", "temperature_K", "property", "value",
            "missing_value", "missing_temperature", "composition_missing", "magnitude_review", "physical_sign_review", "temperature_review"]
    p = pd.read_csv(HERE / "starrydata_te_points_experiment.csv.gz", usecols=cols)
    n0 = len(p)
    p = p[~(p.missing_value | p.missing_temperature | p.composition_missing
            | p.magnitude_review | p.physical_sign_review | p.temperature_review)].dropna(subset=["value", "temperature_K"])
    s = pd.read_csv(HERE / "tebench_split_starrydata_experiment.csv.gz",
                    usecols=["tebench_id", "paper_id", "sample_record_id", "split__paper_random_70_15_15"])
    s = s.rename(columns={"paper_id": "SID", "sample_record_id": "sample_id", "split__paper_random_70_15_15": "role"})
    p = p.merge(s, on=["SID", "sample_id"], how="inner")
    # point composition = curve composition; fall back to sample composition when blank
    p["composition"] = p.composition.fillna(p.sample_composition)
    NOTES["starrydata_points"] = dict(points_in_file=n0, points_after_flag_filter_and_split_join=int(len(p)),
        filter="dropped points flagged missing_value, missing_temperature, composition_missing, magnitude_review, physical_sign_review or temperature_review (flags from build_starrydata.py); no other outlier removal, so unflagged extreme values (e.g. kappa up to 8200 W/mK) remain",
        temperature="point-level: every measured (T, value) point is its own row; temperature_K is a feature; no averaging, no interpolation")
    for prop, name in [("seebeck_uV_K", "seebeck_uV_K"), ("zT", "zT"), ("kappa_W_m_K", "kappa_W_m_K (Starrydata thermal conductivity)")]:
        x = p[p.property == prop][["tebench_id", "composition", "temperature_K", "role"]].assign(y=p.loc[p.property == prop, "value"])
        fit_eval("starrydata_experiment", name, x, ["val", "test", "own_paper_holdout"], RF_LARGE,
                 "paper_random_70_15_15 (point-level)", True)
    return p

def parity_plots(pred):
    for (src, tgt, sch), g in pred.groupby(["source", "target", "split_scheme"]):
        g = g[g.split_role.isin(["test", "leaveout_test"])]
        if len(g) == 0: continue
        if len(g) > 20000: g = g.sample(20000, random_state=SEED)
        fig, ax = plt.subplots(figsize=(4, 4))
        ax.scatter(g.y_true, g.y_pred, s=4, alpha=0.4)
        lo, hi = np.nanmin([g.y_true.min(), g.y_pred.min()]), np.nanmax([g.y_true.max(), g.y_pred.max()])
        ax.plot([lo, hi], [lo, hi], "k--", lw=1); ax.set_xlabel("true"); ax.set_ylabel("RF predicted")
        ax.set_title(f"{src}\n{tgt} | {sch} | test", fontsize=7)
        fn = f"parity_{src}_{tgt.split(' ')[0]}_{sch.split(' ')[0]}.png".replace("/", "_")
        fig.tight_layout(); fig.savefig(HERE / "baseline_plots" / fn, dpi=110); plt.close(fig)

if __name__ == "__main__":
    T0 = time.time(); (HERE / "baseline_plots").mkdir(exist_ok=True)
    own_n = run_bi2te3(); run_jarvis(); run_starry()
    pred = pd.concat(PRED_FRAMES, ignore_index=True)
    # Safety check: own-paper rows must never be in training (they only appear as eval rows here).
    assert not ((pred.split_role == "train").any())
    met = pd.DataFrame(ROWS); met.to_csv(HERE / "tebench_baseline_metrics.csv", index=False)
    for src, g in pred.groupby("source"):
        g.to_csv(HERE / f"tebench_baseline_predictions_{src}.csv.gz", index=False, compression="gzip")
    parity_plots(pred)
    summary = dict(
        status="CPU baseline scores under PROPOSED TEBench splits; not an official benchmark; not a reproduction of DOI 10.1021/acsaem.6c03156",
        seed=SEED, sklearn_model="RandomForestRegressor", rf_params_small=RF_SMALL, rf_params_starrydata=RF_LARGE,
        features="matminer Magpie ElementProperty (132) on pymatgen Composition + temperature_K (experimental sources only)",
        tuning="none; val reported only", min_rows_per_eval=MIN_ROWS, notes=NOTES,
        own_paper_rule="own_paper_holdout role never used for fitting (train mask = role=='train')",
        runtime_seconds=round(time.time() - T0, 1), metrics=ROWS)
    (HERE / "tebench_baseline_summary.json").write_text(json.dumps(summary, indent=2, default=str))
    print(met.to_string()); print("total s", round(time.time() - T0))
