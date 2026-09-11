#!/usr/bin/env python3
"""Sync the canonical 中级计量经济学 course sources from EconKB into this Quarto site.

Sources are READ-ONLY and never modified:

    <econkb>/30_教学/01_中级计量经济学（应用经济学硕士）/课程知识库/飞书课程版/
        manifest.json        -- 38 course pages: id / title / parent / source
        state.json           -- course page id -> 飞书 node_token
        textbook_links.json  -- textbook page id -> 飞书 url (+ per-heading block ids)
        lessons/*.md         -- course page bodies
        图片/                 -- course images
    <econkb>/30_教学/09_计量教材/
        拆分章节/*.md         -- 24 textbook page bodies
        图片/{教材插图,小黑,封面图}/ -- textbook images

Generated in this repo:

    index.qmd                 -- from manifest page "root"
    course/<id>.qmd           -- one per remaining manifest page
    textbook/<id>.qmd         -- one per TEXTBOOK_PAGES entry
    assets/images/*.png       -- images referenced by any synced page
    the AUTO-GENERATED block in _quarto.yml (the sidebar)

飞书 links inside the Markdown are rewritten to in-site links, so a reader who
clicks 「教材对应」 stays on the site instead of being sent to 飞书. Links whose
target is not part of this site are unwrapped to plain text.

Usage:
    python3 tools/sync_from_econkb.py --econkb ~/Documents/EconKB
    python3 tools/sync_from_econkb.py --econkb ~/Documents/EconKB --check
"""

from __future__ import annotations

import argparse
import json
import posixpath
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from PIL import Image


COURSE_REL = Path("30_教学/01_中级计量经济学（应用经济学硕士）/课程知识库/飞书课程版")
TEXTBOOK_REL = Path("30_教学/09_计量教材")

# Textbook pages, in site order. Derived from textbook_links.json ids, but the
# order there is arbitrary, so it is pinned here.
TEXTBOOK_PAGES: list[tuple[str, str]] = [
    ("guide", "0_导读与使用说明.md"),
    ("intro", "00_导论.md"),
    ("part1", "00a_第一部分_回归分析基础.md"),
    ("ch01", "01_第1章_一元线性回归.md"),
    ("ch02", "02_第2章_多元线性回归_估计.md"),
    ("ch03", "03_第3章_多元线性回归_推断.md"),
    ("ch04", "04_第4章_模型形式扩展.md"),
    ("ch05", "05_第5章_模型设定与诊断.md"),
    ("part2", "05a_第二部分_从基础回归到复杂现实.md"),
    ("ch06", "06_第6章_离散选择模型.md"),
    ("ch07", "07_第7章_面板数据模型.md"),
    ("ch08", "08_第8章_工具变量模型.md"),
    ("ch09", "09_第9章_因果推断前沿方法.md"),
    ("ch10", "10_第10章_大数据与非经典计量.md"),
    ("part3", "10a_第三部分_从方法到实证项目.md"),
    ("ch11", "11_第11章_研究问题与识别策略.md"),
    ("ch12", "12_第12章_数据准备与变量构建.md"),
    ("ch13", "13_第13章_模型估计与结果检验.md"),
    ("ch14", "14_第14章_研究成果的呈现.md"),
    ("references", "15_参考文献.md"),
    ("appendix_math", "附录1_数学基础.md"),
    ("appendix_stata", "附录2_Stata入门.md"),
    ("appendix_python", "附录3_Python入门.md"),
    ("ending", "结束语.md"),
]

# Textbook pages reference images Obsidian-style: ![[ch01-fig1.png]]
# Pages written by hand in this repo (not part of the 飞书 manifest) that belong
# in the sidebar. Pinned here so the generated sidebar does not drop them.
#
# Repository-only resource pages. They are not Feishu pages, so the generator
# keeps them in the sidebar and llms.txt without trying to overwrite the files.
EXTRA_RESOURCE_PAGES: list[tuple[str, str]] = [
    ("course/materials.qmd", "代码与数据｜下载与复现"),
]

