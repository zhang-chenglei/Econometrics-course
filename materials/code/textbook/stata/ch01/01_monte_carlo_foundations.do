* 第1章案例：从样本均值到样本回归线
clear all
set more off
set seed 20260910
capture mkdir output

* ------------------------------------------------------------
* 任务1：大数定律
* ------------------------------------------------------------
set obs 1000
gen z = -2*ln(runiform())
gen running_mean = sum(z)/_n
gen sample_size = _n
twoway (line running_mean sample_size, lcolor(navy)), ///
    yline(2, lcolor(maroon) lpattern(dash)) ///
    title("A. 大数定律") xtitle("累计样本量") ytitle("累计样本均值")
graph save output/ch01_lln.gph, replace
list running_mean in 10
list running_mean in 100
list running_mean in 1000

* ------------------------------------------------------------
* 任务2：中心极限定理
* ------------------------------------------------------------
capture program drop draw_mean
program define draw_mean, rclass
    syntax, N(integer)
    drop _all
    set obs `n'
    gen z = -2*ln(runiform())
    quietly summarize z
    return scalar zmean = r(mean)
end

tempfile clt_all part
simulate zmean=r(zmean), reps(3000) nodots: draw_mean, n(1)
gen n = 1
save `clt_all', replace
foreach size in 5 30 100 {
    simulate zmean=r(zmean), reps(3000) nodots: draw_mean, n(`size')
    gen n = `size'
    save `part', replace
    use `clt_all', clear
    append using `part'
    save `clt_all', replace
}
use `clt_all', clear
gen zstd = sqrt(n)*(zmean-2)/2
twoway (kdensity zstd if n==1, lcolor(gs8) lpattern(dot)) ///
       (kdensity zstd if n==5, lcolor(orange)) ///
       (kdensity zstd if n==30, lcolor(blue)) ///
       (kdensity zstd if n==100, lcolor(green)) ///
       (function y=normalden(x), range(-3.5 5) lcolor(black) lpattern(dash)), ///
       title("B. 中心极限定理") xtitle("标准化数值") ytitle("密度") ///
       legend(order(1 "原始观测" 2 "n=5" 3 "n=30" 4 "n=100" 5 "标准正态"))
graph save output/ch01_clt.gph, replace

* ------------------------------------------------------------
* 任务3：OLS斜率的重复抽样分布
* ------------------------------------------------------------
capture program drop draw_ols
program define draw_ols, rclass
    syntax, N(integer)
    drop _all
    set obs `n'
    gen x = 10*runiform()
    gen y = 2 + 0.5*x + rnormal()
    quietly regress y x
    return scalar b1 = _b[x]
end

tempfile ols_all
simulate b1=r(b1), reps(3000) nodots: draw_ols, n(30)
gen n = 30
save `ols_all', replace
foreach size in 100 500 {
    simulate b1=r(b1), reps(3000) nodots: draw_ols, n(`size')
    gen n = `size'
    save `part', replace
    use `ols_all', clear
    append using `part'
    save `ols_all', replace
}
use `ols_all', clear
table n, statistic(mean b1) statistic(sd b1)
twoway (kdensity b1 if n==30, lcolor(orange)) ///
       (kdensity b1 if n==100, lcolor(blue)) ///
       (kdensity b1 if n==500, lcolor(green)), ///
       xline(0.5, lcolor(black) lpattern(dash)) ///
       title("C. OLS斜率的抽样分布") xtitle("斜率估计值") ytitle("密度") ///
       legend(order(1 "n=30" 2 "n=100" 3 "n=500"))
graph save output/ch01_ols.gph, replace

graph combine output/ch01_lln.gph output/ch01_clt.gph output/ch01_ols.gph, ///
    cols(3) title("从样本均值到OLS斜率")
graph export output/ch01-monte-carlo-foundations.png, width(3200) replace
