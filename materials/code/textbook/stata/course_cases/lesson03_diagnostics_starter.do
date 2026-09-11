* 第3讲实验二学生起始文件：只生成模型诊断数据，不包含回归答案
clear
set more off
set seed 20250710
set obs 800

gen educ = round(rnormal(14, 2))
replace educ = 9  if educ < 9
replace educ = 22 if educ > 22
gen exper = round(rnormal(12, 6))
replace exper = 0  if exper < 0
replace exper = 35 if exper > 35
gen exper2 = exper^2
gen female = rbinomial(1, 0.48)
gen urban = rbinomial(1, 0.55)
gen ability = rnormal(0, 1) + 0.3*(educ - 14)/2
gen city_scale = rnormal(0, 1)
gen city_gdp_pc = 40000 + 15000*city_scale + rnormal(0, 3000)
gen city_pop = 400 + 150*city_scale + rnormal(0, 30)
gen u = rnormal(0, sqrt(0.2 + 0.03*exper))

gen ln_wage = 5.0 + 0.08*educ + 0.04*exper - 0.0006*exper2 ///
              - 0.15*female + 0.18*urban + 0.05*ability ///
              + 0.000005*city_gdp_pc + 0.0001*city_pop + u

display "实验二数据已生成。"
describe
list in 1/5
