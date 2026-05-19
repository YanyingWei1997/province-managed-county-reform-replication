# 变量名映射表 - 省管县改革研究项目 v2

**生成任务**：T03  
**生成日期**：2026-04-23  
**数据来源**：panel_analysis_public.dta（36888观测，56变量，1537县，2000-2023）

---

## 核查结论

**所有预期变量均存在，变量名与 AGENTS.md 完全一致，无需映射替代。**

---

## 变量存在性核查表

| 角色 | 预期变量名 | 实际变量名 | 状态 | 数据类型 | 非空数 | 缺失数 |
|------|-----------|-----------|------|---------|--------|--------|
| 面板标识 | county_code | county_code | ✅ 存在 | long | 36888 | 0 |
| 时间标识 | year | year | ✅ 存在 | long | 36888 | 0 |
| 处理变量（总） | D | D | ✅ 存在 | long | 36888 | 0 |
| 处理变量（行政） | D1 | D1 | ✅ 存在 | long | 36888 | 0 |
| 处理变量（财政） | D2 | D2 | ✅ 存在 | long | 36888 | 0 |
| 改革年份（总） | reform_year | reform_year | ✅ 存在 | double | 23760 | 13128 |
| 改革年份（D1） | D1_year | D1_year | ✅ 存在 | double | 10008 | 26880 |
| 改革年份（D2） | D2_year | D2_year | ✅ 存在 | double | 18984 | 17904 |
| 结果变量（首选） | gdp_growth_pc | gdp_growth_pc | ✅ 存在 | double | 24846 | 12042 |
| 结果变量（稳健） | ln_gdppc | ln_gdppc | ✅ 存在 | double | 26623 | 10265 |
| 中介变量1 | fiscal_autonomy | fiscal_autonomy | ✅ 存在 | double | 36726 | 162 |
| 中介变量2 | ln_fiscal_exp_pc | ln_fiscal_exp_pc | ✅ 存在 | double | 36718 | 170 |
| 控制变量1 | primary_ratio | primary_ratio | ✅ 存在 | double | 36218 | 670 |
| 控制变量2 | secondary_ratio | secondary_ratio | ✅ 存在 | double | 36215 | 673 |
| 控制变量3 | ln_pop | ln_pop | ✅ 存在 | double | 36724 | 164 |
| 控制变量4 | gov_scale | gov_scale | ✅ 存在 | double | 36110 | 778 |
| 地区变量 | region | region | ✅ 存在 | str6 | 36888 | 0 |

---

## 额外可用变量（非预期核查但存在）

| 变量名 | 说明 |
|--------|------|
| high_development | 高发展水平虚拟变量（已构造） |
| high_agriculture | 高农业占比虚拟变量（已构造） |
| is_county_city | 县级市虚拟变量 |
| region_east / region_central / region_west | 地区哑变量（已分解） |
| relative_time | 相对改革时间 |
| event_m6plus ~ event_p10plus | 事件研究窗口虚拟变量（已构造，共17个） |
| transfer_dependence | 转移支付依存度 |
| tertiary_ratio | 第三产业占比 |

---

## 注意事项

1. **region 为字符型**（str6），取值为"东部"、"中部"、"西部"。后续 Python/GRF 分析需编码为数值（1/2/3）。
2. **D2_year 中位数 = 2007**，将用于 T04 控制组伪改革年设置（reform_pivot = 2007）。
3. **fiscal_autonomy_pre、primary_ratio_pre 等改革前均值变量**：原始数据中不存在，需在 T04 中构造（改革前3年均值）。
4. **GRF 协变量**（fiscal_autonomy_pre 等）均需在 T04 中基于 D2_year 计算改革前3年均值。

---

## 变量名映射（无偏差）

本次核查未发现变量名偏差，所有后续任务（T03B~T25）可直接使用 AGENTS.md 中记录的变量名。

**无变量名需要替代或重新映射。**
