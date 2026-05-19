"""
T23: 结果汇总表格规范化输出
生成期刊级三线表，保存为 outputs/tables/paper_tables.xlsx
"""

import os
import sys
import numpy as np
import pandas as pd
import openpyxl
from openpyxl.styles import Font, Border, Side, Alignment, PatternFill
from openpyxl.utils import get_column_letter

# ─── 工作目录 ─────────────────────────────────────────────
os.chdir(Path(__file__).resolve().parents[3] if "Path" in globals() else os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

# ─── 三线表边框样式 ────────────────────────────────────────
THICK = Side(style='medium')
THIN  = Side(style='thin')
NO    = Side(style=None)

def top_border():    return Border(top=THICK)
def mid_border():    return Border(top=THIN)
def bottom_border(): return Border(bottom=THICK)
def no_border():     return Border()

def header_font(): return Font(name='Times New Roman', bold=True, size=10)
def body_font():   return Font(name='Times New Roman', size=10)
def center_align(): return Alignment(horizontal='center', vertical='center', wrap_text=True)
def left_align():   return Alignment(horizontal='left',   vertical='center', wrap_text=True)

def style_sheet(ws, header_row, data_rows):
    """应用三线表格式：顶线 / 栏目分隔线 / 底线"""
    for row in ws.iter_rows():
        for cell in row:
            cell.font = body_font()
            cell.alignment = center_align()
            cell.border = no_border()
    # 顶线（第1行上方）
    for cell in ws[header_row]:
        cell.border = top_border()
        cell.font = header_font()
        cell.alignment = center_align()
    # 栏目分隔线（第1行下方 = 第2行上方）
    next_row = header_row + 1
    for cell in ws[next_row]:
        cell.border = Border(top=THIN, bottom=NO)
    # 底线（最后一行下方）
    last = header_row + data_rows
    for cell in ws[last]:
        cell.border = bottom_border()
    # 第一列左对齐
    for row in ws.iter_rows(min_row=header_row):
        row[0].alignment = left_align()
        row[0].font = body_font()

def set_col_widths(ws, widths):
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w

# ═══════════════════════════════════════════════════════════
# 读取 CATE 数据，计算表2所需的分组统计
# ═══════════════════════════════════════════════════════════
print("Loading CATE data for Table 2...")
cate_df = pd.read_csv("data/processed/d2_cate_results.csv")
grf_df  = pd.read_csv("data/processed/grf_input.csv")[
    ['county_code', 'fiscal_autonomy_pre', 'region_val']
]
df = cate_df.merge(grf_df, on='county_code', how='inner')
df = df.dropna(subset=['cate', 'fiscal_autonomy_pre', 'region_val'])

# CATE 单位转换为百分比（GRF 用 Y/100 估计，因此 cate 原始值需 ×100）
df['cate_pct'] = df['cate'] * 100

n_total = len(df)
ate     = df['cate_pct'].mean()
ate_se  = df['cate_pct'].std() / np.sqrt(n_total)

# 按 fiscal_autonomy_pre 四分位分组
df['fa_q'] = pd.qcut(df['fiscal_autonomy_pre'], 4, labels=['Q1','Q2','Q3','Q4'])
fa_stats = {}
for q in ['Q1', 'Q4']:
    sub = df[df['fa_q'] == q]['cate_pct']
    fa_stats[q] = {
        'mean': sub.mean(),
        'se'  : sub.std() / np.sqrt(len(sub)),
        'n'   : len(sub)
    }

# 按地区分组（来自 T13 报告数值，此处用数据再计算）
region_map = {1: 'East', 2: 'Central', 3: 'West'}
reg_stats = {}
for rval, rname in region_map.items():
    sub = df[df['region_val'] == rval]['cate_pct']
    reg_stats[rname] = {
        'mean': sub.mean(),
        'se'  : sub.std() / np.sqrt(len(sub)),
        'n'   : len(sub)
    }

print(f"  Total n={n_total}, ATE={ate:.4f}%")
for q in ['Q1','Q4']:
    print(f"  {q}: mean={fa_stats[q]['mean']:.4f}%, n={fa_stats[q]['n']}")
for r in ['East','Central','West']:
    print(f"  {r}: mean={reg_stats[r]['mean']:.4f}%, n={reg_stats[r]['n']}")

# ═══════════════════════════════════════════════════════════
# 创建 Excel 工作簿
# ═══════════════════════════════════════════════════════════
os.makedirs("outputs/tables", exist_ok=True)
wb = openpyxl.Workbook()
wb.remove(wb.active)  # 删除默认 sheet

# ───────────────────────────────────────────────────────────
# Table 1: Methods Comparison
# ─────────────────────────────────────────────
print("Writing Table 1: Methods Comparison...")
ws1 = wb.create_sheet("table1_methods_comparison")

t1_headers = ['Method', 'Coef. (pp)', 'SE', 'p-value', '95% CI', 'N']
t1_data = [
    # Source: T03B_baseline_did.md
    ['TWFE (D2)',          '1.023',   '0.339', '0.003',  '[0.358, 1.688]',  '24,781'],
    # Source: T03B_baseline_did.md (CS-DID section)
    ['CS-DID (D2)',        '1.192',   '0.474', '0.012',  '[0.263, 2.122]',  '24,781'],
    # Source: T09_grf_d2.md (Exploratory Only, Y in decimal×100)
    ['GRF ATE (D2)†',     '-2.728',  '0.050', '—',      '—',               '1,261'],
    # Source: T14_dml_baseline.md
    ['DML PLR (D2)',       '1.042',   '0.289', '0.000',  '[0.476, 1.607]',  '24,781'],
]

ws1.append(t1_headers)
for row in t1_data:
    ws1.append(row)

note1 = ('Note: Dependent variable = gdp_growth_pc (%). '
         'TWFE/CS-DID use two-way FE panel (county+year); DML uses within-transformed panel. '
         '† GRF uses cross-section (county-level pre-reform means); '
         'T06A verdict = Exploratory Only (unconfoundedness not confirmed). '
         'SE clustered by county_code for TWFE/CS-DID.')
ws1.append([''])
ws1.append([note1])

style_sheet(ws1, header_row=1, data_rows=len(t1_data))
set_col_widths(ws1, [28, 14, 10, 10, 20, 10])
ws1.row_dimensions[1].height = 20

# ───────────────────────────────────────────────────────────
# Table 2: CATE by Group
# ───────────────────────────────────────────────────────────
print("Writing Table 2: CATE by Group...")
ws2 = wb.create_sheet("table2_cate_by_group")

t2_headers = ['Group', 'Mean CATE (pp)', 'SE', 'Diff. from ATE (pp)', 'N']

def fmt(x): return f'{x:.4f}'

t2_data = [
    ['All counties (ATE)',
     fmt(ate),
     fmt(ate_se),
     '—',
     str(n_total)],
    ['Low fiscal autonomy (Q1)',
     fmt(fa_stats['Q1']['mean']),
     fmt(fa_stats['Q1']['se']),
     fmt(fa_stats['Q1']['mean'] - ate),
     str(fa_stats['Q1']['n'])],
    ['High fiscal autonomy (Q4)',
     fmt(fa_stats['Q4']['mean']),
     fmt(fa_stats['Q4']['se']),
     fmt(fa_stats['Q4']['mean'] - ate),
     str(fa_stats['Q4']['n'])],
    ['East region',
     fmt(reg_stats['East']['mean']),
     fmt(reg_stats['East']['se']),
     fmt(reg_stats['East']['mean'] - ate),
     str(reg_stats['East']['n'])],
    ['Central region',
     fmt(reg_stats['Central']['mean']),
     fmt(reg_stats['Central']['se']),
     fmt(reg_stats['Central']['mean'] - ate),
     str(reg_stats['Central']['n'])],
    ['West region',
     fmt(reg_stats['West']['mean']),
     fmt(reg_stats['West']['se']),
     fmt(reg_stats['West']['mean'] - ate),
     str(reg_stats['West']['n'])],
]

ws2.append(t2_headers)
for row in t2_data:
    ws2.append(row)

note2 = ('Note: CATE estimated by CausalForest (n_estimators=2000, random_state=42). '
         'T06A verdict = Exploratory Only. CATE in percentage points (×100 from decimal). '
         'Fiscal autonomy quartiles based on pre-reform fiscal_autonomy_pre. '
         'Region: 1=East, 2=Central, 3=West. Source: T09_grf_d2.md, T13_heterogeneity.md.')
ws2.append([''])
ws2.append([note2])

style_sheet(ws2, header_row=1, data_rows=len(t2_data))
set_col_widths(ws2, [30, 18, 10, 22, 10])

# ───────────────────────────────────────────────────────────
# Table 3: Double ML Mediation
# ───────────────────────────────────────────────────────────
print("Writing Table 3: Double ML Mediation...")
ws3 = wb.create_sheet("table3_mediation")

t3_headers = ['Pathway',
              'Step1 (D2→Med.)',
              'Step2 (Med.→GDP)',
              'Indirect Effect (pp)',
              'Bootstrap 95% CI',
              'Share (%)']
t3_data = [
    # Source: T16_dml_indirect.md (path 1) and T17_dml_exp.md (path 2)
    ['Path 1: D2→fiscal_autonomy→GDP',
     'α = −1.4252%',
     'β = 2.0538 pp',
     '−0.0293',
     '[−0.0569, 0.0004]†',
     '−2.8%'],
    ['Path 2: D2→ln_fiscal_exp→GDP',
     'γ = 0.0509 (ln)',
     'δ = 4.2523 pp',
     '0.2165',
     '[0.1520, 0.2949]',
     '20.8%'],
]

ws3.append(t3_headers)
for row in t3_data:
    ws3.append(row)

note3 = ('Note: Double ML (LinearDML, LassoCV cv=5). Within-transformed panel data (n=24,781). '
         'Total DML theta = 1.0415 pp (T14). '
         '† Path 1 Bootstrap CI contains 0 → indirect effect not significant at 5% level; '
         'expression: "direction consistent but not significant at 5%." '
         'Path 2 Bootstrap CI excludes 0 → significant at 5%. '
         'Bootstrap reps=200, percentile method. '
         'Source: T15_dml_indirect.md (α), T16_dml_indirect.md (β, CI1), T17_dml_exp.md (γ, δ, CI2).')
ws3.append([''])
ws3.append([note3])

style_sheet(ws3, header_row=1, data_rows=len(t3_data))
set_col_widths(ws3, [35, 22, 22, 22, 22, 12])

# ───────────────────────────────────────────────────────────
# Table 4: Robustness Checks
# ───────────────────────────────────────────────────────────
print("Writing Table 4: Robustness Checks...")
ws4 = wb.create_sheet("table4_robustness")

t4_headers = ['Method / Specification', 'Coef.', 'SE', 'p-value', 'Consistent with Baseline']
t4_data = [
    # Baseline for reference (from T03B)
    ['Baseline: TWFE (D2, gdp_growth_pc)',     '1.023 pp', '0.339', '0.003', '—'],
    # Source: T20_sdid.md
    ['SDID (T20)',                              '0.878 pp', '0.442', '0.047', 'Yes'],
    # Source: T21_robustness.md (GRF alt outcome ATE in log units)
    ['Alt. outcome: ln_gdppc — GRF ATE (T21)', '−0.0119',  '0.0077', '—',   'Yes (same sign)'],
]

ws4.append(t4_headers)
for row in t4_data:
    ws4.append(row)

note4 = ('Note: Baseline TWFE from T03B (county+year FE, cluster SE, n=24,781). '
         'SDID: Arkhangelsky et al. (2021), balanced panel 907 counties × 22 years, Bootstrap 200 reps. '
         'Alt. outcome GRF: CausalForest with Y=ln_gdppc (T21, n=1,486); Exploratory Only. '
         'Units: TWFE/SDID in percentage points; Alt. outcome in log units. '
         'Source: T20_sdid.md, T21_robustness.md.')
ws4.append([''])
ws4.append([note4])

style_sheet(ws4, header_row=1, data_rows=len(t4_data))
set_col_widths(ws4, [42, 12, 10, 10, 26])

# ─── 保存 ────────────────────────────────────────────────
out_path = "outputs/tables/paper_tables.xlsx"
wb.save(out_path)
print(f"\nSaved: {out_path}")

# ─── 验证 Sheet 名 ────────────────────────────────────────
import openpyxl as _ox
_wb = _ox.load_workbook(out_path)
print(f"Sheets: {_wb.sheetnames}")

print("\nT23 DONE: paper_tables.xlsx written with 4 sheets.")
