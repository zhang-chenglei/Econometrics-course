#!/usr/bin/env python3
"""Generate the synthetic firm-level dataset for the Lesson 4 Agent Lab.

The public data contain plausible observed firm characteristics. Two latent
factors are used only while generating the sample and are never written to the
student-facing files. The result is a deliberately strong correlation with weak
causal identification, which keeps the lesson focused on research design.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


SEED = 20260922
N = 800
OUTPUT_DIR = (
    Path(__file__).resolve().parents[1]
    / "materials"
    / "data"
    / "firm-ai-innovation-case"
)


def build_data() -> pd.DataFrame:
    rng = np.random.default_rng(SEED)

    industry = rng.integers(1, 7, N)
    industry_effect = np.array([-2.0, 0.0, 1.5, 3.0, -1.0, 2.0])
    management_quality = rng.normal(0, 1, N)
    market_opportunity = rng.normal(0, 1, N)

    ln_employment = np.clip(
        5.0
        + 0.45 * management_quality
        + 0.10 * industry_effect[industry - 1]
        + rng.normal(0, 0.75, N),
        2.8,
        8.2,
    )
    firm_age = np.clip(rng.gamma(shape=2.4, scale=5.0, size=N) + 2, 2, 45)
    digital_capability = np.clip(
        3.4
        + 0.85 * management_quality
        + 0.32 * ln_employment
        + 0.12 * industry_effect[industry - 1]
        + rng.normal(0, 1.15, N),
        1,
        10,
    )
    prior_innovation = np.clip(
        19
        + 3.8 * management_quality
        + 2.1 * digital_capability
        + 1.4 * ln_employment
        + industry_effect[industry - 1]
        + rng.normal(0, 6.0, N),
        5,
        80,
    )
    rd_intensity = np.clip(
        0.8
        + 0.65 * management_quality
        + 0.11 * prior_innovation
        + rng.normal(0, 1.25, N),
        0.2,
        15,
    )
    export_share = np.clip(
        0.08
        + 0.055 * management_quality
        + 0.018 * digital_capability
        + 0.035 * market_opportunity
        + rng.normal(0, 0.10, N),
        0,
        0.80,
    )
    ai_intensity = np.clip(
        -1.8
        + 0.055 * prior_innovation
        + 0.34 * digital_capability
        + 0.13 * rd_intensity
        + 0.22 * ln_employment
        + 0.72 * management_quality
        + 0.40 * market_opportunity
        + rng.normal(0, 1.25, N),
        0,
        10,
    )
    innovation_score = np.clip(
        10
        + 0.50 * ai_intensity
        + 0.48 * prior_innovation
        + 0.85 * rd_intensity
        + 0.90 * digital_capability
        + 0.60 * ln_employment
        + 4.0 * export_share
        + industry_effect[industry - 1]
        + 2.2 * management_quality
        + 1.5 * market_opportunity
        + rng.normal(0, 5.0, N),
        5,
        100,
    )

    data = pd.DataFrame(
        {
            "firm_id": np.arange(1, N + 1),
            "innovation_score": innovation_score,
            "ai_intensity": ai_intensity,
            "prior_innovation": prior_innovation,
            "rd_intensity": rd_intensity,
            "digital_capability": digital_capability,
            "ln_employment": ln_employment,
            "firm_age": firm_age,
            "export_share": export_share,
            "industry": industry,
        }
    )

    continuous = [
        "innovation_score",
        "ai_intensity",
        "prior_innovation",
        "rd_intensity",
        "digital_capability",
        "ln_employment",
        "firm_age",
        "export_share",
    ]
    data[continuous] = data[continuous].round(2)
    return data


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    data = build_data()

    data.to_csv(
        OUTPUT_DIR / "firm_ai_innovation_case.csv", index=False, encoding="utf-8-sig"
    )
    data.to_stata(
        OUTPUT_DIR / "firm_ai_innovation_case.dta",
        write_index=False,
        version=118,
        data_label="Lesson 4 Agent Lab: firm AI use and innovation",
        variable_labels={
            "firm_id": "匿名企业编号",
            "innovation_score": "企业创新产出得分（0-100）",
            "ai_intensity": "企业AI使用强度（0-10）",
            "prior_innovation": "上一期创新产出得分（0-100）",
            "rd_intensity": "研发支出占营业收入比重（%）",
            "digital_capability": "数字化能力得分（1-10）",
            "ln_employment": "企业员工数的自然对数",
            "firm_age": "企业成立年限",
            "export_share": "出口收入占比（0-1）",
            "industry": "行业编号（1-6）",
        },
    )

    print(f"Generated {len(data)} observations in {OUTPUT_DIR}")
    print(data.describe().loc[["mean", "std", "min", "max"]].round(2).T)


if __name__ == "__main__":
    main()
