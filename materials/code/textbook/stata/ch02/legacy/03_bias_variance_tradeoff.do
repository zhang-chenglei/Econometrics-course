/*══════════════════════════════════════════════════════════════
  第2章 多元线性回归：估计 — 偏差和方差权衡模拟
  配套教材：《计量经济学：理论与实践》
  功能：重复抽样比较完整模型、遗漏变量模型、加入高相关噪声变量模型
  ══════════════════════════════════════════════════════════════*/

clear all
set more off
set seed 20250703

local sims = 1000
local n = 1000

tempname sim
postfile `sim' b1_full b1_omit b1_noise using ch02_bias_variance_results.dta, replace

forval i = 1/`sims' {
    clear
    set obs `n'

    * 射箭成绩类比：y 越小表示离靶心越近
    gen x1 = rnormal(10,3)          // 练习时间
    * 让天气与练习时间正相关，使遗漏 x2 会产生系统偏误
    gen x2 = 5 + 0.5*(x1-10) + rnormal(0,2)
    gen x3 = rbinomial(1,0.5)       // 工具质量
    gen x4 = x1 + rnormal(0,0.1)    // 与 x1 高度相关的噪声变量
    gen u  = rnormal(0,1)
    gen y  = 10 - 0.5*x1 + 0.3*x2 - 1.5*x3 + u

    * 模型1：完整模型
    quietly regress y x1 x2 x3
    local coef_full = _b[x1]

    * 模型2：遗漏 x2
    quietly regress y x1 x3
    local coef_omit = _b[x1]

    * 模型3：加入高相关噪声变量 x4
    quietly regress y x1 x2 x3 x4
    local coef_noise = _b[x1]

    post `sim' (`coef_full') (`coef_omit') (`coef_noise')
}

postclose `sim'

use ch02_bias_variance_results.dta, clear

summarize b1_full b1_omit b1_noise

histogram b1_full, bin(40) normal color(blue%45) ///
    title("完整模型：x1系数分布") xtitle("x1系数")

histogram b1_omit, bin(40) normal color(red%45) ///
    title("遗漏变量模型：x1系数分布") xtitle("x1系数")

histogram b1_noise, bin(40) normal color(green%45) ///
    title("加入高相关噪声变量：x1系数分布") xtitle("x1系数")

display "真实 x1 系数 = -0.5"
display "比较均值是否偏离真实值，以及分布是否更分散。"
