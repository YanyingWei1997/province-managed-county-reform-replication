"""
T14: Double ML 总处理效应基准（PLR）
使用 LinearDML 估计 D2 对 gdp_growth_pc 的总处理效应
与 T03B TWFE 基准结果对比
"""
import numpy as np
import pandas as pd
from econml.dml import LinearDML
from sklearn.linear_model import LassoCV
import os, json, re

np.random.seed(42)

# ── 1. 读取数据 ──────────────────────────────────────────────
df = pd.read_csv("data/processed/dml_panel_within.csv")
cols_need = ["gdp_growth_pc_w", "D2_w", "primary_ratio_w", "secondary_ratio_w",
             "ln_pop_w", "gov_scale_w"]
df = df.dropna(subset=cols_need)
print(f"样本量（dropna后）: {len(df)}")
print(f"D2_w 均值: {df['D2_w'].mean():.6e}  （应≈0）")

Y = df["gdp_growth_pc_w"].values
T = df["D2_w"].values
W = df[["primary_ratio_w", "secondary_ratio_w", "ln_pop_w", "gov_scale_w"]].values

# ── 2. 从 T03B 报告读取 TWFE 基准 ─────────────────────────────
twfe_ref = None
report_path = "docs/task_reports/T03B_baseline_did.md"
if os.path.exists(report_path):
    text = open(report_path).read()
    # 匹配如 1.023% 或 1.02% 等
    m = re.search(r"TWFE.*?D2.*?(\d+\.\d+)%", text)
    if m:
        twfe_ref = float(m.group(1))
    else:
        # 宽松匹配：ATT.*?(\d+\.\d+)%
        m2 = re.search(r"ATT[（(]?[^%\n]*?(\d+\.\d+)%", text)
        if m2:
            twfe_ref = float(m2.group(1))
if twfe_ref is None:
    twfe_ref = 1.023  # fallback：T03B 报告中明确值
    print("⚠ 未能从报告自动解析 TWFE 值，使用 fallback 1.023%")
else:
    print(f"从 T03B 报告读取 TWFE ATT = {twfe_ref:.4f}%")

# ── 3. 拟合 LinearDML ─────────────────────────────────────────
model = LinearDML(
    model_y=LassoCV(cv=5, random_state=42, max_iter=5000),
    model_t=LassoCV(cv=5, random_state=42, max_iter=5000),
    random_state=42
)
model.fit(Y, T, X=None, W=W)

# ── 4. 推断结果 ───────────────────────────────────────────────
# 当 X=None 时，LinearDML 的处理效应存于 cate_intercept（常数项）
# 通过 intercept__inference() 获取推断统计量
inf = model.intercept__inference()
theta = float(np.atleast_1d(inf.point_estimate).ravel()[0])
se    = float(np.atleast_1d(inf.pred_stderr).ravel()[0])
pval  = float(np.atleast_1d(inf.pvalue()).ravel()[0])
ci_arr = inf.conf_int()
ci_lo = float(np.atleast_1d(ci_arr[0]).ravel()[0])
ci_hi = float(np.atleast_1d(ci_arr[1]).ravel()[0])

# gdp_growth_pc 单位已是百分点（均值约14%），theta 直接以百分点解读
# D2_w 是二元变量的 within 变换，LinearDML theta 已代表处理效应（pp）
theta_pct = theta       # 已为百分点单位，无需乘100
se_pct    = se
ci_lo_pct = ci_lo
ci_hi_pct = ci_hi

# ── 5. 与 TWFE 对比 ──────────────────────────────────────────
diff_pp  = theta_pct - twfe_ref          # 百分点差
diff_pct = diff_pp / twfe_ref * 100      # 百分比差（相对差）

print(f"\nT14 DONE: DML_theta={theta_pct:.4f}pp, SE={se_pct:.4f}pp, p={pval:.4f}" if pval is not None
      else f"\nT14 DONE: DML_theta={theta_pct:.4f}pp, SE={se_pct:.4f}pp, p=N/A")
print(f"TWFE 基准（T03B）: {twfe_ref:.4f}%")
print(f"差距: {diff_pp:+.4f} pp ({diff_pct:+.2f}%)")

consistent = abs(diff_pp) <= 2.0 and theta_pct > 0
verdict = "一致" if consistent else "不一致"
print(f"判断：DML 基准结果与 TWFE {verdict}，差距为 {abs(diff_pp):.4f} 个百分点（{abs(diff_pct):.2f}%）")

# ── 6. 保存结果供报告使用 ────────────────────────────────────
result = {
    "theta_pct": round(theta_pct, 6),
    "se_pct":    round(se_pct, 6) if se_pct else None,
    "pval":      round(pval, 6) if pval is not None else None,
    "ci_lo_pct": round(ci_lo_pct, 6) if ci_lo_pct else None,
    "ci_hi_pct": round(ci_hi_pct, 6) if ci_hi_pct else None,
    "twfe_ref":  twfe_ref,
    "diff_pp":   round(diff_pp, 6),
    "diff_pct":  round(diff_pct, 4),
    "verdict":   verdict,
    "n_obs":     len(df)
}
os.makedirs("outputs/tables", exist_ok=True)
pd.DataFrame([result]).to_csv("outputs/tables/table_t14_dml_baseline.csv", index=False)
print("结果已保存至 outputs/tables/table_t14_dml_baseline.csv")
