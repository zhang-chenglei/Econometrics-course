"""第3讲实验二学生起始文件：只生成模型诊断数据，不包含回归答案。"""

import numpy as np
import pandas as pd

np.random.seed(20250710)
n = 800
educ = np.clip(np.round(np.random.normal(14, 2, n)), 9, 22).astype(int)
exper = np.clip(np.round(np.random.normal(12, 6, n)), 0, 35).astype(int)
female = np.random.binomial(1, 0.48, n)
urban = np.random.binomial(1, 0.55, n)
ability = np.random.normal(0, 1, n) + 0.3 * (educ - 14) / 2
city_scale = np.random.normal(0, 1, n)
city_gdp_pc = 40000 + 15000 * city_scale + np.random.normal(0, 3000, n)
city_pop = 400 + 150 * city_scale + np.random.normal(0, 30, n)
u = np.random.normal(0, np.sqrt(0.2 + 0.03 * exper), n)

ln_wage = (
    5.0
    + 0.08 * educ
    + 0.04 * exper
    - 0.0006 * exper**2
    - 0.15 * female
    + 0.18 * urban
    + 0.05 * ability
    + 0.000005 * city_gdp_pc
    + 0.0001 * city_pop
    + u
)

diag = pd.DataFrame(
    {
        "ln_wage": ln_wage,
        "educ": educ,
        "exper": exper,
        "exper2": exper**2,
        "female": female,
        "urban": urban,
        "city_gdp_pc": city_gdp_pc,
        "city_pop": city_pop,
        "ability": ability,
    }
)

print("实验二数据已生成。")
print("样本量：", len(diag))
print(diag.head())
print("请在本起始文件的副本末尾继续编写任务四的诊断代码。")
