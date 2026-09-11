/*══════════════════════════════════════════════════════════════
  第5章 模型设定诊断 — 案例实践
  配套教材：《计量经济学：理论与实践》
  功能：生成模拟工资数据，依次完成四个任务：
        任务1：遗漏变量诊断
        任务2：多重共线性诊断（VIF）
        任务3：异方差检验与稳健标准误
        任务4：综合诊断报告整合提示
  ══════════════════════════════════════════════════════════════*/

clear
set more off
set seed 20250710
set obs 800

* ============================================================
* 数据生成
* ============================================================
gen educ   = round(rnormal(14, 2))
replace educ = 9  if educ < 9
replace educ = 22 if educ > 22
gen exper  = round(rnormal(12, 6))
replace exper = 0  if exper < 0
replace exper = 35 if exper > 35
gen exper2 = exper^2
gen female = rbinomial(1, 0.48)
gen urban  = rbinomial(1, 0.55)

* ability — 个人能力，与 educ 正相关（在真实研究中不可观测）
gen ability = rnormal(0, 1) + 0.3*(educ - 14)/2

* 城市经济变量 — 共用一个潜在因子，导致高度相关
gen city_scale = rnormal(0, 1)
gen city_gdp_pc = 40000 + 15000*city_scale + rnormal(0, 3000)
gen city_pop = 400 + 150*city_scale + rnormal(0, 30)

* 异方差误差项 — 方差随 exper 增大
gen u = rnormal(0, sqrt(0.2 + 0.03*exper))

gen ln_wage = 5.0 + 0.08*educ + 0.04*exper - 0.0006*exper2 ///
              - 0.15*female + 0.18*urban + 0.05*ability ///
              + 0.000005*city_gdp_pc + 0.0001*city_pop + u
gen wage = exp(ln_wage)

label variable ln_wage  "对数月工资"
label variable wage     "月工资（元）"
label variable educ     "受教育年限"
label variable exper    "工作经验（年）"
label variable exper2   "工作经验平方"
label variable female   "女性（=1）"
label variable urban    "城市（=1）"
label variable ability  "个人能力（不可观测）"
label variable city_gdp_pc "城市人均GDP（元）"
label variable city_pop "城市人口（万人）"

* ============================================================
* 任务1：遗漏变量诊断
* ============================================================
display _n "========== 任务1：遗漏变量诊断 =========="

* 天真模型 — 遗漏 ability
reg ln_wage educ exper exper2 female urban city_gdp_pc city_pop, robust
estimates store m_naive
local b_naive_educ = _b[educ]
local se_naive_educ = _se[educ]

* 完整模型 — 包含 ability
reg ln_wage educ exper exper2 female urban city_gdp_pc city_pop ability, robust
estimates store m_full
local b_full_educ = _b[educ]
local se_full_educ = _se[educ]

estimates table m_naive m_full, ///
    stats(N r2) b(%9.4f) se(%9.4f) ///
    drop(_cons)

display _n "=== 教育系数对比 ==="
display "  天真模型（遗漏ability）: " %9.5f `b_naive_educ' "  (SE: " %9.5f `se_naive_educ' ")"
display "  完整模型（包含ability）: " %9.5f `b_full_educ' "  (SE: " %9.5f `se_full_educ' ")"
display "  偏误 = " %9.5f (`b_naive_educ' - `b_full_educ')
display "  偏误方向：ability与educ正相关，ability对工资有正向影响"
display "           → 遗漏导致 educ 系数被高估"

* ============================================================
* 任务2：多重共线性诊断
* ============================================================
display _n "========== 任务2：多重共线性诊断 =========="

* 相关系数矩阵
display _n "--- 解释变量相关系数矩阵 ---"
corr educ exper female urban city_gdp_pc city_pop ability

* VIF 诊断（完整模型）
display _n "--- VIF 诊断（完整模型）---"
reg ln_wage educ exper exper2 female urban city_gdp_pc city_pop ability
vif

* 处理共线性：删除 city_pop 后重新计算 VIF
display _n "--- VIF 诊断（删除 city_pop 后）---"
reg ln_wage educ exper exper2 female urban city_gdp_pc ability
vif

display _n "=== 共线性处理提示 ==="
display "  如果 city_gdp_pc 和 city_pop 的 VIF > 10，三种处理方式："
display "  ① 删除其中一个（如果理论上不重要）"
display "  ② 按理论构造有明确含义的综合指标，而不是机械相除"
display "  ③ 保留但谨慎解读系数（标准误偏大可能导致不显著）"

* ============================================================
* 任务3：异方差检验与稳健标准误
* ============================================================
display _n "========== 任务3：异方差检验与稳健标准误 =========="

* 使用完整模型（用 city_gdp_pc 不含 city_pop 以避免共线性干扰）
reg ln_wage educ exper exper2 female urban city_gdp_pc ability

* Breusch-Pagan 检验
display _n "--- Breusch-Pagan 检验 ---"
estat hettest
display "  H0: 同方差  拒绝H0 → 存在异方差"

* White 检验
display _n "--- White 检验 ---"
estat imtest, white

* 传统标准误 vs 稳健标准误
display _n "--- 传统 SE vs 稳健 SE ---"
reg ln_wage educ exper exper2 female urban city_gdp_pc ability
estimates store m_conv

reg ln_wage educ exper exper2 female urban city_gdp_pc ability, robust
estimates store m_rob

estimates table m_conv m_rob, ///
    stats(N r2) b(%9.4f) se(%9.4f) ///
    drop(_cons)

display _n "=== 传统SE vs 稳健SE 比较提示 ==="
display "  1. 点估计（系数）完全相同 — 稳健SE只修正标准误，不改变系数"
display "  2. 关注SE变化最大的变量 — 通常与异方差来源（exper）相关"
display "  3. 如果核心变量（educ）的SE变化很小，异方差对该结论影响有限"
display "  4. 安全做法：在论文中报告稳健标准误"

* ============================================================
* 任务4：综合诊断报告整合提示
* ============================================================
display _n "========== 任务4：综合诊断报告整合提示 =========="
display "请将前三项任务的发现整合为一份不超过400字的诊断报告："
display "  1. 遗漏变量：ability被遗漏时educ系数偏误的方向与大小"
display "  2. 多重共线：VIF最高的变量及你选择的处理方式与理由"
display "  3. 异方差：BP/White检验结果，传统SE vs 稳健SE的关键差异"
display "  4. 内部有效性总体评价：哪些系数估计可信，哪些需存疑"
display "  5. 如果时间允许，提出一种可能的模型改进方案"
