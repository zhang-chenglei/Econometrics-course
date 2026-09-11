/*══════════════════════════════════════════════════════════════
  第3章 多元线性回归：推断 — 第一类错误模拟
  配套教材：《计量经济学：理论与实践》
  功能：真实斜率为0时，观察5%显著性水平下的错误拒绝比例
  ══════════════════════════════════════════════════════════════*/

clear
set more off
set seed 20250704

local sims 1000
local n 50
local alpha 0.05
local beta 0

tempfile results
postfile handle t_value p_value reject using `results', replace

forvalues s = 1/`sims' {
    quietly {
        clear
        set obs `n'
        gen x = rnormal()
        gen u = rnormal()
        gen y = `beta' * x + u
        regress y x
        local t = _b[x] / _se[x]
        local p = 2 * ttail(e(df_r), abs(`t'))
        local reject = (`p' < `alpha')
        post handle (`t') (`p') (`reject')
    }
}

postclose handle
use `results', clear

summarize reject
display "重复次数 = `sims'"
display "显著性水平 = `alpha'"
display "第一类错误次数 = " r(sum)
display "第一类错误比例 = " r(mean)

local critical = invttail(`n' - 2, `alpha'/2)
histogram t_value, frequency width(0.25) ///
    xline(-`critical' `critical', lcolor(red) lpattern(dash)) ///
    title("真实斜率为0时的t值分布") ///
    xtitle("t值") ytitle("次数")

display "解释提示：真实斜率为0时，拒绝比例应接近设定的显著性水平。"
