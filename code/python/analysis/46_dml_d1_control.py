"""
T46: Double ML PLR with D1 added to control vector W.

Reviewer concern: original DML controls only on (primary_ratio, secondary_ratio,
ln_pop, gov_scale). D1 (county-direct revenue management) is potentially correlated
with D2 (county-direct full reform) and with growth. Adding D1 to W tightens the
identification: theta now equals the effect of D2 partialling out D1, matching the
joint-TWFE specification used as the headline in Table 1.

Outputs:
  outputs/tables/table_t46_dml_d1control.csv
"""
import os
import numpy as np
import pandas as pd
from econml.dml import LinearDML
from sklearn.linear_model import LassoCV

os.chdir(Path(__file__).resolve().parents[3] if "Path" in globals() else os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
np.random.seed(42)

# ---------- 1. Data ----------
df = pd.read_csv("data/processed/dml_panel_within.csv")
need = ["gdp_growth_pc_w", "D2_w", "D1_w",
        "primary_ratio_w", "secondary_ratio_w", "ln_pop_w", "gov_scale_w"]
df = df.dropna(subset=need)
print(f"N(obs after dropna) = {len(df)}")

Y = df["gdp_growth_pc_w"].values
T = df["D2_w"].values

# ---------- 2. Three nested specifications ----------
specs = {
    "baseline_no_D1": ["primary_ratio_w", "secondary_ratio_w",
                       "ln_pop_w", "gov_scale_w"],
    "with_D1":        ["D1_w", "primary_ratio_w", "secondary_ratio_w",
                       "ln_pop_w", "gov_scale_w"],
}

records = []
for tag, w_cols in specs.items():
    W = df[w_cols].values
    model = LinearDML(
        model_y=LassoCV(cv=5, random_state=42, max_iter=5000),
        model_t=LassoCV(cv=5, random_state=42, max_iter=5000),
        random_state=42,
    )
    model.fit(Y, T, X=None, W=W)
    inf = model.intercept__inference()
    theta = float(np.atleast_1d(inf.point_estimate).ravel()[0])
    se    = float(np.atleast_1d(inf.pred_stderr).ravel()[0])
    pval  = float(np.atleast_1d(inf.pvalue()).ravel()[0])
    ci    = inf.conf_int()
    ci_lo = float(np.atleast_1d(ci[0]).ravel()[0])
    ci_hi = float(np.atleast_1d(ci[1]).ravel()[0])

    print(f"\n[{tag}]")
    print(f"  W = {w_cols}")
    print(f"  theta = {theta:.4f} pp,  SE = {se:.4f},  p = {pval:.4f}")
    print(f"  95% CI = [{ci_lo:.4f}, {ci_hi:.4f}]")
    records.append({
        "spec": tag,
        "theta_pp": theta,
        "se": se,
        "pval": pval,
        "ci_lo": ci_lo,
        "ci_hi": ci_hi,
        "n": len(df),
        "controls": ", ".join(w_cols),
    })

out = pd.DataFrame(records)
os.makedirs("outputs/tables", exist_ok=True)
out.to_csv("outputs/tables/table_t46_dml_d1control.csv", index=False)
print("\nSaved -> outputs/tables/table_t46_dml_d1control.csv")
print(out.to_string(index=False))
