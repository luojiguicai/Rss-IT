#!/usr/bin/env python3
"""Generate README.md from data/entries.json.

Usage:
    python3 scripts/generate-readme.py           # writes README.md
    python3 scripts/generate-readme.py --check   # dry-run, prints stats only
"""

import json
import os
import sys

LINK_LABELS = {
    "blog": "Blog",
    "rss": "RSS",
    "x": "X",
    "youtube": "YouTube",
    "github": "GitHub",
    "zhihu": "知乎",
    "juejin": "掘金",
    "wechat": "微信",
    "medium": "Medium",
    "telegram": "Telegram",
    "newsletter": "Newsletter",
    "podcast": "Podcast",
    "website": "Website",
}

LINK_ORDER = [
    "blog", "website", "rss", "x", "youtube", "github",
    "zhihu", "juejin", "wechat", "medium", "telegram",
    "newsletter", "podcast",
]


def load_data():
    data_path = os.path.join(os.path.dirname(__file__), "..", "data", "entries.json")
    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)


def render_links(links):
    """Render link badges for an entry."""
    parts = []
    for key in LINK_ORDER:
        url = links.get(key)
        if url:
            label = LINK_LABELS.get(key, key)
            parts.append(f"[{label}]({url})")
    return " ".join(parts)


def render_stars(quality):
    return "⭐" * quality + "☆" * (5 - quality)


def generate(data, check=False):
    categories = data["categories"]
    entries = data["entries"]
    name = data["name"]
    description = data["description"]
    updated = data["updated"]

    # Group entries by category
    grouped = {}
    for cat in categories:
        grouped[cat["id"]] = []
    for entry in entries:
        grouped.setdefault(entry["category"], []).append(entry)

    total_entries = len(entries)
    total_categories = len(categories)

    lines = []
    lines.append(f"# {name}")
    lines.append("")
    lines.append(f"> {description}")
    lines.append(f">")
    lines.append(f"> 📊 **{total_entries}** 个信息源 · **{total_categories}** 个分类 · 更新于 {updated}")
    lines.append("")
    lines.append("---")
    lines.append("")

    for cat in categories:
        cat_entries = grouped.get(cat["id"], [])
        lines.append(f"## {cat['name']}")
        lines.append(f"*{cat['desc']}* · {len(cat_entries)} 个源")
        lines.append("")

        for entry in cat_entries:
            link_str = render_links(entry.get("links", {}))
            stars = render_stars(entry.get("quality", 3))
            lines.append(f"- **{entry['name']}** — {entry['desc']} {stars}")
            if link_str:
                lines.append(f"  <div align='right'>{link_str}</div>")

        # AI category special footer
        if cat["id"] == "ai":
            lines.append("")
            lines.append(
                "> 📌 更多 AI 资源见 "
                "[awesome-ai-field-notes](https://github.com/Gracker/awesome-ai-field-notes)"
                "（608 条，每日更新）"
            )

        lines.append("")

    # Footer
    lines.append("---")
    lines.append("")
    lines.append("## 📋 贡献指南")
    lines.append("")
    lines.append("1. Fork 本仓库")
    lines.append("2. 编辑 `data/entries.json`，按 schema 添加新条目")
    lines.append("3. 运行 `python3 scripts/generate-readme.py` 重新生成 README")
    lines.append("4. 运行 `python3 scripts/check-links.py` 验证链接")
    lines.append("5. 提交 PR")
    lines.append("")
    lines.append("### 数据格式")
    lines.append("")
    lines.append("每个条目包含 `id`、`name`、`category`、`author`、`desc`、`links`（optional）、`tags`、`quality`（1-5）。")
    lines.append("links 中只填真实存在的链接，不要留空值。")
    lines.append("")
    lines.append("### 自动维护")
    lines.append("")
    lines.append("- `scripts/check-links.py` — 检查所有链接可用性")
    lines.append("- 每日发现任务由 [OpenClaw](https://github.com/openclaw/openclaw) 自动执行，扫描 Android Weekly、RSS 列表、Obsidian 产出，LLM 评估后写入 `data/candidates.json`")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(f"<p align='center'>Licensed under the terms of the <a href='https://github.com/Gracker/Dev-Radar/blob/main/LICENSE'>LICENSE</a> file.</p>")

    readme = "\n".join(lines) + "\n"

    if check:
        print(f"README would contain {len(readme)} chars, {total_entries} entries, {total_categories} categories")
        return readme

    readme_path = os.path.join(os.path.dirname(__file__), "..", "README.md")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme)
    print(f"README.md generated ({len(readme)} chars, {total_entries} entries, {total_categories} categories)")
    return readme


if __name__ == "__main__":
    data = load_data()
    check = "--check" in sys.argv
    generate(data, check=check)