# The Feishu source serves one specific graduate class, while this GitHub site
# is a public learning resource for several cohorts.  Keep the source material
# authoritative, then apply a small, explicit public-site layer during sync.
# This prevents class-specific grading rules from reappearing on GitHub after a
# future Feishu refresh.
PUBLIC_SITE_TITLE = "计量经济学：理论与实践"
PUBLIC_PAGE_TITLES = {
    "root": f"{PUBLIC_SITE_TITLE}｜课程主页",
    "syllabus": "学习大纲｜内容与进度",
}

PUBLIC_HOME_RESOURCES = r"""

## 推荐资料与链接

> 不必从头到尾读完所有材料。遇到概念、方法、代码或复现问题时，按需要选择一项继续深入即可。

::: {.resource-grid}
::: {.resource-card}
### 教材与方法

- [Wooldridge, *Introductory Econometrics: A Modern Approach*](https://www.cengage.com/c/student/9780357900161/?filterBy=Student)：体系完整，适合查阅多元回归、面板数据、工具变量等基础与应用方法。
- [Stock & Watson, *Introduction to Econometrics*](https://www.pearson.com/en-us/subject-catalog/p/introduction-to-econometrics/P200000005880/9780136879787)：重视经济问题、数据和结果解释，适合巩固实证分析思维。
- [Angrist & Pischke, *Mastering ’Metrics*](https://press.princeton.edu/books/paperback/9780691152844/mastering-metrics)：通过研究故事理解识别策略，适合进入因果推断时阅读。
- [Causal Inference: The Mixtape](https://mixtape.scunning.com/)与[The Effect](https://theeffectbook.net/)：两本可在线阅读的开放教材，适合按方法查找案例、图形和进一步解释。
:::

::: {.resource-card}
### AI辅助学习与编程

- [AI Agent辅助学习指南](course/agent_learning_guide.qmd)：从指定课程材料、提问、核验到自测，建立不依赖“直接要答案”的学习方式。
- [Vibe Research实操手册](course/vibe_research_guide.qmd)：用Agent管理论文阅读、代码运行、结果检查和项目文件。
- [Claude Code官方文档](https://code.claude.com/docs/en/overview)与[OpenAI Codex官方文档](https://developers.openai.com/codex/)：了解如何让编码Agent读取项目、执行任务并保留可检查的修改记录。
- [Quarto Guide](https://quarto.org/docs/guide/)：把Markdown、代码、图表和解释整理成可复现网页或报告。
:::

::: {.resource-card}
### 论文、数据与复现

- [本站代码与教学数据](course/materials.qmd)：教材案例、Stata与Python代码、AI任务卡和匿名教学数据的统一入口。
- [《中国工业经济》](https://ciejournal.ajcass.com/)：可从实证论文及其附件中寻找数据、代码和复现材料。
- [《数量经济技术经济研究》](https://www.jqte.net/sljjjsjjyj/ch/index.aspx)：可关注“下载全文及数据”和开放科学实验室中的复现资源。
- 阅读复现包时，先理解研究问题、样本和变量，再运行代码；不要只追求把结果数字跑得一模一样。
:::
:::
"""

WIKI_IMAGE_RE = re.compile(r"!\[\[([^\]]+)\]\]")

# Course pages reference images with ordinary Markdown, relative to the course
# 图片/ folder (written both as "图片/x.png" and "../图片/x.png" in the sources).
# The sub-path is preserved on the site: course 图片/xiaohei/a.png and textbook
# 小黑/a.png are different files with the same basename.
COURSE_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(((?:\.\./)?图片/([^)\s]+))\)")

FEISHU_LINK_RE = re.compile(
    r"\[([^\]]+)\]\((https://[^/\s)]+/wiki/([A-Za-z0-9]+)(?:#[A-Za-z0-9]+)?)\)"
)


def replace_once(text: str, old: str, new: str, page_id: str) -> str:
    """Replace one class-specific passage, failing loudly if the source drifts."""
    count = text.count(old)
    if count != 1:
        raise ValueError(
            f"Public-site override for {page_id!r} expected one match, found {count}: {old[:60]!r}"
        )
    return text.replace(old, new, 1)


