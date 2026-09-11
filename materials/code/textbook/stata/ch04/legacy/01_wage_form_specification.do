/*══════════════════════════════════════════════════════════════
  第4章 模型形式扩展 — 案例实践：工资决定因素中的非线性与异质性
  配套教材：《计量经济学：理论与实践》
  功能：生成模拟工资数据，依次完成四个任务：
        任务1：水平模型 vs 对数模型
        任务2：二次项 + 极值点
        任务3：交互项 + 四群体教育回报
        任务4：四模型汇总比较
  ══════════════════════════════════════════════════════════════*/

clear
set more off
set seed 20250710
set obs 800

* ============================================================
* 数据生成
* ============================================================
gen female = rbinomial(1, 0.48)
gen urban  = rbinomial(1, 0.55)
gen educ   = round(rnormal(14, 2))
replace educ = 9  if educ < 9
replace educ = 22 if educ > 22
gen exper  = round(rnormal(12, 6))
replace exper = 0  if exper < 0
replace exper = 35 if exper > 35
gen exper2 = exper^2
gen u = rnormal(0, 0.35)

gen ln_wage = 5.0 + 0.08*educ + 0.04*exper - 0.0006*exper2 ///
              - 0.15*female + 0.18*urban + 0.02*educ*female ///
              + 0.015*educ*urban + u
gen wage = exp(ln_wage)

gen educ_female = educ * female
gen educ_urban  = educ * urban

label variable wage    "月工资（元）"
label variable ln_wage "对数月工资"
label variable educ    "受教育年限"
label variable exper   "工作经验（年）"
label variable exper2  "工作经验平方"
label variable female  "女性（=1）"
label variable urban   "城市（=1）"

* ============================================================
* 任务1：比较线性模型与对数模型
* ============================================================
display _n "========== 任务1：水平模型 vs 对数模型 =========="

reg wage educ exper female urban, robust
estimates store m_linear
local b_linear_educ = _b[educ]

reg ln_wage educ exper female urban, robust
estimates store m_log
local b_log_educ = _b[educ]

estimates table m_linear m_log, ///
    stats(N r2) b(%9.4f) se(%9.4f)

display "水平模型：教育每增1年，wage 平均增加 " `b_linear_educ' " 元"
display "对数模型：教育每增1年，wage 约增加 " 100*`b_log_educ' " %"

* ============================================================
* 任务2：检验工作经验的非线性效应
* ============================================================
display _n "========== 任务2：二次项模型 =========="

reg ln_wage educ exper exper2 female urban, robust
estimates store m_quad

local b1 = _b[exper]
local b2 = _b[exper2]
local turning = -`b1' / (2*`b2')
display "经验一次项 = " `b1' "，平方项 = " `b2'
display "工资峰值的经验年限 ≈ " `turning' " 年"

twoway (scatter ln_wage exper, mcolor(gs10) msize(vsmall))     ///
       (qfit ln_wage exper, lcolor(maroon) lwidth(medthick)),   ///
       xline(`turning', lcolor(navy) lpattern(dash))             ///
       legend(order(1 "观测值" 2 "二次拟合" 3 "峰值"))           ///
       title("工作经验与对数工资（二次拟合）")                    ///
       xtitle("工作经验（年）") ytitle("对数工资")

* ============================================================
* 任务3：分析教育回报的异质性
* ============================================================
display _n "========== 任务3：交互项模型 =========="

reg ln_wage educ exper exper2 female urban educ_female educ_urban, robust
estimates store m_inter

display "=== 四个群体的教育回报（近似百分比） ==="
display "非城市男性: " 100*_b[educ] "%"
lincom educ + educ_urban
display "→ 城市男性"
lincom educ + educ_female
display "→ 非城市女性"
lincom educ + educ_female + educ_urban
display "→ 城市女性"

* ============================================================
* 任务4：模型比较
* ============================================================
display _n "========== 任务4：四模型汇总比较 =========="

estimates table m_linear m_log m_quad m_inter, ///
    stats(N r2) b(%9.4f) se(%9.4f) ///
    drop(_cons)

display "模型选择思考："
display "  水平模型 → 适合讨论绝对金额变化"
display "  对数模型 → 适合讨论百分比变化，缓解右偏"
display "  +二次项  → 适合讨论边际递减趋势"
display "  +交互项  → 适合讨论群体异质性"
display "不是越复杂越好，取决于你想回答什么问题。"
