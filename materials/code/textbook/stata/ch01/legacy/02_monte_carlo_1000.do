/*══════════════════════════════════════════════════════════════
  第1章 一元线性回归 — 蒙特卡洛模拟
  功能：比较 n=100 与 n=500 时斜率估计值的偏差和精度
  ══════════════════════════════════════════════════════════════*/

clear all
set more off

capture program drop sim_slope
program define sim_slope, rclass
    syntax, N(integer)
    clear
    set obs `n'
    gen x = runiform(0,10)
    gen u = rnormal(0,1)
    gen y = 2 + 0.5*x + u
    quietly regress y x
    return scalar beta1 = _b[x]
end

tempfile sim100 sim500

simulate beta1=r(beta1), reps(1000) seed(20250703): sim_slope, n(100)
gen n = 100
save `sim100'

simulate beta1=r(beta1), reps(1000) seed(20250704): sim_slope, n(500)
gen n = 500
save `sim500'

use `sim100', clear
append using `sim500'
save betasim.dta, replace

gen bias = beta1 - 0.5
tabstat beta1 bias, by(n) statistics(mean sd n)

twoway ///
    (kdensity beta1 if n==100, lcolor(navy)) ///
    (kdensity beta1 if n==500, lcolor(maroon)), ///
    xline(0.5, lpattern(dash) lcolor(forest_green)) ///
    legend(order(1 "n=100" 2 "n=500")) ///
    title("不同样本量下斜率估计值的分布") ///
    xtitle("斜率估计值") ytitle("密度")

display "均值接近0.5反映偏差较小；分布变窄反映估计精度提高。"
