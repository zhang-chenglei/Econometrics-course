/*══════════════════════════════════════════════════════════════
  第3章 多元线性回归：推断 — 第二类错误与检验功效模拟
  配套教材：《计量经济学：理论与实践》
  功能：比较不同真实效应和样本量下的拒绝比例
  ══════════════════════════════════════════════════════════════*/

clear
set more off
set seed 20250705

local sims 1000
local alpha 0.05

tempfile results
postfile handle n beta reject_rate power type_ii_rate using `results', replace

foreach n in 30 100 300 {
    foreach beta in 0.10 0.30 0.50 {
        local rejects 0

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
                if (`p' < `alpha') {
                    local rejects = `rejects' + 1
                }
            }
        }

        local reject_rate = `rejects' / `sims'
        local power = `reject_rate'
        local type_ii_rate = 1 - `power'
        post handle (`n') (`beta') (`reject_rate') (`power') (`type_ii_rate')
    }
}

postclose handle
use `results', clear

format reject_rate power type_ii_rate %6.3f
list, sepby(n)

twoway ///
    connected power beta if n == 30, sort lcolor(navy) mcolor(navy) ///
    || connected power beta if n == 100, sort lcolor(maroon) mcolor(maroon) ///
    || connected power beta if n == 300, sort lcolor(forest_green) mcolor(forest_green) ///
    , legend(order(1 "n=30" 2 "n=100" 3 "n=300")) ///
    title("效应大小、样本量与检验功效") ///
    xtitle("真实斜率") ytitle("拒绝原假设的比例")

display "解释提示：真实效应越大、样本量越大，检验功效通常越高。"
