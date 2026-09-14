* 第3章案例：读懂一张成绩回归表
* 生成正文图3-3（回归表中各系数的点估计与95%置信区间）。
*
* 数据与第2章完全同源：同一份数据生成过程、同一个随机种子，因此两章的数字可以直接
* 对照。第2章关心"AI 系数等于多少"，本章关心"这个数字有多确定"。

clear all
set more off
set seed 20260430
capture mkdir output

* ------------------------------------------------------------
* 1. 与第2章相同的数据生成过程
* ------------------------------------------------------------
set obs 800
gen ability = rnormal(0, 1)
gen age     = round(rnormal(20, 1.6))
replace age = 17 if age < 17
replace age = 26 if age > 26
gen female  = runiform() < 0.5

gen ai = 8 + 3.2*ability + 0.25*(age-20) - 1.2*female + rnormal(0, 3.5)
replace ai = 0  if ai < 0
replace ai = 30 if ai > 30

gen score = 68 + 1.25*ai + 4.5*ability + 0.6*(age-20) - 1.8*female + rnormal(0, 5.5)

* ------------------------------------------------------------
* 2. 估计完整模型并整理回归表
* ------------------------------------------------------------
regress score ai age female ability

display _newline "回归表（被解释变量：课程成绩）："
matrix b  = e(b)
matrix V  = e(V)
local names : colnames b
display _newline %-16s "变量" %12s "系数" %12s "标准误" %10s "t值" %12s "95%CI下" %12s "95%CI上"
foreach v of local names {
    local coef = _b[`v']
    local se   = _se[`v']
    local t    = `coef'/`se'
    local lo   = `coef' - invttail(e(df_r), 0.025)*`se'
    local hi   = `coef' + invttail(e(df_r), 0.025)*`se'
    display %-16s "`v'" %12.5f `coef' %12.5f `se' %10.3f `t' %12.5f `lo' %12.5f `hi'
}
display _newline "样本量：" e(N) "，R² = " %6.4f e(r2) "，调整R² = " %6.4f e(r2_a)
display "整体F统计量：" %9.3f e(F) "，p = " %10.4g e(p)

display _newline "AI 系数的手工t值：" %9.5f _b[ai]/_se[ai]

* ------------------------------------------------------------
* 3. 联合检验：年龄与性别能否同时排除
* ------------------------------------------------------------
display _newline "联合检验 H0: age = female = 0"
test age female

* ------------------------------------------------------------
* 4. 导出回归表
* ------------------------------------------------------------
tempname mem
tempfile tab
postfile `mem' str12 variable double coef double std_err double t_value ///
    double p_value double ci_lower double ci_upper using `tab', replace
foreach v in ai age female ability {
    local coef = _b[`v']
    local se   = _se[`v']
    local p    = 2*ttail(e(df_r), abs(`coef'/`se'))
    local lo   = `coef' - invttail(e(df_r), 0.025)*`se'
    local hi   = `coef' + invttail(e(df_r), 0.025)*`se'
    post `mem' ("`v'") (`coef') (`se') (`coef'/`se') (`p') (`lo') (`hi')
}
postclose `mem'
use `tab', clear
export delimited using "ch03_regression_table.csv", replace
list, noobs

* ------------------------------------------------------------
* 5. 图3-3：各系数的点估计与置信区间（截距不绘制）
* ------------------------------------------------------------
* 数据顺序为 ai, age, female, ability；令 ai 排在最上方（y 值最大）
gen byte ord = 5 - _n
label define vlab 1 "认知能力" 2 "性别（女性=1）" 3 "年龄" 4 "AI 使用时间"
label values ord vlab

twoway (rcap ci_lower ci_upper ord, horizontal lcolor(gs10) lwidth(med)) ///
       (scatter ord coef, msymbol(O) mcolor(navy) msize(medlarge)), ///
    ylabel(1 2 3 4, valuelabel angle(0) labsize(small) noticks) ///
    xline(0, lcolor(black) lpattern(dash) lwidth(med)) ///
    ytitle("") xtitle("回归系数及 95% 置信区间") ///
    title("成绩回归表：点估计与不确定性") ///
    legend(off)
graph save output/ch03_regression_table.gph, replace
graph export output/ch03-fig3-regression-table-and-ci.png, width(2400) replace

display _newline "图形已保存至 output/"
