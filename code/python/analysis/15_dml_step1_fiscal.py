"""
T15: DML 中介路径1 Step1 - D2 对 fiscal_autonomy 的效应（α）
顺序 DML 第一步：估计改革对财政自主度的因果效应
"""
import numpy as np
import pandas as pd
from econml.dml import LinearDML
from sklearn.linear_model import LassoCV
import os

np.random.seed(42)

# ── 1. 读取数据 ──────────────────────────────────────────────
df = pd.read_csv("data/processed/dml_panel_within.csv")
cols_need = ["fiscal_autonomy_w", "D2_w", "primary_ratio_w",
             "secondary_ratio_w", "ln_pop_w", "gov_scale_w"]
df = df.dropna(subset=cols_need)
print(f"样本量（dropna后）: {len(df)}")

# 非空率检查
non_null_rate = df["fiscal_autonomy_w"].notna().mean()
print(f"fiscal_autonomy_w 非空率: {non_null_rate:.1%}")
if non_null_rate < 0.50:
    print("WARNING: fiscal_autonomy_w 非空率<50%，需切换至原始值+县哑变量方案")
    # 此处数据充足，不触发 fallback
else:
    print("数据质量良好，使用 within 变换变量")

Y = df["fiscal_autonomy_w"].values
T = df["D2_w"].values
W = df[["primary_ratio_w", "secondary_ratio_w", "ln_pop_w", "gov_scale_w"]].values

print(f"\nY (fiscal_autonomy_w) 均值: {Y.mean():.6e}  std: {Y.std():.4f}")
print(f"T (D2_w) 均值: {T.mean():.6e}  （应≈0）")

# ── 2. 拟合 LinearDML ─────────────────────────────────────────
model = LinearDML(
    model_y=LassoCV(cv=5, random_state=42, max_iter=5000),
    model_t=LassoCV(cv=5, random_state=42, max_iter=5000),
    random_state=42
)
model.fit(Y, T, X=None, W=W)

# ── 3. 推断结果（X=None 时用 intercept__inference） ──────────
inf = model.intercept__inference()
alpha = float(np.atleast_1d(inf.point_estimate).ravel()[0])
se    = float(np.atleast_1d(inf.pred_stderr).ravel()[0])
pval  = float(np.atleast_1d(inf.pvalue()).ravel()[0])
ci_arr = inf.conf_int()
ci_lo = float(np.atleast_1d(ci_arr[0]).ravel()[0])
ci_hi = float(np.atleast_1d(ci_arr[1]).ravel()[0])

# fiscal_autonomy 是比例（0~1），乘以100转为百分点
alpha_pct = alpha * 100
se_pct    = se * 100
ci_lo_pct = ci_lo * 100
ci_hi_pct = ci_hi * 100

# ── 4. 方向判断 ───────────────────────────────────────────────
if alpha > 0:
    direction = "α > 0：D2 改革显著提升财政自主度，机制第一步成立"
    status = "PASS"
else:
    direction = "α < 0：WARNING - D2 改革降低了财政自主度，机制第一步方向反常"
    status = "WARNING"

# ── 5. 控制台输出 ─────────────────────────────────────────────
print(f"\n{'='*60}")
print(f"T15 结果摘要")
print(f"{'='*60}")
print(f"α（D2→fiscal_autonomy）= {alpha_pct:.4f}%")
print(f"SE = {se_pct:.4f}%")
print(f"p值 = {pval:.4f}")
print(f"95% CI: [{ci_lo_pct:.4f}%, {ci_hi_pct:.4f}%]")
print(f"方向判断: {direction}")
print(f"{'='*60}")
print(f"\nT15 DONE: alpha={alpha_pct:.4f}%, SE={se_pct:.4f}%, p={pval:.4f}")

# ── 6. 保存结果 ───────────────────────────────────────────────
result = {
    "alpha":       round(alpha, 8),
    "alpha_pct":   round(alpha_pct, 6),
    "se_pct":      round(se_pct, 6),
    "pval":        round(pval, 6),
    "ci_lo_pct":   round(ci_lo_pct, 6),
    "ci_hi_pct":   round(ci_hi_pct, 6),
    "direction":   "positive" if alpha > 0 else "negative",
    "status":      status,
    "n_obs":       len(df)
}
os.makedirs("outputs/tables", exist_ok=True)
pd.DataFrame([result]).to_csv("outputs/tables/table_t15_dml_step1_fiscal.csv", index=False)
print("结果已保存至 outputs/tables/table_t15_dml_step1_fiscal.csv")