def publicize_course_body(page_id: str, text: str) -> str:
    """Adapt class-specific Feishu copy for the public, multi-cohort website."""
    if page_id == "root":
        text = replace_once(
            text,
            "# 中级计量经济学｜课程主页",
            f"# {PUBLIC_SITE_TITLE}",
            page_id,
        )
        text = replace_once(
            text,
            "> 本课程面向应用经济学研究生。飞书按实际授课进程组织，正式教材按知识体系组织，两者通过“教材章节与课程讲次对照”相互连接。",
            "> 本网站面向具备一定统计学和多元回归分析基础的高年级本科生与研究生。15讲学习路径按学习过程组织，正式教材按知识体系组织，两者通过“教材章节与课程讲次对照”相互连接。",
            page_id,
        )
        text = replace_once(
            text,
            "本课程面向已经学习过初级计量经济学的应用经济学研究生。我们不会从一元回归开始逐章重讲，而是用两讲恢复回归基础，再以“内生性与因果推断”为分水岭，进入面板数据、工具变量、准实验方法和前沿模型，最后由每位学生完成一项个人实证项目。",
            "本网站面向具备一定统计学和多元回归分析基础的高年级本科生与研究生。学习路径用两讲恢复回归基础，再以“内生性与因果推断”为分水岭，进入面板数据、工具变量、准实验方法和前沿模型，最后引导学习者完成一项实证项目。",
            page_id,
        )
        text = replace_once(
            text,
            "课程结束时，每位学生应当能够独立提交：",
            "完成学习后，学习者应当能够独立形成：",
            page_id,
        )
        text += PUBLIC_HOME_RESOURCES

    elif page_id == "syllabus":
        text = replace_once(text, "# 课程大纲｜要求与考核", "# 学习大纲｜内容与进度", page_id)
        text = replace_once(
            text,
            "> 本页是《中级计量经济学》的课程契约：这门课学什么、怎么上、怎么考。请第一次课仔细阅读，并留存备查。",
            "> 本页说明这套课程资源学什么、如何组织以及怎样结合教材、代码和AI Agent开展学习。",
            page_id,
        )
        text = replace_once(
            text,
            "- 课程性质：应用经济学研究生专业课，兼具理论性、应用性与实践性",
            "- 课程性质：面向高年级本科生与研究生的开放课程，兼具理论性、应用性与实践性",
            page_id,
        )
        text = replace_once(
            text,
            "- 授课对象：应用经济学研究生，已学习统计学、初级计量经济学和线性回归",
            "- 学习对象：高年级本科生与研究生，具备一定的统计学和多元回归分析基础",
            page_id,
        )
        text = replace_once(
            text,
            "- 每位学生一学期完成一次10分钟课堂汇报，围绕个人项目说明“研究什么、使用什么数据和方法、得到什么阶段结果或遇到什么问题”。PPT页数不作统一限制，但应服务于清晰表达。\n",
            "",
            page_id,
        )
        text, count = re.subn(
            r"\n## 六、考核方式\n.*?(?=\n## 七、诚信与 AI 使用\n)",
            "\n",
            text,
            count=1,
            flags=re.DOTALL,
        )
        if count != 1:
            raise ValueError("Could not remove the public-site assessment section from syllabus")
        text = replace_once(text, "## 七、诚信与 AI 使用", "## 六、诚信与 AI 使用", page_id)
        text = replace_once(text, "- 期末闭卷考试不得使用人工智能工具。\n", "", page_id)
        text = replace_once(
            text,
            "- AI 使用应遵守本课程大纲、课前必读材料和各讲任务中的规范，并保留必要的使用与人工核验记录。",
            "- AI 使用应遵守学术规范、课前必读材料和各讲任务中的要求，并保留必要的使用与人工核验记录。",
            page_id,
        )

    elif page_id == "intro":
        replacement = """**4. 实证项目与成果表达**

学习者可以围绕一个真实经济问题完成小型实证项目，把研究问题、数据、方法、结果和结论串成一条可检查的证据链：

- 项目可以个人完成，也可以在学习小组中协作推进；
- 阶段性分享可围绕研究设计、数据方法、初步结果或实际困难展开；
- 重点不在PPT页数或显著性星号，而在于能否清楚说明问题、证据和结论边界。
"""
        text, count = re.subn(
            r"\*\*4\. 个人项目、课堂汇报和考核\*\*\n.*?(?=\n\*\*5\. 关于 AI 的四个共同约定\*\*)",
            replacement,
            text,
            count=1,
            flags=re.DOTALL,
        )
        if count != 1:
            raise ValueError("Could not replace the public-site project section in lesson 1")
        text = replace_once(
            text,
            "4. 项目中可以全面使用 AI，期末考试则独立证明自己具备监督和核验 AI 的基础能力。",
            "4. 可以全面使用 AI 提高效率，但应通过独立复述、手算或重新运行代码检验自己是否真正理解。",
            page_id,
        )
        text = replace_once(
            text,
            "- 了解课程的教材主线、课堂节奏、个人项目、考核方式和 AI 使用规则。",
            "- 了解课程的教材主线、学习节奏、实证项目和 AI 使用规则。",
            page_id,
        )

    elif page_id == "agent_learning_guide":
        text = replace_once(
            text,
            "个人项目占课程很大比重：正文约 3000—5000 字，另附数据说明、主要代码或操作记录、AI 使用说明。项目分三个阶段，Agent 的角色各不相同。",
            "完整实证项目能够把分散的方法知识连接起来。建议同时保留数据说明、主要代码或操作记录与AI使用说明。项目可以分成三个阶段，Agent在各阶段扮演不同角色。",
            page_id,
        )
        replacement = """### 5. 完成本讲自测与综合复习

**本讲验收**的作用是自查。把验收页的要求交给 Agent，让它出题：

> 这是第 X 讲的验收要求。请据此出 6 道题，其中 2 道考查常见误解，
> 先只给题目，等我作答后再逐题讲评，并指出每道题对应本讲哪一部分。

应定期脱离Agent完成自测：先让Agent出题和讲评，再关掉Agent独立作答，最后回到教材修正仍然说不清的地方。**“看AI讲一遍觉得会了”和“自己能解释、能判断、能运行”，是两种不同的学习状态。**
"""
        text, count = re.subn(
            r"### 5\. 准备本讲验收与期末\n.*?(?=\n---\n\n## 五、提示词模板库)",
            replacement,
            text,
            count=1,
            flags=re.DOTALL,
        )
        if count != 1:
            raise ValueError("Could not replace assessment-specific advice in Agent guide")
        principles = """### 1. 公共学习材料的使用原则

个人项目中可以合理使用AI辅助选题、代码检查和文字修改，但必须说明使用方式，核验数据、文献、代码和结论，并对最终成果负责。建议保留必要的使用与人工核验记录，使研究过程可以追溯和复核。
"""
        text, count = re.subn(
            r"### 1\. 课程是怎么规定的\n.*?(?=\n### 2\. 什么算合理使用，什么算代做)",
            principles,
            text,
            count=1,
            flags=re.DOTALL,
        )
        if count != 1:
            raise ValueError("Could not generalize AI-use rules in Agent guide")
        text = replace_once(
            text,
            "| 让 Agent 在期末闭卷考试中提供帮助 | 严禁 |",
            "| 在明确要求独立完成的任务中调用 Agent | 严禁 |",
            page_id,
        )
        text, count = re.subn(
            r"\n### 5\. 期末考试\n.*?(?=\n---\n\n## 八、进一步阅读)",
            "\n",
            text,
            count=1,
            flags=re.DOTALL,
        )
        if count != 1:
            raise ValueError("Could not remove the final exam section from Agent guide")

    elif page_id == "ch13":
        text = replace_once(
            text,
            "提交一页模型比较、可运行代码和AI协作记录。该专题可纳入平时成绩，但不占正式课堂讲次。",
            "形成一页模型比较、可运行代码和AI协作记录。该专题适合作为自主拓展，不占正式课堂讲次。",
            page_id,
        )

    # Course pages use the public site name; textbook pages are not passed here.
    return text.replace("中级计量经济学", PUBLIC_SITE_TITLE)

