"""第3讲实验一学生起始文件：只生成模型形式实验数据，不包含回归答案。"""

import numpy as np
import pandas as pd

np.random.seed(20250710)
n = 800
female = np.random.binomial(1, 0.48, size=n)
urban = np.random.binomial(1, 0.55, size=n)
educ = np.clip(np.round(np.random.normal(14, 2, size=n)), 9, 22).astype(int)
exper = np.clip(np.round(np.random.normal(12, 6, size=n)), 0, 35).astype(int)
u = np.random.normal(0, 0.35, size=n)

ln_wage = (
    5.0
    + 0.08 * educ
    + 0.04 * exper
    - 0.0006 * exper**2
    - 0.15 * female
    + 0.18 * urban
    + 0.02 * educ * female
    + 0.015 * educ * urban
    + u
)

df = pd.DataFrame(
    {
        "wage": np.exp(ln_wage),
        "ln_wage": ln_wage,
        "educ": educ,
        "exper": exper,
        "female": female,
        "urban": urban,
    }
)

print("实验一数据已生成。")
print("样本量：", len(df))
print(df.head())
print("请在本起始文件的副本末尾继续编写任务一至任务三的代码。")
