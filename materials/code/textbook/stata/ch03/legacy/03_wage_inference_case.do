/*══════════════════════════════════════════════════════════════
  第3章 多元线性回归：推断 — 工资决定因素案例
  配套教材：《计量经济学：理论与实践》
  功能：用教学模拟数据练习t检验、置信区间和F检验解读
  ══════════════════════════════════════════════════════════════*/

clear
set more off
set seed 20250706
set obs 800

* 生成教学用工资数据
gen female = rbinomial(1, 0.48)
gen urban = rbinomial(1, 0.55)
gen educ = round(rnormal(14, 2))
replace educ = 9 if educ < 9
replace educ = 22 if educ > 22

gen exper = round(rnormal(12, 6))
replace exper = 0 if exper < 0
replace exper = 35 if exper > 35

gen exper2 = exper^2
gen ability = rnormal()
gen u = rnormal(0, 0.35)

gen ln_wage = 2.2 + 0.085*educ + 0.045*exper - 0.0008*exper2 ///
    - 0.120*female + 0.180*urban + 0.120*ability + u
gen wage = exp(ln_wage)

label variable ln_wage "对数工资"
label variable wage "工资"
label variable educ "受教育年限"
label variable exper "工作经验"
label variable exper2 "工作经验平方"
label variable female "女性"
label variable urban "城市"

summarize wage ln_wage educ exper female urban

regress ln_wage educ exper exper2 female urban
estimates store wage_model

display "教育年限系数 = " _b[educ]
display "教育年限标准误 = " _se[educ]
display "教育年限t值 = " _b[educ] / _se[educ]
display "教育年限近似百分比解释 = " 100 * _b[educ] " %"

test exper exper2

predict fitted_ln_wage, xb
twoway ///
    scatter ln_wage educ, mcolor(gs10) ///
    || lfit ln_wage educ, lcolor(maroon) ///
    , title("教育年限与对数工资") ///
    xtitle("受教育年限") ytitle("对数工资") legend(off)

display "解释提示：本案例是模拟数据，用来训练推断解读，不应直接当作真实因果结论。"
