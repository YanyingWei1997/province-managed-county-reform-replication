"""
T47: Bootstrap CI for the highest-CATE PolicyTree leaf.

Reviewer concern: §4.4 reports +0.51 pp for the policytree top leaf without an SE.
A discovered subgroup needs a CI, ideally one that accounts for the selection of
the leaf itself.

Two CIs reported:
  (A) Rule-fixed bootstrap: fix the rule extracted on full sample
      (fiscal_autonomy_pre and secondary_ratio_pre cuts), bootstrap counties,
      compute mean CATE among counties matching the rule.
  (B) Rule-free bootstrap: refit DecisionTreeRegressor(max_depth=3, min_samples_leaf=20)
      on each bootstrap sample, take the highest-mean leaf. Wider — accounts for
      the post-hoc selection of "best" leaf.

Both use percentile method, B = 1000 reps (CATE values are pre-computed,
so bootstrap is cheap; no GRF refit).
"""
import os
import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeRegressor

os.chdir(Path(__file__).resolve().parents[3] if "Path" in globals() else os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
np.random.seed(42)

# ---------- 1. Data ----------
grf = pd.read_csv("data/processed/grf_input.csv")
cate = pd.read_csv("data/processed/d2_cate_results.csv")
df = grf.merge(cate[["county_code", "cate"]], on="county_code", how="inner")

feature_cols = [
    "fiscal_autonomy_pre",
    "primary_ratio_pre",
    "secondary_ratio_pre",
    "ln_pop_pre",
    "gov_scale_pre",
    "region_val",
]
df = df.dropna(subset=feature_cols + ["cate"]).reset_index(drop=True)
print(f"N counties = {len(df)}")
print(f"Overall ATE (mean CATE) = {df['cate'].mean()*100:.3f} pp")

X = df[feature_cols].values
y = df["cate"].values

# ---------- 2. Identify rule on full sample ----------
dt = DecisionTreeRegressor(max_depth=3, random_state=42, min_samples_leaf=20)
dt.fit(X, y)
leaf_id = dt.apply(X)

leaf_means = pd.Series(y).groupby(leaf_id).mean()
top_leaf = leaf_means.idxmax()
top_leaf_mask = leaf_id == top_leaf
n_top = int(top_leaf_mask.sum())
top_mean = float(y[top_leaf_mask].mean())
print(f"\nFull-sample top leaf:")
print(f"  leaf id = {top_leaf}")
print(f"  n = {n_top} counties")
print(f"  mean CATE = {top_mean*100:.4f} pp")

# Extract the rule: walk path from root to top_leaf
def path_to_leaf(tree, leaf_id):
    children_left = tree.children_left
    children_right = tree.children_right
    feature = tree.feature
    threshold = tree.threshold

    def find(node, target, path):
        if node == target:
            return True
        l, r = children_left[node], children_right[node]
        if l != -1:
            path.append((node, "<=", feature[node], threshold[node]))
            if find(l, target, path):
                return True
            path.pop()
        if r != -1:
            path.append((node, ">",  feature[node], threshold[node]))
            if find(r, target, path):
                return True
            path.pop()
        return False

    p = []
    find(0, leaf_id, p)
    return p

path = path_to_leaf(dt.tree_, top_leaf)
rule_str = " & ".join([f"{feature_cols[fi]} {op} {th:.4f}"
                       for _, op, fi, th in path])
print(f"  rule: {rule_str}")

# Apply the rule on the dataframe (for the rule-fixed bootstrap).
def apply_rule(df_in, path, feature_cols):
    mask = np.ones(len(df_in), dtype=bool)
    for _, op, fi, th in path:
        col = feature_cols[fi]
        if op == "<=":
            mask &= (df_in[col].values <= th)
        else:
            mask &= (df_in[col].values >  th)
    return mask

rule_mask = apply_rule(df, path, feature_cols)
assert rule_mask.sum() == n_top, "rule must match leaf membership"

# ---------- 3. Bootstrap A: rule-fixed ----------
B = 1000
n = len(df)
np.random.seed(42)

# We bootstrap counties with replacement, then average CATE among counties
# whose features satisfy the rule.
boot_A = np.empty(B)
for b in range(B):
    idx = np.random.choice(n, n, replace=True)
    sub = df.iloc[idx]
    sub_mask = apply_rule(sub, path, feature_cols)
    boot_A[b] = sub.loc[sub_mask, "cate"].mean() if sub_mask.sum() else np.nan

boot_A = boot_A[~np.isnan(boot_A)]
ci_A_lo, ci_A_hi = np.percentile(boot_A, [2.5, 97.5])
se_A = boot_A.std()
print(f"\n[A] Rule-fixed bootstrap (B={B})")
print(f"    mean CATE in leaf = {top_mean*100:.4f} pp")
print(f"    bootstrap mean    = {boot_A.mean()*100:.4f} pp")
print(f"    SE                = {se_A*100:.4f} pp")
print(f"    95% CI            = [{ci_A_lo*100:.4f}, {ci_A_hi*100:.4f}] pp")

# ---------- 4. Bootstrap B: rule-free (refit tree, take max-leaf mean) ----------
np.random.seed(42)
boot_B = np.empty(B)
for b in range(B):
    idx = np.random.choice(n, n, replace=True)
    Xb, yb = X[idx], y[idx]
    dt_b = DecisionTreeRegressor(max_depth=3, random_state=42, min_samples_leaf=20)
    dt_b.fit(Xb, yb)
    lid_b = dt_b.apply(Xb)
    leaf_means_b = pd.Series(yb).groupby(lid_b).mean()
    boot_B[b] = leaf_means_b.max()

ci_B_lo, ci_B_hi = np.percentile(boot_B, [2.5, 97.5])
se_B = boot_B.std()
print(f"\n[B] Rule-free bootstrap (B={B}) — accounts for post-hoc leaf selection")
print(f"    bootstrap mean = {boot_B.mean()*100:.4f} pp")
print(f"    SE             = {se_B*100:.4f} pp")
print(f"    95% CI         = [{ci_B_lo*100:.4f}, {ci_B_hi*100:.4f}] pp")

# ---------- 5. Save ----------
out = pd.DataFrame([
    dict(spec="A_rule_fixed",
         point_pp=top_mean*100,
         boot_mean_pp=boot_A.mean()*100,
         se_pp=se_A*100,
         ci_lo_pp=ci_A_lo*100,
         ci_hi_pp=ci_A_hi*100,
         n_in_leaf=n_top,
         B=len(boot_A),
         rule=rule_str),
    dict(spec="B_rule_free",
         point_pp=top_mean*100,
         boot_mean_pp=boot_B.mean()*100,
         se_pp=se_B*100,
         ci_lo_pp=ci_B_lo*100,
         ci_hi_pp=ci_B_hi*100,
         n_in_leaf=n_top,
         B=B,
         rule="argmax leaf mean across refit trees"),
])
os.makedirs("outputs/tables", exist_ok=True)
out.to_csv("outputs/tables/table_t47_policytree_leaf_ci.csv", index=False)
print("\nSaved -> outputs/tables/table_t47_policytree_leaf_ci.csv")
print(out.to_string(index=False))
