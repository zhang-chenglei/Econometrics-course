* 第2章案例：教育、经验与工资——控制变量、遗漏变量与FWL
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

* 任务1：遗漏模型与完整模型
regress ln_wage educ
estimates store omitted
regress ln_wage educ exper tenure
estimates store full
local b_full = _b[educ]
estimates table omitted full, b(%9.4f) se(%9.4f) stats(N r2)
corr educ exper tenure

* 任务2和3：FWL三步法
regress educ exper tenure
predict educ_hat, xb
predict educ_resid, residuals
regress ln_wage exper tenure
predict wage_hat, xb
predict wage_resid, residuals
regress wage_resid educ_resid
display "完整回归教育系数 = " %12.10f `b_full'
display "FWL残差回归斜率 = " %12.10f _b[educ_resid]
display "两者差值 = " %12.3e (`b_full' - _b[educ_resid])

twoway (scatter educ educ_hat, msize(small) mcolor(navy%35)) ///
       (function y=x, range(9 20) lcolor(black) lpattern(dash)), ///
       title("A. 从教育中剔除控制变量") xtitle("预测教育") ytitle("实际教育")
graph save output/ch02_fwl_a.gph, replace

twoway (scatter ln_wage wage_hat, msize(small) mcolor(orange%35)) ///
       (function y=x, range(2 4) lcolor(black) lpattern(dash)), ///
       title("B. 从工资中剔除控制变量") xtitle("预测对数工资") ytitle("实际对数工资")
graph save output/ch02_fwl_b.gph, replace

twoway (scatter wage_resid educ_resid, msize(small) mcolor(gs7%35)) ///
       (lfit wage_resid educ_resid, lcolor(navy)), ///
       title("C. 偏回归图") xtitle("教育残差") ytitle("工资残差")
graph save output/ch02_fwl_c.gph, replace

graph combine output/ch02_fwl_a.gph output/ch02_fwl_b.gph output/ch02_fwl_c.gph, ///
    cols(3) title("FWL定理：先剔除相同控制变量，再比较剩余部分")
graph export output/ch02-fwl-partial-regression.png, width(3200) replace
