"""
T21: 替代结果变量稳健性检验（ln_gdppc_outcome）
用 ln_gdppc_outcome 替换 gdp_growth_outcome，重跑 CausalForest（T09 完整流程）
"""
import pandas as pd
import numpy as np
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# 设置随机种子
np.random.seed(42)

# ── 读取数据 ──────────────────────────────────────────────────────────────────
data_path = "data/processed/grf_input.csv"
df = pd.read_csv(data_path)

print(f"总样本量：{len(df)}")
print(f"ln_gdppc_outcome 非空数：{df['ln_gdppc_outcome'].notna().sum()}")
print(f"ln_gdppc_outcome 非空率：{df['ln_gdppc_outcome'].notna().mean():.4f}")

# ── 筛选有效样本（与 T09 相同逻辑） ───────────────────────────────────────────
feature_cols = [
    'fiscal_autonomy_pre', 'primary_ratio_pre', 'secondary_ratio_pre',
    'ln_pop_pre', 'gov_scale_pre', 'region_val', 'D1'
]

df_valid = df.dropna(subset=['ln_gdppc_outcome', 'D2'] + feature_cols).copy()
print(f"\n有效样本量（ln_gdppc）：{len(df_valid)}")
print(f"其中 D2=1：{df_valid['D2'].sum()}")

# ── 非空率检查 ─────────────────────────────────────────────────────────────────
non_null_rate = df['ln_gdppc_outcome'].notna().mean()
if non_null_rate < 0.50:
    print(f"警告：ln_gdppc_outcome 非空率 {non_null_rate:.2%} < 50%，存在样本量限制")

# ── 构造 Y、T、X ──────────────────────────────────────────────────────────────
Y = df_valid['ln_gdppc_outcome'].values
T = df_valid['D2'].values.astype(float)
X = df_valid[feature_cols].values

print(f"\nY (ln_gdppc_outcome) stats: mean={Y.mean():.4f}, std={Y.std():.4f}")
print(f"T (D2): 处理={T.sum():.0f}, 控制={len(T)-T.sum():.0f}")

# ── 运行 CausalForest（与 T09 完全相同参数） ──────────────────────────────────
try:
    from econml.grf import CausalForest
    print("\n使用 econml.grf.CausalForest")
except ImportError:
    print("尝试备用 import 路径...")
    from econml.grf._causal_forest import CausalForest

cf = CausalForest(
    n_estimators=2000,
    min_samples_leaf=5,
    random_state=42,
    n_jobs=-1
)

cf.fit(X, T, Y)

# ── CATE 估计（与 T09 相同方式）─────────────────────────────────────────────
cate_out, cate_lower_out, cate_upper_out = cf.predict(X, interval=True, alpha=0.05)
cate_pred = cate_out.squeeze()
cate_lower = cate_lower_out.squeeze()
cate_upper = cate_upper_out.squeeze()

ate_val = float(np.mean(cate_pred))
ate_se = float(np.std(cate_pred) / np.sqrt(len(cate_pred)))

print(f"\n{'='*50}")
print(f"ATE(ln_gdppc) = {ate_val:.6f}")
print(f"SE(近似) = {ate_se:.6f}")
print(f"{'='*50}")

# ── 与原始结果（gdp_growth）对比 ─────────────────────────────────────────────
ate_original = -0.02728   # T09 已验证：ATE(gdp_growth) = -2.728%
print(f"\n原始 ATE(gdp_growth) = {ate_original:.4f}（T09 结果）")
print(f"替代 ATE(ln_gdppc)   = {ate_val:.6f}")
print(f"方向一致：{'是' if (ate_original < 0 and ate_val < 0) or (ate_original > 0 and ate_val > 0) else '否'}")

# ── Pearson r(CATE, fiscal_autonomy_pre) ─────────────────────────────────────
fiscal_autonomy_pre = df_valid['fiscal_autonomy_pre'].values
r_alt, p_alt = stats.pearsonr(cate_pred, fiscal_autonomy_pre)
r_original = -0.1230  # T13 已验证

print(f"\nPearson r（替代 CATE ~ fiscal_autonomy_pre）= {r_alt:.4f}，p = {p_alt:.6f}")
print(f"原始 r（gdp_growth CATE ~ fiscal_autonomy_pre） = {r_original:.4f}")
print(f"符号一致：{'是（均为负相关）' if r_alt < 0 and r_original < 0 else '否（符号不一致）'}")

# ── 保存结果 ──────────────────────────────────────────────────────────────────
result_df = pd.DataFrame({
    'county_code': df_valid['county_code'].values,
    'D2': T,
    'ln_gdppc_outcome': Y,
    'cate_lngdp': cate_pred,
    'cate_lower': cate_lower,
    'cate_upper': cate_upper,
    'fiscal_autonomy_pre': fiscal_autonomy_pre
})
result_df.to_csv('data/processed/t21_cate_lngdp.csv', index=False)
print(f"\n结果已保存至 data/processed/t21_cate_lngdp.csv")

# ── 最终摘要 ──────────────────────────────────────────────────────────────────
print(f"\n{'='*50}")
print(f"T21 稳健性检验摘要")
print(f"{'='*50}")
print(f"替代变量：ln_gdppc_outcome（非空率 {non_null_rate:.2%}）")
print(f"有效样本：{len(df_valid)} 县")
print(f"ATE(ln_gdppc)        = {ate_val:.6f}")
print(f"ATE(gdp_growth, T09) = {ate_original:.4f}")
ate_direction_consistent = (ate_original < 0 and ate_val < 0) or (ate_original > 0 and ate_val > 0)
print(f"ATE 方向一致：{'是' if ate_direction_consistent else '否'}")
print(f"Pearson r（替代）= {r_alt:.4f}，原始 r = {r_original:.4f}")
r_sign_consistent = (r_alt < 0 and r_original < 0) or (r_alt > 0 and r_original > 0)
print(f"Pearson r 符号一致：{'是（均为负相关）' if r_sign_consistent else '否（符号不一致）'}")
if ate_direction_consistent and r_sign_consistent:
    print("\n结论：替代结果变量检验支持原结论的稳健性")
else:
    print("\n结论：替代结果变量检验不支持原结论的稳健性")
