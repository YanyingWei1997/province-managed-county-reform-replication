"""
T09: GRF CausalForest D2 主估计
注：T06A 裁决为 Exploratory Only，本脚本输出为探索性异质性证据，不使用强因果语言。
D1 作为条件协变量加入 X，控制 D1+D2 重叠县的污染。
"""
import pandas as pd
import numpy as np
import sys

try:
    from econml.grf import CausalForest
except ImportError:
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "econml", "--upgrade"], check=True)
    from econml.grf import CausalForest

np.random.seed(42)

# ── 1. 读取数据 ──────────────────────────────────────────────
df = pd.read_csv("data/processed/grf_input.csv")

required_cols = [
    "gdp_growth_outcome", "fiscal_autonomy_pre", "primary_ratio_pre",
    "secondary_ratio_pre", "ln_pop_pre", "gov_scale_pre", "region_val",
    "D1", "D2", "county_code"
]
df_valid = df.dropna(subset=required_cols)
print(f"n_total={len(df)}, n_valid={len(df_valid)}")

# Y 除以 100 转为小数单位（原始数据 mean~19% 即 19，转为 0.19）
# 使 ATE 与 TWFE ATT~4.8% 的口径一致（ate*100 即百分点）
Y = df_valid["gdp_growth_outcome"].values / 100.0
T = df_valid["D2"].values.astype(float)
X = df_valid[[
    "fiscal_autonomy_pre", "primary_ratio_pre", "secondary_ratio_pre",
    "ln_pop_pre", "gov_scale_pre", "region_val", "D1"
]].values

n_D2 = int(T.sum())
print(f"n_D2={n_D2}, n_D2_frac={n_D2/len(df_valid)*100:.1f}%")

# ── 2. 拟合 CausalForest ────────────────────────────────────
try:
    cf = CausalForest(n_estimators=2000, min_samples_leaf=5, random_state=42, n_jobs=-1)
    cf.fit(X, T, Y)
except MemoryError:
    print("MemoryError: 降级至 n_estimators=500")
    cf = CausalForest(n_estimators=500, min_samples_leaf=5, random_state=42, n_jobs=-1)
    cf.fit(X, T, Y)

# ── 3. 预测 CATE ─────────────────────────────────────────────
# econml.grf.CausalForest 使用 predict(interval=True) 而非 effect()
cate_out, cate_lower_out, cate_upper_out = cf.predict(X, interval=True, alpha=0.05)
# shape 可能是 (n, 1)，展平为 1D
cate = cate_out.squeeze()
cate_lower = cate_lower_out.squeeze()
cate_upper = cate_upper_out.squeeze()

ate = float(np.mean(cate))
ate_se = float(np.std(cate) / np.sqrt(len(cate)))

# ── 4. 仅 D2 县（D1=0, D2=1）子集 ATE ──────────────────────
mask_d2only = (df_valid["D1"].values == 0) & (df_valid["D2"].values == 1)
cate_d2only = cate[mask_d2only]
ate_d2only = float(np.mean(cate_d2only)) if mask_d2only.sum() > 0 else np.nan
n_d2only = int(mask_d2only.sum())
print(f"n_D2only(D1=0,D2=1)={n_d2only}, ATE_D2only={ate_d2only*100:.3f}%")

# ── 5. 保存结果 ──────────────────────────────────────────────
result = df_valid[["county_code", "D2"]].copy().reset_index(drop=True)
result["cate"] = cate
result["cate_lower"] = cate_lower
result["cate_upper"] = cate_upper
result.to_csv("data/processed/d2_cate_results.csv", index=False)
print(f"Saved d2_cate_results.csv: {len(result)} rows")

# ── 6. 最终输出行（验收标准要求） ────────────────────────────
print(
    f"T09 DONE: ATE={ate*100:.3f}%, SE_approx={ate_se*100:.3f}%, "
    f"n={len(df_valid)}, n_D2={n_D2}"
)
print(
    f"T09 SUPPLEMENT: ATE_D2only(D1=0,D2=1)={ate_d2only*100:.3f}%, "
    f"n_D2only={n_d2only}"
)
