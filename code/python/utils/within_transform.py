"""
T08: 双向 within 变换（county + year 固定效应去均值）
不平衡面板采用迭代去均值（alternating projections），迭代至收敛。
输入：data/processed/dml_panel.csv
输出：data/processed/dml_panel_within.csv
"""
import os
import json
import numpy as np
import pandas as pd

os.chdir(Path(__file__).resolve().parents[3] if "Path" in globals() else os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

df = pd.read_csv("data/processed/dml_panel.csv")
print(f"读取数据：{len(df)} 行，{df.columns.tolist()}")

# 检查关键列缺失
assert df['county_code'].notna().all(), "county_code 存在缺失值"
assert df['year'].notna().all(), "year 存在缺失值"

cols = [
    'gdp_growth_pc', 'D2', 'D1', 'fiscal_autonomy',
    'ln_fiscal_exp_pc', 'primary_ratio', 'secondary_ratio',
    'ln_pop', 'gov_scale'
]
existing_cols = [c for c in cols if c in df.columns]
missing_cols = [c for c in cols if c not in df.columns]
if missing_cols:
    print(f"警告：以下列不存在，将跳过：{missing_cols}")


def within_transform_iterative(df: pd.DataFrame, cols: list,
                                tol: float = 1e-10, max_iter: int = 500) -> pd.DataFrame:
    """
    双向固定效应 within 变换（迭代去均值，适用于不平衡面板）。
    算法：交替投影（Gaure 2013 / Mundlak 迭代）
    """
    df = df.copy()
    county = df['county_code']
    year = df['year']

    for col in cols:
        y = df[col].values.astype(float).copy()
        for _ in range(max_iter):
            y_old = y.copy()
            # 减去县均值
            county_means = pd.Series(y, index=df.index).groupby(county).transform('mean').values
            y = y - county_means
            # 减去年均值
            year_means = pd.Series(y, index=df.index).groupby(year).transform('mean').values
            y = y - year_means
            # 检查收敛
            if np.max(np.abs(y - y_old)) < tol:
                break
        df[col + '_w'] = y

    return df


df_w = within_transform_iterative(df, existing_cols)

# 验证1：within 均值接近0
mean_D2_w = abs(df_w['D2_w'].mean())
print(f"within均值验证通过（D2_w均值绝对值={mean_D2_w:.2e}）")
assert mean_D2_w < 1e-6, f"within均值验证失败：{mean_D2_w}"

# 验证2：县均值接近0
county_max_D2 = df_w.groupby('county_code')['D2_w'].mean().abs().max()
print(f"县均值验证通过（D2_w县最大绝对均值={county_max_D2:.2e}）")
assert county_max_D2 < 1e-6, f"县均值验证失败：max={county_max_D2}"

# 验证3：年均值接近0
year_max_D2 = df_w.groupby('year')['D2_w'].mean().abs().max()
print(f"年均值验证通过（D2_w年最大绝对均值={year_max_D2:.2e}）")
assert year_max_D2 < 1e-6, f"年均值验证失败：max={year_max_D2}"

# 输出统计摘要
print("\n=== within 变换结果摘要 ===")
w_cols = [c + '_w' for c in existing_cols]
print(df_w[w_cols].describe().round(6))

# 保存
df_w.to_csv("data/processed/dml_panel_within.csv", index=False)
print(f"\n已保存：data/processed/dml_panel_within.csv（{len(df_w)} 行，{len(df_w.columns)} 列）")

# 保存验证结果
os.makedirs("outputs/logs", exist_ok=True)
validation_results = {
    'mean_D2_w': float(mean_D2_w),
    'county_max_D2_w': float(county_max_D2),
    'year_max_D2_w': float(year_max_D2),
    'n_rows': len(df_w),
    'w_cols': w_cols,
}
with open("outputs/logs/T08_validation.json", "w") as f:
    json.dump(validation_results, f, indent=2)
print("验证结果已保存至 outputs/logs/T08_validation.json")
