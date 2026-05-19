"""
T11: GRF CausalForest D1 CATE 估计（辅助对比）
注：T06A 裁决为 Exploratory Only，本脚本输出为探索性异质性证据，不使用强因果语言。
D2 作为条件协变量加入 X，控制 D1+D2 重叠县的 D2 效应对 D1 估计的污染。
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

# Y 除以 100 转为小数单位（与 T09 口径一致）
Y = df_valid["gdp_growth_outcome"].values / 100.0
T = df_valid["D1"].values.astype(float)   # 处理变量改为 D1
X = df_valid[[
    "fiscal_autonomy_pre", "primary_ratio_pre", "secondary_ratio_pre",
    "ln_pop_pre", "gov_scale_pre", "region_val", "D2"              # D2 作为条件协变量
]].values

n_D1 = int(T.sum())
print(f"n_D1={n_D1}, n_D1_frac={n_D1/len(df_valid)*100:.1f}%")

# ── 2. 拟合 CausalForest ────────────────────────────────────
try:
    cf = CausalForest(n_estimators=2000, min_samples_leaf=5, random_state=42, n_jobs=-1)
    cf.fit(X, T, Y)
except MemoryError:
    print("MemoryError: 降级至 n_estimators=500")
    cf = CausalForest(n_estimators=500, min_samples_leaf=5, random_state=42, n_jobs=-1)
    cf.fit(X, T, Y)

# ── 3. 预测 CATE ─────────────────────────────────────────────
cate_out, cate_lower_out, cate_upper_out = cf.predict(X, interval=True, alpha=0.05)
cate = cate_out.squeeze()
cate_lower = cate_lower_out.squeeze()
cate_upper = cate_upper_out.squeeze()

ate = float(np.mean(cate))
ate_se = float(np.std(cate) / np.sqrt(len(cate)))

# ── 4. D1 样本量不足诊断 ─────────────────────────────────────
if n_D1 < 100:
    print(f"WARNING: n_D1={n_D1} < 100，D1 处理组样本量不足，结果仅供参考")

if ate < 0:
    print(f"NOTE: ATE(D1)={ate*100:.3f}% < 0，检查 D1 处理组样本量 n_D1={n_D1}")
    if n_D1 < 100:
        print("D1 样本量不足，结果仅供参考")

# ── 5. 保存结果 ──────────────────────────────────────────────
result = df_valid[["county_code", "D1"]].copy().reset_index(drop=True)
result["cate"] = cate
result["cate_lower"] = cate_lower
result["cate_upper"] = cate_upper
result.to_csv("data/processed/d1_cate_results.csv", index=False)
print(f"Saved d1_cate_results.csv: {len(result)} rows")

# ── 6. 最终输出行（验收标准要求） ────────────────────────────
print(
    f"T11 DONE: ATE(D1)={ate*100:.3f}%, SE_approx={ate_se*100:.3f}%, "
    f"n={len(df_valid)}, n_D1={n_D1}"
)
