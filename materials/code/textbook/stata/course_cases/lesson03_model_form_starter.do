* 第3讲实验一学生起始文件：只生成模型形式实验数据，不包含回归答案
clear
set more off
set seed 20250710
set obs 800

gen female = rbinomial(1, 0.48)
gen urban  = rbinomial(1, 0.55)
gen educ   = round(rnormal(14, 2))
replace educ = 9  if educ < 9
replace educ = 22 if educ > 22
gen exper  = round(rnormal(12, 6))
replace exper = 0  if exper < 0
replace exper = 35 if exper > 35
gen u = rnormal(0, 0.35)

gen ln_wage = 5.0 + 0.08*educ + 0.04*exper - 0.0006*exper^2 ///
              - 0.15*female + 0.18*urban + 0.02*educ*female ///
              + 0.015*educ*urban + u
gen wage = exp(ln_wage)

display "实验一数据已生成。"
describe
list in 1/5
