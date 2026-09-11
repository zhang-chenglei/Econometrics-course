/*══════════════════════════════════════════════════════════════
  第1章 一元线性回归 — 蒙特卡洛模拟：单次抽样
  配套教材：《计量经济学：理论与实践》
  功能：生成一个DGP样本，估计OLS，比较样本回归线与总体回归线
  ══════════════════════════════════════════════════════════════*/

clear

set seed 20250703              // 固定随机种子，保证可复现
set obs 100                    // 样本容量 n = 100

gen x = runiform(0,10)         // X ~ Uniform(0, 10)
gen u = rnormal(0,1)           // u ~ N(0, 1)
gen y = 2 + 0.5*x + u          // 真实模型: Y = 2 + 0.5 X + u

reg y x                        // OLS 估计

twoway (scatter y x, msymbol(circle) mcolor(gs8))          ///  散点图
       (lfit y x, lcolor(blue))                            ///  样本回归线
       (function y = 2 + 0.5*x, range(0 10)                ///  总体回归线
         lcolor(red) lpattern(dash)),                         ///
       legend(label(2 "样本回归线") label(3 "总体回归线"))      ///
       title("一次抽样：样本回归线 vs 总体回归线")