SIDEBAR_BEGIN = "      # >>> AUTO-GENERATED by tools/sync_from_econkb.py -- do not edit by hand >>>"
SIDEBAR_END = "      # <<< AUTO-GENERATED <<<"

# The EconKB sources are print-resolution PNGs (mostly 2688x1536, ~6 MB each)
# because the same files feed the PDF build. A website needs neither that size
# nor that format: copying them verbatim puts ~255 MB into the repository and
# makes every push crawl. So raster images are downscaled and re-encoded here.
# The EconKB originals are never touched.
IMAGE_MAX_WIDTH = 1600
IMAGE_QUALITY = 90
RASTER_EXT_RE = re.compile(r"\.(png|jpe?g)$", re.IGNORECASE)


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def build_feishu_map(course_dir: Path) -> dict[str, str]:
    """Map every 飞书 wiki token that has an in-site counterpart to its page."""
    mapping: dict[str, str] = {}

    state = load_json(course_dir / "state.json")
    for page_id, entry in state.get("pages", {}).items():
        target = "index.qmd" if page_id == "root" else f"course/{page_id}.qmd"
        for key in ("node_token", "obj_token"):
            token = entry.get(key)
            if token:
                mapping[token] = target

    links = load_json(course_dir / "textbook_links.json")
    for page_id, entry in links.get("pages", {}).items():
        match = re.search(r"/wiki/([A-Za-z0-9]+)", entry.get("url", ""))
        if match:
            mapping[match.group(1)] = f"textbook/{page_id}.qmd"

    return mapping


