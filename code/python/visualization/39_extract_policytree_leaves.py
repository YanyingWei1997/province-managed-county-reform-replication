"""
Extract county_codes that fall in the highest-CATE leaf of the depth-3 PolicyTree.
Output: data/processed/policytree_top_leaf_counties.csv
"""
import pathlib
import pandas as pd
from sklearn.tree import DecisionTreeRegressor

ROOT = pathlib.Path(__file__).resolve().parents[3]

cate = pd.read_csv(ROOT / "data" / "processed" / "d2_cate_results.csv")
grf = pd.read_csv(ROOT / "data" / "processed" / "grf_input.csv")
df = cate.merge(grf, on=["county_code", "D2"], how="inner")
print(f"Merged sample: {len(df)}")

features = ["fiscal_autonomy_pre", "primary_ratio_pre", "secondary_ratio_pre",
            "ln_pop_pre", "gov_scale_pre", "region_val"]  # match T12 original
X = df[features].fillna(df[features].median())
y = df["cate"].values

tree = DecisionTreeRegressor(max_depth=3, random_state=42)
tree.fit(X, y)

# Predict CATE per county (= leaf mean)
df["leaf_pred"] = tree.predict(X)
df["leaf_id"] = tree.apply(X)

leaf_summary = (df.groupby("leaf_id")
                  .agg(n=("county_code", "count"),
                       cate_mean=("cate", "mean"),
                       fa_pre_max=("fiscal_autonomy_pre", "max"),
                       sec_max=("secondary_ratio_pre", "max"))
                  .sort_values("cate_mean", ascending=False))
print("Leaf summary (sorted by CATE):")
print(leaf_summary)

# Find the highest-CATE leaf
best_leaf = leaf_summary.index[0]
best_counties = df[df["leaf_id"] == best_leaf][["county_code", "cate", "fiscal_autonomy_pre", "secondary_ratio_pre"]]
print(f"\nHighest-CATE leaf id={best_leaf}, n={len(best_counties)}, mean CATE={leaf_summary.loc[best_leaf,'cate_mean']:.4f}")
print(f"Threshold check: max secondary_ratio_pre = {best_counties['secondary_ratio_pre'].max():.4f}")
print(f"Threshold check: max fiscal_autonomy_pre = {best_counties['fiscal_autonomy_pre'].max():.4f}")

best_counties.to_csv(ROOT / "data" / "processed" / "policytree_top_leaf_counties.csv", index=False)
print(f"\nSaved to data/processed/policytree_top_leaf_counties.csv")

# Also extract counties matching the paper's stated threshold:
# secondary_ratio_pre <= 18.86 AND fiscal_autonomy_pre <= 0.049
mask = (df["secondary_ratio_pre"] <= 18.86) & (df["fiscal_autonomy_pre"] <= 0.049)
paper_counties = df.loc[mask, ["county_code", "cate", "fiscal_autonomy_pre", "secondary_ratio_pre"]]
print(f"\nPaper threshold (sec<=18.86 AND fa<=0.049): n = {len(paper_counties)}, mean CATE = {paper_counties['cate'].mean():.4f}")
paper_counties.to_csv(ROOT / "data" / "processed" / "policytree_paper_threshold_counties.csv", index=False)
print(f"Saved to data/processed/policytree_paper_threshold_counties.csv")
