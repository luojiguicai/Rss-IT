#!/usr/bin/env python3
"""Generate README.md from data/entries.json.

Usage:
    python3 scripts/generate-readme.py           # writes README.md
    python3 scripts/generate-readme.py --check   # dry-run, prints stats only
"""

import json
import os
import sys
from datetime import datetime, date

LINK_ICONS = {
    "blog": "🌐",
    "website": "🔗",
    "rss": "📡",
    "x": "𝕏",
    "youtube": "▶️",
    "github": "🐙",
    "zhihu": "💙",
    "juejin": "💎",
    "wechat": "💬",
    "medium": "📝",
    "telegram": "✈️",
    "newsletter": "📬",
    "podcast": "🎙️",
}

LINK_ORDER = [
    "blog", "website", "rss", "x", "youtube", "github",
    "zhihu", "juejin", "wechat", "medium", "telegram",
    "newsletter", "podcast",
]

FIELD_LABELS = {
    "android-official": "Android",
    "android-blog": "Android",
    "android-community": "Android",
    "ai": "AI",
    "general-tech": "通用",
    "tools": "工具",
}


def load_data():
    data_path = os.path.join(os.path.dirname(__file__), "..", "data", "entries.json")
    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)


def render_links_inline(links):
    """Render links as compact inline badges."""
    parts = []
    for key in LINK_ORDER:
        url = links.get(key)
        if url:
            icon = LINK_ICONS.get(key, "🔗")
            parts.append(f"[{icon}]({url})")
    if not parts:
        return ""
    return " " + " ".join(parts)


def render_stars(quality):
    return "⭐" * quality + "☆" * (5 - quality)


def generate(data, check=False):
    categories = data["categories"]
    entries = data["entries"]
    name = data["name"]
    description = data["description"]
    updated = data["updated"]

    # Group entries by category, sort by quality desc
    grouped = {}
    for cat in categories:
        grouped[cat["id"]] = []
    for entry in entries:
        grouped.setdefault(entry["category"], []).append(entry)
    for cat_id in grouped:
        grouped[cat_id].sort(key=lambda e: e.get("quality", 3), reverse=True)

    total_entries = len(entries)
    total_categories = len(categories)

    lines = []
    lines.append(f"# {name}")
    lines.append("")
    lines.append(f"> {description}")
    lines.append(f">")
    lines.append(f"> 📊 **{total_entries}** 个信息源 · **{total_categories}** 个分类 · 更新于 {updated}")
    lines.append("")

    # Quick nav
    lines.append("**快速导航**")
    nav_parts = []
    for cat in categories:
        nav_parts.append(f"[{cat['name']}](#{cat['id'].replace('-', '')})")
    lines.append(" · ".join(nav_parts))
    lines.append("")
    lines.append("---")

    # Recent entries (top 10 by added_date)
    recent = sorted(
        [e for e in entries if e.get("added_date")],
        key=lambda e: e.get("added_date", ""),
        reverse=True,
    )[:10]

    if recent:
        lines.append("")
        lines.append("## 🔥 最近收录")
        lines.append("> 每日自动发现，LLM 评估后收录")
        lines.append("")
        lines.append("| 信息源 | 领域 | 描述 |")
        lines.append("|--------|------|------|")
        for entry in recent:
            link_str = render_links_inline(entry.get("links", {}))
            stars = render_stars(entry.get("quality", 3))
            field = FIELD_LABELS.get(entry["category"], entry["category"])
            added = entry.get("added_date", "")
            name_col = f"**{entry['name']}**{link_str}"
            desc_col = f"{entry['desc']} {stars}"
            lines.append(f"| {name_col} | {field} | {desc_col} |")
        lines.append("")

    # Categories
    for cat in categories:
        cat_entries = grouped.get(cat["id"], [])
        anchor = cat["id"].replace("-", "")
        lines.append("")
        lines.append(f'<a id="{anchor}"></a>')
        lines.append(f"## {cat['name']}")
        lines.append(f"*{cat['desc']}* · {len(cat_entries)} 个源")
        lines.append("")

        lines.append("| 信息源 | 描述 |")
        lines.append("|--------|------|")
        for entry in cat_entries:
            link_str = render_links_inline(entry.get("links", {}))
            stars = render_stars(entry.get("quality", 3))
            name_col = f"**{entry['name']}**{link_str}"
            desc_col = f"{entry['desc']} {stars}"
            lines.append(f"| {name_col} | {desc_col} |")

        # AI category special footer
        if cat["id"] == "ai":
            lines.append("")
            lines.append(
                "> 📌 更多 AI 资源见 "
                "[awesome-ai-field-notes](https://github.com/Gracker/awesome-ai-field-notes)"
                "（608 条，每日更新）"
            )

    # Footer
    lines.append("")
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
    lines.append("### 📡 订阅")
    lines.append("")
    lines.append("- [OPML 文件](data/feeds.opml) — 导入到 RSS 阅读器（Inoreader、Feedly、Follow 等）")
    lines.append(f"- 包含 **67** 个可用 RSS 源")
    lines.append("")
    lines.append("### 自动维护")
    lines.append("")
    lines.append("- 每日发现任务由 [OpenClaw](https://github.com/openclaw/openclaw) 自动执行")
    lines.append("- 扫描 Android Weekly、掘金、GitHub Trending、RSS 列表、Obsidian 产出")
    lines.append("- LLM 评估后自动收录，README + OPML 每日更新")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(f'<p align="center">Licensed under the terms of the <a href="https://github.com/Gracker/awesome-android-ai-dev-sources/blob/main/LICENSE">LICENSE</a> file.</p>')

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
