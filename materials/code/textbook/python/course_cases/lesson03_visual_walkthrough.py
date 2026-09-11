"""第3讲：模型设定与模型诊断的可视化案例。

运行示例：
python3 lesson03_visual_walkthrough.py
python3 lesson03_visual_walkthrough.py --output-dir /path/to/output
"""

# %% 0. 环境与通用设置
from argparse import ArgumentParser
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.diagnostic import het_breuschpagan, het_white
from statsmodels.stats.outliers_influence import variance_inflation_factor


def parse_args():
    parser = ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "output_lesson03",
        help="图片和结果表的保存目录",
    )
    return parser.parse_args()


ARGS = parse_args()
OUTPUT_DIR = ARGS.output_dir.resolve()
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams["figure.dpi"] = 120
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["font.sans-serif"] = [
    "Arial Unicode MS",
    "PingFang SC",
    "Microsoft YaHei",
    "DejaVu Sans",
]

COLORS = {
    "orange": "#E76F51",
    "teal": "#2A9D8F",
    "blue": "#457B9D",
    "navy": "#264653",
    "sand": "#E9C46A",
    "lavender": "#8E7DBE",
    "light": "#F6F1E9",
}


def finish_figure(filename: str) -> None:
    path = OUTPUT_DIR / filename
    plt.tight_layout()
    plt.savefig(path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"图形已保存：{path}")


def fit_ols(data, outcome, variables, robust=False):
    model = sm.OLS(data[outcome], sm.add_constant(data[variables])).fit()
    return model.get_robustcov_results(cov_type="HC1") if robust else model


def named_params(result, names):
    """稳健结果对象会返回数组；为图表恢复变量名索引。"""
    return pd.Series(np.asarray(result.params), index=["const", *names])


def named_bse(result, names):
    return pd.Series(np.asarray(result.bse), index=["const", *names])


# %% 1. 实验一：模型形式
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
form_df = pd.DataFrame(
    {
        "ln_wage": ln_wage,
        "wage": np.exp(ln_wage),
        "educ": educ,
        "exper": exper,
        "exper2": exper**2,
        "female": female,
        "urban": urban,
        "educ_female": educ * female,
        "educ_urban": educ * urban,
    }
)

base_vars = ["educ", "exper", "female", "urban"]
quad_vars = ["educ", "exper", "exper2", "female", "urban"]
inter_vars = quad_vars + ["educ_female", "educ_urban"]

m_level_raw = fit_ols(form_df, "wage", base_vars)
m_log_raw = fit_ols(form_df, "ln_wage", base_vars)
m_quad_raw = fit_ols(form_df, "ln_wage", quad_vars)
m_inter_raw = fit_ols(form_df, "ln_wage", inter_vars)

m_level = m_level_raw.get_robustcov_results(cov_type="HC1")
m_log = m_log_raw.get_robustcov_results(cov_type="HC1")
m_quad = m_quad_raw.get_robustcov_results(cov_type="HC1")
m_inter = m_inter_raw.get_robustcov_results(cov_type="HC1")


# %% 2. 图1：水平模型与对数模型
educ_grid = np.linspace(form_df["educ"].min(), form_df["educ"].max(), 150)
typical_exper = form_df["exper"].mean()
predict_base = pd.DataFrame(
    {
        "const": 1.0,
        "educ": educ_grid,
        "exper": typical_exper,
        "female": form_df["female"].mean(),
        "urban": form_df["urban"].mean(),
    }
)
pred_level = m_level_raw.predict(predict_base)
pred_log = m_log_raw.predict(predict_base)

binned = form_df.groupby("educ", as_index=False).agg(wage=("wage", "mean"), ln_wage=("ln_wage", "mean"))
fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
axes[0].scatter(binned["educ"], binned["wage"], color=COLORS["blue"], s=34, alpha=0.75, label="各教育年限的样本均值")
axes[0].plot(educ_grid, pred_level, color=COLORS["orange"], linewidth=2.4, label="水平模型预测")
axes[0].set(title="水平模型：系数表示工资的绝对变化", xlabel="受教育年限", ylabel="工资水平")
axes[0].legend(frameon=False, fontsize=9)

axes[1].scatter(binned["educ"], binned["ln_wage"], color=COLORS["blue"], s=34, alpha=0.75, label="各教育年限的样本均值")
axes[1].plot(educ_grid, pred_log, color=COLORS["teal"], linewidth=2.4, label="对数模型预测")
axes[1].set(title="对数模型：系数近似表示工资的百分比变化", xlabel="受教育年限", ylabel="工资的对数")
axes[1].legend(frameon=False, fontsize=9)
finish_figure("01_level_vs_log.png")