def relative_to(from_dir: str, target: str) -> str:
    """Path to `target` as seen from `from_dir` (both site-root-relative POSIX)."""
    from_posix = from_dir if from_dir else "."
    return posixpath.relpath(target, from_posix)


def web_name(name: str) -> str:
    """Site path for an image: rasters become .webp, anything else is unchanged."""
    return RASTER_EXT_RE.sub(".webp", name)


def write_image(source: Path, destination: Path) -> None:
    """Write one site image, downscaling and re-encoding rasters to WebP."""
    if not RASTER_EXT_RE.search(source.name):
        shutil.copy2(source, destination)  # vector, or already a web format
        return

    with Image.open(source) as image:
        width = image.width
    command = ["cwebp", "-q", str(IMAGE_QUALITY), "-quiet"]
    if width > IMAGE_MAX_WIDTH:
        command += ["-resize", str(IMAGE_MAX_WIDTH), "0"]
    command += [str(source), "-o", str(destination)]
    try:
        subprocess.run(command, check=True)
    except FileNotFoundError:
        raise SystemExit(
            "cwebp not found. Install it (`brew install webp`) or lower the "
            "image handling in write_image()."
        )


def rewrite_body(text: str, feishu_map: dict[str, str], from_dir: str) -> str:
    """Rewrite 飞书 links and wiki-style images into in-site equivalents."""

    def link_repl(match: re.Match[str]) -> str:
        label, _url, token = match.group(1), match.group(2), match.group(3)
        target = feishu_map.get(token)
        if target is None:
            # Not part of this site (e.g. 飞书-only material): keep the text only.
            return label
        return f"[{label}]({relative_to(from_dir, target)})"

    text = FEISHU_LINK_RE.sub(link_repl, text)

    def course_image_repl(match: re.Match[str]) -> str:
        alt, sub_path = match.group(1), match.group(3)
        target = f"{relative_to(from_dir, 'assets/images')}/{web_name(sub_path)}"
        return f"![{alt}]({target})"

    text = COURSE_IMAGE_RE.sub(course_image_repl, text)

    def image_repl(match: re.Match[str]) -> str:
        target = f"{relative_to(from_dir, 'assets/images')}/{web_name(match.group(1))}"
        return f"![]({target})"

    return WIKI_IMAGE_RE.sub(image_repl, text)


