#!/usr/bin/env python3
"""Generate the synthetic student-level dataset for the Lesson 4 Agent Lab.

The public data intentionally contains observed pre-treatment confounders and a
post-treatment mediator. A latent resource factor is used only while generating
the sample and is never written to the student-facing files. This makes the lab
useful for separating regression adjustment from causal identification.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


SEED = 20260922
N = 800
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "materials" / "data" / "ai-score-case"


def build_data() -> pd.DataFrame:
    rng = np.random.default_rng(SEED)

    class_id = rng.integers(1, 21, N)
    class_effect = rng.normal(0, 1.4, 20)
    ability = rng.normal(0, 1, N)
    latent_resources = rng.normal(0, 1, N)
    gender = rng.integers(0, 2, N)

    motivation = np.clip(
        5.5 + 1.15 * ability + 0.55 * latent_resources + rng.normal(0, 1.15, N),
        1,
        10,
    )
    digital_skill = np.clip(
        5.0 + 0.65 * ability + 0.90 * latent_resources + rng.normal(0, 1.20, N),
        1,
        10,
    )
    study_hours = np.clip(
        7 + motivation + 0.55 * ability + rng.normal(0, 2.10, N),
        2,
        28,
    )
    prior_score = np.clip(
        61
        + 8.0 * ability
        + 1.4 * motivation
        + class_effect[class_id - 1]
        + rng.normal(0, 5.0, N),
        35,
        95,
    )

    ai_hours = np.clip(
        -14
        + 0.20 * prior_score
        + 0.48 * motivation
        + 0.60 * digital_skill
        + 0.09 * study_hours
        + 1.25 * latent_resources
        + rng.normal(0, 2.0, N),
        0,
        20,
    )
    assignment_quality = np.clip(
        50
        + 0.22 * prior_score
        + 1.05 * ai_hours
        + 1.05 * motivation
        + 0.75 * latent_resources
        + class_effect[class_id - 1]
        + rng.normal(0, 4.2, N),
        35,
        100,
    )
    final_score = np.clip(
        22
        + 0.34 * prior_score
        + 0.22 * ai_hours
        + 0.20 * assignment_quality
        + 0.95 * motivation
        + 0.12 * study_hours
        + 1.15 * latent_resources
        + class_effect[class_id - 1]
        + rng.normal(0, 4.7, N),
        30,
        100,
    )

    data = pd.DataFrame(
        {
            "student_id": np.arange(1, N + 1),
            "final_score": final_score,
            "ai_hours": ai_hours,
            "prior_score": prior_score,
            "motivation": motivation,
            "digital_skill": digital_skill,
            "study_hours": study_hours,
            "assignment_quality": assignment_quality,
            "gender": gender,
            "class_id": class_id,
        }
    )

    continuous = [
        "final_score",
        "ai_hours",
        "prior_score",
        "motivation",
        "digital_skill",
        "study_hours",
        "assignment_quality",
    ]
    data[continuous] = data[continuous].round(2)
    return data


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    data = build_data()

    data.to_csv(OUTPUT_DIR / "AI_score_case.csv", index=False, encoding="utf-8-sig")
    data.to_stata(
        OUTPUT_DIR / "AI_score_case.dta",
        write_index=False,
        version=118,
        data_label="Lesson 4 Agent Lab: AI use and student outcomes",
        variable_labels={
            "student_id": "匿名学生编号",
            "final_score": "期末成绩（0-100）",
            "ai_hours": "每周生成式AI学习使用小时数",
            "prior_score": "课程开始前基础成绩（0-100）",
            "motivation": "学期开始时学习动机（1-10）",
            "digital_skill": "学期开始时数字工具能力（1-10）",
            "study_hours": "学期开始时每周自主学习小时数",
            "assignment_quality": "学期中作业质量（0-100，处理后变量）",
            "gender": "性别（0=男，1=女）",
            "class_id": "班级编号（1-20）",
        },
        value_labels={"gender": {0: "男", 1: "女"}},
    )

    print(f"Generated {len(data)} observations in {OUTPUT_DIR}")
    print(data.describe().loc[["mean", "std", "min", "max"]].round(2).T)


if __name__ == "__main__":
    main()