# %% 3. 图2：二次项与转折点
quad_p = named_params(m_quad_raw, quad_vars)
turning_point = -quad_p["exper"] / (2 * quad_p["exper2"])
exper_grid = np.linspace(form_df["exper"].min(), form_df["exper"].max(), 180)
quad_design = pd.DataFrame(
    {
        "const": 1.0,
        "educ": form_df["educ"].mean(),
        "exper": exper_grid,
        "exper2": exper_grid**2,
        "female": form_df["female"].mean(),
        "urban": form_df["urban"].mean(),
    }
)
quad_pred = m_quad_raw.predict(quad_design)

fig, ax = plt.subplots(figsize=(9.5, 5.0))
ax.plot(exper_grid, quad_pred, color=COLORS["teal"], linewidth=2.8)
ax.axvline(turning_point, color=COLORS["orange"], linestyle="--", linewidth=2, label=f"估计转折点：{turning_point:.1f} 年")
ax.fill_betweenx(
    [quad_pred.min() - 0.03, quad_pred.max() + 0.03],
    form_df["exper"].quantile(0.01),
    form_df["exper"].quantile(0.99),
    color=COLORS["sand"],
    alpha=0.14,
    label="样本中间 98% 的经验范围",
)
ax.set(
    title="二次项把“边际回报递减”画成一条曲线",
    xlabel="工作经验（年）",
    ylabel="预测的对数工资",
)
ax.legend(frameon=False)
ax.text(
    0.03,
    0.08,
    "先检查转折点是否落在样本范围内，\n再讨论它有没有经济意义。",
    transform=ax.transAxes,
    bbox={"boxstyle": "round,pad=0.4", "facecolor": COLORS["light"], "edgecolor": "none"},
)
finish_figure("02_quadratic_turning_point.png")


# %% 4. 图3：交互项与四个群体的教育回报
group_specs = [
    ("非城市男性", 0, 0, COLORS["navy"]),
    ("城市男性", 0, 1, COLORS["teal"]),
    ("非城市女性", 1, 0, COLORS["orange"]),
    ("城市女性", 1, 1, COLORS["lavender"]),
]
fig, ax = plt.subplots(figsize=(9.5, 5.3))
group_rows = []
for label, is_female, is_urban, color in group_specs:
    design = pd.DataFrame(
        {
            "const": 1.0,
            "educ": educ_grid,
            "exper": typical_exper,
            "exper2": typical_exper**2,
            "female": is_female,
            "urban": is_urban,
            "educ_female": educ_grid * is_female,
            "educ_urban": educ_grid * is_urban,
        }
    )
    prediction = m_inter_raw.predict(design)
    slope = (
        m_inter_raw.params["educ"]
        + is_female * m_inter_raw.params["educ_female"]
        + is_urban * m_inter_raw.params["educ_urban"]
    )
    group_rows.append({"group": label, "education_slope": slope})
    ax.plot(educ_grid, prediction, color=color, linewidth=2.3, label=f"{label}：{slope:.3f}")

ax.set(
    title="交互项的重点不是一个系数，而是不同群体的斜率",
    xlabel="受教育年限",
    ylabel="预测的对数工资",
)
ax.legend(title="每增加一年教育的估计回报", frameon=False, fontsize=9)
finish_figure("03_interaction_group_slopes.png")


