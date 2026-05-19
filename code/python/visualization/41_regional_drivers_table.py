"""
Re-run the regional standardized OLS that backs Figure 3, output as a table.
Table: pre-reform covariate × {East, Central, West}, with standardized coef and SE.
"""
import pathlib
import pandas as pd
import numpy as np
import statsmodels.api as sm
from sklearn.preprocessing import StandardScaler
import pyreadstat

ROOT = pathlib.Path(__file__).resolve().parents[3]

grf = pd.read_csv(ROOT / "data" / "processed" / "grf_input.csv")
d2 = pd.read_csv(ROOT / "data" / "processed" / "d2_cate_results.csv")

raw, _ = pyreadstat.read_dta(
    str(pathlib.Path("data/analysis/panel_analysis_public.dta")),
    usecols=["county_code", "year", "fiscal_rev_pc", "gdppc", "transfer_dependence"],
)
extra = (
    raw[raw["year"] <= 2005]
    .groupby("county_code")[["fiscal_rev_pc", "gdppc", "transfer_dependence"]]
    .mean()
    .reset_index()
    .rename(columns={
        "fiscal_rev_pc": "fiscal_rev_pc_pre",
        "gdppc": "gdppc_pre",
        "transfer_dependence": "transfer_dep_pre",
    })
)

need = ["county_code", "fiscal_autonomy_pre", "secondary_ratio_pre",
        "primary_ratio_pre", "ln_pop_pre", "region_val"]
df = (grf[need]
      .merge(d2[["county_code", "cate"]], on="county_code")
      .merge(extra, on="county_code", how="left")
      .dropna())
print(f"Sample: {len(df)} counties")

pred_vars = ["fiscal_autonomy_pre", "transfer_dep_pre", "fiscal_rev_pc_pre",
             "secondary_ratio_pre", "primary_ratio_pre", "gdppc_pre", "ln_pop_pre"]
pred_labels = ["Fiscal autonomy (pre)", "Transfer dependence (pre)",
               "Fiscal revenue p.c. (pre)", "Secondary ratio (pre)",
               "Primary ratio (pre)", "GDP p.c. (pre)", "Population (ln, pre)"]

regions = [(1, "East"), (2, "Central"), (3, "West")]

results = {}
for rcode, rname in regions:
    sub = df[df["region_val"] == rcode]
    Xs = StandardScaler().fit_transform(sub[pred_vars])
    ys = (sub["cate"].values - sub["cate"].mean()) / sub["cate"].std()
    fit = sm.OLS(ys, sm.add_constant(Xs)).fit()
    results[rname] = {
        "n": len(sub),
        "coef": fit.params[1:],
        "se": fit.bse[1:],
        "pval": fit.pvalues[1:],
    }

# Build the table
rows = []
for j, (lbl, var) in enumerate(zip(pred_labels, pred_vars)):
    row = {"Predictor": lbl}
    for rname in ["East", "Central", "West"]:
        coef = results[rname]["coef"][j]
        se = results[rname]["se"][j]
        p = results[rname]["pval"][j]
        stars = "***" if p < 0.01 else ("**" if p < 0.05 else ("*" if p < 0.10 else ""))
        row[f"{rname} coef (SE)"] = f"{coef:+.3f}{stars} ({se:.3f})"
    rows.append(row)

table = pd.DataFrame(rows)
print()
print(table.to_string(index=False))

# Save CSV
out_csv = ROOT / "outputs" / "tables" / "table_regional_drivers.csv"
table.to_csv(out_csv, index=False)
print(f"\nSaved CSV: {out_csv}")

# Save Markdown
out_md = ROOT / "outputs" / "tables" / "table_regional_drivers.md"
with open(out_md, "w") as f:
    f.write("| Predictor | East coef (SE) | Central coef (SE) | West coef (SE) |\n")
    f.write("| --- | --- | --- | --- |\n")
    for _, r in table.iterrows():
        f.write(f"| {r['Predictor']} | {r['East coef (SE)']} | {r['Central coef (SE)']} | {r['West coef (SE)']} |\n")
    f.write(f"| _N_ | {results['East']['n']} | {results['Central']['n']} | {results['West']['n']} |\n")
print(f"Saved markdown: {out_md}")
