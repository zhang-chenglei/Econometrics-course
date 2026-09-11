/*══════════════════════════════════════════════════════════════
  第2章 多元线性回归：估计 — 遗漏变量偏误模拟
  配套教材：《计量经济学：理论与实践》
  功能：比较遗漏变量模型与完整模型中 x1 系数的变化
  ══════════════════════════════════════════════════════════════*/

clear
set more off
set seed 20250703
set obs 1000

* 真实数据生成过程：x1 和 x2 正相关，且二者都影响 y
gen x1 = rnormal()
gen x2 = 0.8*x1 + rnormal()
gen u  = rnormal()
gen y  = 2 + 3*x1 + 5*x2 + u

* 模型1：遗漏 x2
reg y x1
estimates store omitted

* 模型2：控制 x2 的完整模型
reg y x1 x2
estimates store full

* 对比两个模型
estimates table omitted full, b se stats(N r2) title("遗漏变量模型 vs 完整模型")

display "真实 x1 系数 = 3"
display "如果遗漏 x2，x1 会吸收部分 x2 的影响，系数通常偏离真实值。"