# %% 5. 实验二：模型诊断
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
diag_df = pd.DataFrame(
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

naive_vars = ["educ", "exper", "exper2", "female", "urban", "city_gdp_pc", "city_pop"]
full_vars = naive_vars + ["ability"]
naive_raw = fit_ols(diag_df, "ln_wage", naive_vars)
full_raw = fit_ols(diag_df, "ln_wage", full_vars)
naive_rob = naive_raw.get_robustcov_results(cov_type="HC1")
full_rob = full_raw.get_robustcov_results(cov_type="HC1")

vif_design = sm.add_constant(diag_df[full_vars])
vif = pd.Series(
    [variance_inflation_factor(vif_design.values, i) for i in range(1, vif_design.shape[1])],
    index=full_vars,
)

test_vars = ["educ", "exper", "exper2", "female", "urban", "city_gdp_pc", "ability"]
hetero_raw = fit_ols(diag_df, "ln_wage", test_vars)
hetero_rob = hetero_raw.get_robustcov_results(cov_type="HC1")
bp_stat, bp_pvalue, _, _ = het_breuschpagan(hetero_raw.resid, hetero_raw.model.exog)
white_stat, white_pvalue, _, _ = het_white(hetero_raw.resid, hetero_raw.model.exog)


# %% 6. 图4：把四项诊断结果放在同一张工作台
fig, axes = plt.subplots(2, 2, figsize=(12, 9))

naive_params = named_params(naive_rob, naive_vars)
full_params = named_params(full_rob, full_vars)
naive_bse = named_bse(naive_rob, naive_vars)
full_bse = named_bse(full_rob, full_vars)
diag_coefs = np.array([naive_params["educ"], full_params["educ"]])
diag_se = np.array([naive_bse["educ"], full_bse["educ"]])
axes[0, 0].errorbar(
    diag_coefs,
    [0, 1],
    xerr=1.96 * diag_se,
    fmt="o",
    color=COLORS["teal"],
    ecolor=COLORS["navy"],
    capsize=5,
    linewidth=2,
)
axes[0, 0].axvline(0.08, color=COLORS["orange"], linestyle="--", label="DGP 中教育系数 0.08")
axes[0, 0].set(
    yticks=[0, 1],
    yticklabels=["遗漏 ability", "控制 ability"],
    title="A. 遗漏变量：教育系数发生变化",
    xlabel="教育系数及 95% 置信区间",
)
axes[0, 0].invert_yaxis()
axes[0, 0].legend(frameon=False, fontsize=8)

vif_show = vif[["exper", "exper2", "city_gdp_pc", "city_pop", "educ", "ability"]].sort_values()
bar_colors = [COLORS["blue"] if value < 5 else COLORS["orange"] for value in vif_show]
axes[0, 1].barh(vif_show.index, vif_show.values, color=bar_colors)
axes[0, 1].axvline(5, color="#777777", linestyle="--", linewidth=1)
axes[0, 1].set(title="B. VIF：高值需要结合变量结构解释", xlabel="VIF（5 只是常见经验线，不是删除命令）")
for y_pos, value in enumerate(vif_show.values):
    axes[0, 1].text(value + 0.2, y_pos, f"{value:.1f}", va="center", fontsize=9)

abs_resid = pd.Series(np.abs(hetero_raw.resid))
bins = pd.qcut(diag_df["exper"], q=8, duplicates="drop")
hetero_plot = pd.DataFrame({"exper": diag_df["exper"], "abs_resid": abs_resid, "bin": bins}).groupby("bin", observed=True).agg(exper=("exper", "mean"), abs_resid=("abs_resid", "mean"))
axes[1, 0].scatter(diag_df["exper"], abs_resid, s=12, alpha=0.16, color=COLORS["blue"])
axes[1, 0].plot(hetero_plot["exper"], hetero_plot["abs_resid"], color=COLORS["orange"], marker="o", linewidth=2.4)
axes[1, 0].set(title="C. 异方差：图形与检验需要结合判断", xlabel="工作经验（年）", ylabel="残差绝对值")
axes[1, 0].text(
    0.03,
    0.93,
    f"BP p={bp_pvalue:.4f}；White p={white_pvalue:.4f}",
    transform=axes[1, 0].transAxes,
    va="top",
    bbox={"boxstyle": "round,pad=0.3", "facecolor": COLORS["light"], "edgecolor": "none"},
)

conv_bse = named_bse(hetero_raw, test_vars)
rob_bse = named_bse(hetero_rob, test_vars)
se_vars = ["educ", "exper", "female", "ability"]
se_ratio = rob_bse[se_vars] / conv_bse[se_vars]
axes[1, 1].bar(se_vars, se_ratio, color=[COLORS["teal"], COLORS["blue"], COLORS["sand"], COLORS["lavender"]])
axes[1, 1].axhline(1, color=COLORS["orange"], linestyle="--", linewidth=1.5, label="两种标准误相同")
axes[1, 1].set(title="D. 本次稳健/传统标准误差异不大", ylabel="稳健标准误 ÷ 传统标准误")
axes[1, 1].legend(frameon=False, fontsize=8)
for i, value in enumerate(se_ratio):
    axes[1, 1].text(i, value + 0.02, f"{value:.2f}", ha="center", fontsize=9)

fig.suptitle("模型诊断不是一次性判决，而是发现问题—解释来源—选择处理方式", fontsize=15, y=1.01)
finish_figure("04_model_diagnostics.png")


# %% 7. 保存课堂核对表
form_summary = pd.DataFrame(group_rows)
form_summary.loc[len(form_summary)] = {"group": "quadratic_turning_point", "education_slope": turning_point}
form_summary.to_csv(OUTPUT_DIR / "lesson03_model_form_results.csv", index=False)

diagnostic_summary = pd.DataFrame(
    {
        "item": ["educ_omitting_ability", "educ_controlling_ability", "bp_pvalue", "white_pvalue"],
        "value": [naive_params["educ"], full_params["educ"], bp_pvalue, white_pvalue],
    }
)
diagnostic_summary.to_csv(OUTPUT_DIR / "lesson03_diagnostic_results.csv", index=False)

print("\n模型形式结果：")
print(f"对数模型中 educ 系数：{m_log_raw.params['educ']:.4f}")
print(f"二次项模型的经验转折点：{turning_point:.2f} 年")
print(pd.DataFrame(group_rows).round(4).to_string(index=False))
print("\n模型诊断结果：")
print(f"遗漏 ability 时 educ 系数：{naive_params['educ']:.4f}")
print(f"控制 ability 时 educ 系数：{full_params['educ']:.4f}")
print("重点变量 VIF：", vif_show.round(2).to_dict())
print(f"BP 检验 p 值：{bp_pvalue:.6f}")
print(f"White 检验 p 值：{white_pvalue:.6f}")