def render_page(
    text: str,
    title: str,
    feishu_map: dict[str, str],
    from_dir: str,
    is_home: bool = False,
) -> str:
    """Build a Quarto page with a human-readable browser-tab title.

    ``pagetitle`` changes only the HTML ``<title>`` metadata.  The visible H1
    remains the one maintained in EconKB, so synced pages do not gain a
    duplicate title block.
    """
    heading = re.search(r"^#\s+(.+?)\s*$", text, flags=re.MULTILINE)
    page_title = heading.group(1) if heading else title
    metadata = json.dumps(page_title, ensure_ascii=False)
    body = rewrite_body(text, feishu_map, from_dir)
    body_class = "body-classes: course-home\n" if is_home else ""
    return f"---\npagetitle: {metadata}\n{body_class}---\n\n{body}"


def collect_images(
    course_bodies: list[str],
    textbook_bodies: list[str],
    course_image_root: Path,
    textbook_image_roots: list[Path],
) -> dict[str, Path]:
    """Resolve every image referenced by a synced page.

    Returns a mapping of output path (relative to assets/images/) to source file.
    """
    result: dict[str, Path] = {}
    missing: list[str] = []

    # Textbook: ![[name]] -> assets/images/<name>, looked up across the textbook roots.
    available: dict[str, Path] = {}
    for root in textbook_image_roots:
        if root.is_dir():
            for path in root.rglob("*"):
                if path.is_file():
                    available.setdefault(path.name, path)
    for text in textbook_bodies:
        for name in WIKI_IMAGE_RE.findall(text):
            if name in result:
                continue
            source = available.get(name)
            if source is None:
                missing.append(f"textbook: {name}")
            else:
                result[name] = source

    # Course: ![](图片/<sub>) -> assets/images/<sub>, keeping the sub-path.
    for text in course_bodies:
        for _alt, _raw, sub_path in COURSE_IMAGE_RE.findall(text):
            if sub_path in result:
                continue
            source = course_image_root / sub_path
            if not source.is_file():
                missing.append(f"course: 图片/{sub_path}")
            else:
                result[sub_path] = source

    if missing:
        raise FileNotFoundError(
            "Images referenced by synced pages were not found:\n  "
            + "\n  ".join(sorted(set(missing)))
        )
    return result


def sidebar_yaml(manifest: dict[str, Any]) -> list[str]:
    """Render the site sidebar from the manifest's page tree."""
    pages = manifest["pages"]
    children: dict[str | None, list[dict[str, Any]]] = {}
    for page in pages:
        children.setdefault(page.get("parent"), []).append(page)

    def href_for(page_id: str) -> str:
        return "index.qmd" if page_id == "root" else f"course/{page_id}.qmd"

    def quote(value: str) -> str:
        return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'

    def display_title(node: dict[str, Any]) -> str:
        return PUBLIC_PAGE_TITLES.get(node["id"], node["title"])

    lines: list[str] = []

    def emit(nodes: list[dict[str, Any]], indent: int) -> None:
        pad = " " * indent
        for node in nodes:
            kids = children.get(node["id"], [])
            nested_extra = textbook_entries() if node["id"] == "textbook" else []
            if not kids and not nested_extra:
                lines.append(f"{pad}- href: {href_for(node['id'])}")
                lines.append(f"{pad}  text: {quote(display_title(node))}")
                continue
            lines.append(f"{pad}- section: {quote(display_title(node))}")
            lines.append(f"{pad}  href: {href_for(node['id'])}")
            lines.append(f"{pad}  contents:")
            # Textbook chapters go directly under 「教材全文」, as siblings of the
            # manifest's own children there (50.4｜附录、50.5｜对照). Wrapping them in
            # a nested `教材正文` section pushed every chapter to level 3, where the
            # default collapse-level of 2 hides the whole textbook behind a click.
            for title, target in nested_extra:
                lines.append(f"{pad}    - href: {target}")
                lines.append(f"{pad}      text: {quote(title)}")
            emit(kids, indent + 4)
            if node["id"] == "resources":
                child_pad = " " * (indent + 4)
                for href, text in EXTRA_RESOURCE_PAGES:
                    lines.append(f"{child_pad}- href: {href}")
                    lines.append(f"{child_pad}  text: {quote(text)}")

    def textbook_entries() -> list[tuple[str, str]]:
        titles = load_json(course_dir / "textbook_links.json")["pages"]
        return [
            (titles[page_id]["title"], f"textbook/{page_id}.qmd")
            for page_id, _filename in TEXTBOOK_PAGES
            if page_id in titles
        ]

    # Top level: manifest root's children, preceded by the homepage itself.
    root = next(page for page in pages if page["id"] == "root")
    lines.append("- href: index.qmd")
    lines.append(f"  text: {quote(display_title(root))}")
    emit(children.get("root", []), 0)
    return lines


