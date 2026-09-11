* 第3章案例：读懂一张工资回归表
clear all
set more off
set seed 20260910
capture mkdir output
set obs 800

gen background = rnormal()
gen educ = 14 + 1.1*background + rnormal(0,1.2)
gen exper = 12 + 1.8*background + rnormal(0,3)
gen tenure = 4 + 0.25*exper + 0.5*background + rnormal(0,1.8)
gen u = rnormal(0,0.25)
gen ln_wage = 1.6 + 0.08*educ + 0.035*exper + 0.02*tenure + u

regress ln_wage educ exper tenure
estimates store wage_model
display "手工核对教育t值 = " _b[educ]/_se[educ]
display "教育95%置信区间 = [" _b[educ]-invttail(e(df_r),0.025)*_se[educ] ", " ///
    _b[educ]+invttail(e(df_r),0.025)*_se[educ] "]"
test exper tenure

* 整理三个斜率及95%置信区间用于绘图
estimates restore wage_model
local df = e(df_r)
local critical = invttail(`df',0.025)
foreach v in educ exper tenure {
    local b_`v' = _b[`v']
    local se_`v' = _se[`v']
}
preserve
clear
set obs 3
gen order = _n
gen str12 variable = ""
replace variable = "教育年限" in 1
replace variable = "工作经验" in 2
replace variable = "任职年限" in 3
gen coef = .
gen se = .
replace coef = `b_educ' in 1
replace coef = `b_exper' in 2
replace coef = `b_tenure' in 3
replace se = `se_educ' in 1
replace se = `se_exper' in 2
replace se = `se_tenure' in 3
gen lower = coef - `critical'*se
gen upper = coef + `critical'*se
twoway (rcap lower upper order, horizontal lcolor(navy)) ///
       (scatter order coef, mcolor(maroon)), ///
       xline(0, lpattern(dash) lcolor(black)) ///
       ylabel(1 "教育年限" 2 "工作经验" 3 "任职年限") ///
       ytitle("") xtitle("系数及95%置信区间") ///
       title("工资回归表中的点估计与区间") legend(off)
graph export output/ch03-regression-table-and-ci.png, width(1800) replace
restore