def splice_sidebar(quartoTemplate: Path, block: str) -> bool:
    """Replace the AUTO-GENERATED sidebar block. Returns True if anything changed."""
    text = quartoTemplate.read_text(encoding="utf-8")
    begin = text.find(SIDEBAR_BEGIN)
    end = text.find(SIDEBAR_END)
    if begin == -1 or end == -1:
        raise SystemExit(
            f"{quartoTemplate} is missing the AUTO-GENERATED markers; "
            "see SIDEBAR_BEGIN / SIDEBAR_END in this script."
        )
    end += len(SIDEBAR_END)
    updated = f"{text[:begin]}{SIDEBAR_BEGIN}\n{block}\n{SIDEBAR_END}{text[end:]}"
    if updated == text:
        return False
    quartoTemplate.write_text(updated, encoding="utf-8")
    return True


def write_llms_txt(repo: Path, manifest: dict[str, Any], course_dir: Path) -> None:
    """Regenerate llms.txt so agents can index every page on the site."""
    site = "https://zhang-chenglei.github.io/Econometrics-course"
    textbook_titles = load_json(course_dir / "textbook_links.json")["pages"]

    lines = [
        f"# {PUBLIC_SITE_TITLE}",
        "",
        "> 面向具备一定统计学和多元回归分析基础的高年级本科生与研究生：15讲学习路径、完整教材、代码、数据与AI协作指南。",
        "",
        "## 课程",
        "",
    ]
    for page in manifest["pages"]:
        target = "index.html" if page["id"] == "root" else f"course/{page['id']}.html"
        title = PUBLIC_PAGE_TITLES.get(page["id"], page["title"])
        lines.append(f"- [{title}]({site}/{target})")

    for href, title in EXTRA_RESOURCE_PAGES:
        target = href.removesuffix(".qmd") + ".html"
        lines.append(f"- [{title}]({site}/{target})")

    lines += ["", "## 教材", ""]
    for page_id, _filename in TEXTBOOK_PAGES:
        entry = textbook_titles.get(page_id)
        if entry:
            lines.append(f"- [{entry['title']}]({site}/textbook/{page_id}.html)")

    lines.append("")
    lines += [
        "## 机器可读材料",
        "",
        f"- [代码与数据说明]({site}/materials/README.md)",
        f"- [Python与Stata代码目录](https://github.com/zhang-chenglei/Econometrics-course/tree/main/materials/code)",
        f"- [教学数据目录](https://github.com/zhang-chenglei/Econometrics-course/tree/main/materials/data)",
        "",
    ]
    (repo / "llms.txt").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--econkb", type=Path, required=True, help="Path to the EconKB checkout")
    parser.add_argument("--check", action="store_true", help="Report drift without writing")
    args = parser.parse_args()

    global course_dir
    repo = Path(__file__).resolve().parents[1]
    course_dir = args.econkb / COURSE_REL
    textbook_dir = args.econkb / TEXTBOOK_REL

    manifest = load_json(course_dir / "manifest.json")
    feishu_map = build_feishu_map(course_dir)

    # Read every source page up front, so image collection sees the real bodies.
    course_bodies: list[tuple[str, str, str, str]] = []  # (page_id, title, body, target)
    for page in manifest["pages"]:
        source = course_dir / page["source"]
        target = "index.qmd" if page["id"] == "root" else f"course/{page['id']}.qmd"
        body = publicize_course_body(
            page["id"], source.read_text(encoding="utf-8")
        )
        course_bodies.append(
            (page["id"], PUBLIC_PAGE_TITLES.get(page["id"], page["title"]), body, target)
        )

    textbook_titles = load_json(course_dir / "textbook_links.json")["pages"]
    textbook_bodies: list[tuple[str, str, str, str]] = []
    for page_id, filename in TEXTBOOK_PAGES:
        source = textbook_dir / "拆分章节" / filename
        textbook_bodies.append(
            (
                page_id,
                textbook_titles[page_id]["title"],
                source.read_text(encoding="utf-8"),
                f"textbook/{page_id}.qmd",
            )
        )

    images = collect_images(
        [body for _, _, body, _ in course_bodies],
        [body for _, _, body, _ in textbook_bodies],
        course_dir / "图片",
        [textbook_dir / "图片"],
    )

    if args.check:
        problems = []
        for page_id, title, body, target in course_bodies + textbook_bodies:
            from_dir = posixpath.dirname(target)
            expected = render_page(
                body,
                title,
                feishu_map,
                from_dir,
                is_home=page_id == "root" and target == "index.qmd",
            )
            path = repo / target
            if not path.exists() or path.read_text(encoding="utf-8") != expected:
                problems.append(target)
        if problems:
            print(f"{len(problems)} page(s) out of date: " + ", ".join(problems))
            sys.exit(1)
        print("All pages up to date.")
        return

    # 1. Write the pages.
    written: set[str] = set()
    for page_id, title, body, target in course_bodies + textbook_bodies:
        from_dir = posixpath.dirname(target)
        path = repo / target
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            render_page(
                body,
                title,
                feishu_map,
                from_dir,
                is_home=page_id == "root" and target == "index.qmd",
            ),
            encoding="utf-8",
        )
        written.add(target)
    written.update(href for href, _title in EXTRA_RESOURCE_PAGES)

    # 2. Write the images (downscaled + re-encoded, see write_image).
    image_dir = repo / "assets/images"
    image_dir.mkdir(parents=True, exist_ok=True)
    expected_images = {web_name(name) for name in images}
    for target_rel, source in images.items():
        destination = image_dir / web_name(target_rel)
        destination.parent.mkdir(parents=True, exist_ok=True)
        write_image(source, destination)

    # 3. Regenerate the sidebar.
    block = "\n".join(
        "      " + line if line.strip() else "" for line in sidebar_yaml(manifest)
    )
    changed = splice_sidebar(repo / "_quarto.yml", block)

    # 4. Regenerate llms.txt.
    write_llms_txt(repo, manifest, course_dir)

    # 5. Report orphans rather than deleting anything.
    orphans = [
        path.relative_to(repo).as_posix()
        for folder in ("course", "textbook")
        for path in sorted((repo / folder).glob("*.qmd"))
        if path.relative_to(repo).as_posix() not in written
    ]

    stale_images = [
        path.relative_to(repo).as_posix()
        for path in sorted(image_dir.rglob("*"))
        if path.is_file() and path.relative_to(image_dir).as_posix() not in expected_images
    ]

    print(f"Pages written : {len(course_bodies)} course + {len(textbook_bodies)} textbook")
    print(f"Images written: {len(images)}")
    print(f"Sidebar       : {'updated' if changed else 'unchanged'}")
    if orphans:
        print("Orphan pages (not removed, no longer in the manifest):")
        for orphan in orphans:
            print(f"  {orphan}")
    if stale_images:
        print("Stale images (not removed — e.g. the pre-WebP PNGs):")
        for stale in stale_images:
            print(f"  {stale}")


if __name__ == "__main__":
    main()
