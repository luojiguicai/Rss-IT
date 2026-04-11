#!/usr/bin/env python3
"""Integrate follow.opml into entries.json and generate feeds.opml."""

import json
import os
import re
import xml.etree.ElementTree as ET
from urllib.parse import urlparse
from collections import OrderedDict

OPML_PATH = "/Users/gracker/Library/Mobile Documents/iCloud~md~obsidian/Documents/Obsidian/follow.opml"
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
ENTRIES_PATH = os.path.join(DATA_DIR, "entries.json")
OPML_OUT_PATH = os.path.join(DATA_DIR, "feeds.opml")

def load_entries():
    with open(ENTRIES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_entries(data):
    with open(ENTRIES_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")

def parse_opml(path):
    tree = ET.parse(path)
    root = tree.getroot()
    results = []
    for top in root.findall(".//body/outline"):
        cat = top.get("text", "")
        for item in top.findall("outline"):
            text = item.get("text", "")
            title = item.get("title", text)
            xml_url = item.get("xmlUrl", "")
            html_url = item.get("htmlUrl", "")
            results.append((cat, title, xml_url, html_url))
    return results

def normalize_domain(url):
    try:
        h = urlparse(url).hostname
        return h.lower().replace("www.", "") if h else None
    except:
        return None

def get_existing_domains(data):
    domains = set()
    for e in data["entries"]:
        for url in e.get("links", {}).values():
            d = normalize_domain(url)
            if d:
                domains.add(d)
    return domains

def get_existing_ids(data):
    return {e["id"] for e in data["entries"]}

def to_kebab(s):
    s = re.sub(r'[^\w\s-]', '', s).strip().lower()
    return re.sub(r'[-\s]+', '-', s)[:60]

def is_bridge(url):
    bridges = ["rsshub.app", "rsshub.imlg.co", "rsshub.rssforever.com",
               "wechat2rss", "werss.bestblogs", "kill-the-newsletter",
               "plink.anyfeeder", "wechat2rss.bestblogs"]
    return any(b in (url or "") for b in bridges)

def normalize_name(name):
    return name.replace("&amp;", "&").replace("&apos;", "'").replace("&lt;", "<").replace("&gt;", ">").strip()

# ============================================================
SKIP_IDS = {"all-about-android-twit","bad-tempered-developer","coder-pig","innei","matthias-endler","nativeguru-blog","wangxiaoer-juejin"}

# MANUALLY CURATED NEW ENTRIES (from OPML analysis)
# ============================================================
# These are hand-picked quality sources from follow.opml, organized by category.
# Only sources NOT already in entries.json are included.

NEW_ENTRIES = [
    # === android-official ===
    {
        "id": "google-developer-cn-wechat",
        "name": "谷歌开发者 (公众号)",
        "category": "android-official",
        "desc": "Google 官方中文开发者公众号，Android/GCP/ML 技术资讯",
        "links": {"wechat": "谷歌开发者"},
        "tags": ["official", "cn"],
        "quality": 5,
    },
    {
        "id": "android-dev-youtube-rss",
        "name": "Android Developers (YouTube)",
        "category": "android-official",
        "desc": "Google Android 官方 YouTube 频道视频更新",
        "links": {
            "youtube": "https://www.youtube.com/@AndroidDevelopers",
            "rss": "https://rsshub.app/youtube/user/%40AndroidDevelopers"
        },
        "tags": ["official", "video"],
        "quality": 5,
    },
    {
        "id": "android-dev-medium",
        "name": "Android Developers (Medium)",
        "category": "android-official",
        "desc": "Google Android 团队 Medium 博客",
        "links": {
            "blog": "https://medium.com/androiddevelopers",
            "rss": "https://medium.com/feed/androiddevelopers"
        },
        "tags": ["official", "medium"],
        "quality": 4,
    },
    {
        "id": "kotlin-blog-jetbrains",
        "name": "Kotlin Blog (JetBrains)",
        "category": "android-official",
        "desc": "JetBrains 官方 Kotlin 博客，语言特性、多平台、Compose",
        "links": {
            "blog": "https://blog.jetbrains.com/kotlin/",
            "rss": "https://blog.jetbrains.com/kotlin/feed/"
        },
        "tags": ["official", "kotlin"],
        "quality": 5,
    },
    {
        "id": "flutter-blog",
        "name": "Flutter Blog",
        "category": "android-official",
        "desc": "Google Flutter 官方博客，跨平台 UI 框架",
        "links": {
            "blog": "https://blog.flutter.dev/",
            "rss": "https://medium.com/feed/flutter"
        },
        "tags": ["official", "flutter"],
        "quality": 5,
    },
    {
        "id": "android-google-blog",
        "name": "Android (Google Blog)",
        "category": "android-official",
        "desc": "Google 官方 Android 产品动态博客",
        "links": {
            "blog": "https://blog.google/products-and-platforms/platforms/android/",
            "rss": "https://blog.google/products-and-platforms/platforms/android/rss/"
        },
        "tags": ["official"],
        "quality": 5,
    },
    {
        "id": "google-deepmind-blog",
        "name": "Google DeepMind Blog",
        "category": "ai",
        "desc": "Google DeepMind 官方研究博客，AI 前沿突破",
        "links": {
            "blog": "https://deepmind.google/blog/",
            "rss": "https://rsshub.app/deepmind/blog"
        },
        "tags": ["official", "research"],
        "quality": 5,
    },

    # === android-blog ===
    {
        "id": "rengwuxian",
        "name": "扔物线 (Henley)",
        "category": "android-blog",
        "desc": "Android 开发布道师，Kotlin/自定义 View/Jetpack 影响力极大",
        "links": {
            "blog": "https://rengwuxian.com/",
            "juejin": "https://juejin.cn/user/2524134386185736",
            "rss": "https://rengwuxian.com/rss/"
        },
        "tags": ["cn", "active", "kotlin"],
        "quality": 5,
    },
    {
        "id": "jsonchao",
        "name": "jsonchao",
        "category": "android-blog",
        "desc": "Android 性能优化和架构设计，持续产出高质量文章",
        "links": {
            "juejin": "https://juejin.cn/user/4318537403878167",
            "rss": "https://rsshub.app/juejin/dynamic/4318537403878167"
        },
        "tags": ["cn", "performance"],
        "quality": 4,
    },
    {
        "id": "bennyhuo",
        "name": "霍丙乾 (bennyhuo)",
        "category": "android-blog",
        "desc": "Kotlin 布道师，《深入理解 Kotlin 协程》作者",
        "links": {
            "juejin": "https://juejin.cn/user/1187128286120631",
            "rss": "https://rsshub.app/juejin/dynamic/1187128286120631"
        },
        "tags": ["cn", "kotlin"],
        "quality": 5,
    },
    {
        "id": "fundroid",
        "name": "fundroid (玉刚说)",
        "category": "android-blog",
        "desc": "Android 技术博主，覆盖 Compose、Jetpack、架构",
        "links": {
            "juejin": "https://juejin.cn/user/3931509309842872",
            "rss": "https://rsshub.app/juejin/dynamic/3931509309842872"
        },
        "tags": ["cn", "compose"],
        "quality": 4,
    },
    {
        "id": "zhangke",
        "name": "张可",
        "category": "android-blog",
        "desc": "独立技术博客，Android 和通用技术话题",
        "links": {
            "blog": "https://zhangke.space/",
            "rss": "https://zhangke.space/feed/"
        },
        "tags": ["cn", "independent"],
        "quality": 4,
    },
    {
        "id": "isming",
        "name": "码农明明桑",
        "category": "android-blog",
        "desc": "Android 独立开发者，移动开发技术分享",
        "links": {
            "blog": "https://isming.me/",
            "rss": "https://isming.me/index.xml"
        },
        "tags": ["cn", "independent"],
        "quality": 4,
    },
    {
        "id": "browserlab-zhihu",
        "name": "BrowserLab (知乎专栏)",
        "category": "android-blog",
        "desc": "浏览器与 Web 技术深度分析专栏",
        "links": {
            "blog": "https://zhuanlan.zhihu.com/browserlab",
            "rss": "https://rss.lilydjwg.me/zhihuzhuanlan/browserlab"
        },
        "tags": ["cn", "browser"],
        "quality": 4,
    },
    {
        "id": "yixuxin-zhihu",
        "name": "易旭昕 (知乎)",
        "category": "android-blog",
        "desc": "Android 系统开发专家，知乎深度回答",
        "links": {
            "zhihu": "https://www.zhihu.com/people/rogeryi",
            "rss": "https://rsshub.app/zhihu/people/activities/rogeryi"
        },
        "tags": ["cn", "system"],
        "quality": 4,
    },
    {
        "id": "meituan-tech",
        "name": "美团技术团队",
        "category": "android-blog",
        "desc": "美团官方技术博客，Android/iOS/后端/工程实践",
        "links": {
            "blog": "https://tech.meituan.com/",
            "rss": "https://tech.meituan.com/atom.xml"
        },
        "tags": ["cn", "company"],
        "quality": 5,
    },
    {
        "id": "youzan-tech",
        "name": "有赞技术团队",
        "category": "android-blog",
        "desc": "有赞官方技术博客，电商技术实践",
        "links": {
            "blog": "https://tech.youzan.com/",
            "rss": "https://tech.youzan.com/rss/"
        },
        "tags": ["cn", "company"],
        "quality": 4,
    },
    {
        "id": "tencent-tech",
        "name": "腾讯技术工程",
        "category": "android-blog",
        "desc": "腾讯官方技术公众号，大前端和移动端",
        "links": {"wechat": "腾讯技术工程"},
        "tags": ["cn", "company"],
        "quality": 5,
    },
    {
        "id": "xiaomi-tech",
        "name": "小米技术",
        "category": "android-blog",
        "desc": "小米官方技术公众号，MIUI/Android 系统开发",
        "links": {"wechat": "小米技术"},
        "tags": ["cn", "company"],
        "quality": 4,
    },
    {
        "id": "bilibili-tech",
        "name": "哔哩哔哩技术",
        "category": "android-blog",
        "desc": "B站官方技术博客，大规模系统架构和移动端",
        "links": {"wechat": "哔哩哔哩技术"},
        "tags": ["cn", "company"],
        "quality": 4,
    },
    {
        "id": "aliyun-dev",
        "name": "阿里云开发者",
        "category": "android-blog",
        "desc": "阿里云官方技术公众号，云原生和移动开发",
        "links": {"wechat": "阿里云开发者"},
        "tags": ["cn", "company"],
        "quality": 4,
    },
    {
        "id": "bytedance-tech",
        "name": "字节跳动技术团队",
        "category": "android-blog",
        "desc": "字节跳动官方技术博客，覆盖 Android、后端、前端、AI",
        "links": {
            "juejin": "https://juejin.cn/user/1838039172387262",
            "rss": "https://rsshub.app/juejin/posts/1838039172387262"
        },
        "tags": ["cn", "company"],
        "quality": 5,
    },
    {
        "id": "wangxiaoer-bilibili",
        "name": "王小二 (B站)",
        "category": "android-blog",
        "desc": "Android 视频教程博主，Framework 和性能优化讲解",
        "links": {
            "youtube": "https://space.bilibili.com/485954104",
            "rss": "https://rsshub.app/bilibili/user/video/485954104"
        },
        "tags": ["cn", "video"],
        "quality": 4,
    },
    {
        "id": "ahaoframework",
        "name": "阿豪讲Framework",
        "category": "android-blog",
        "desc": "专注于 Android Framework 源码分析",
        "links": {
            "juejin": "https://juejin.cn/user/342703355728382",
            "rss": "https://rsshub.app/juejin/posts/342703355728382"
        },
        "tags": ["cn", "framework"],
        "quality": 4,
    },
    {
        "id": "kanxue-android",
        "name": "看雪论坛 Android 安全",
        "category": "android-blog",
        "desc": "看雪论坛 Android 安全方向精华帖",
        "links": {
            "website": "https://bbs.kanxue.com/forum-161-1.htm?digest=1",
            "rss": "https://rsshub.app/kanxue/topic/android/digest"
        },
        "tags": ["cn", "security"],
        "quality": 4,
    },
    {
        "id": "qianlima-framework",
        "name": "千里马学框架 (CSDN)",
        "category": "android-blog",
        "desc": "专注于 Android Framework 学习的 CSDN 博主",
        "links": {
            "blog": "https://blog.csdn.net/learnframework",
            "rss": "https://rss.csdn.net/learnframework/rss/map"
        },
        "tags": ["cn", "framework"],
        "quality": 4,
    },
    {
        "id": "seb-sellmair",
        "name": "Seb's Coding Blog",
        "category": "android-blog",
        "desc": "Android/Kotlin 技术博客，实践导向",
        "links": {
            "blog": "https://blog.sellmair.io/",
            "rss": "https://blog.sellmair.io/rss.xml"
        },
        "tags": ["kotlin", "compose"],
        "quality": 4,
    },
    {
        "id": "zach-klippenstein",
        "name": "Zach Klippenstein",
        "category": "android-blog",
        "desc": "Android 开发者，Compose 深度技术博客",
        "links": {
            "blog": "https://blog.zachklipp.com/",
            "rss": "https://blog.zachklipp.com/rss/"
        },
        "tags": ["compose"],
        "quality": 4,
    },
    {
        "id": "py-blog",
        "name": "P-Y's blog",
        "category": "android-blog",
        "desc": "Android 开发技术博客",
        "links": {
            "blog": "https://blog.p-y.wtf/",
            "rss": "https://blog.p-y.wtf/rss.xml"
        },
        "tags": [],
        "quality": 4,
    },
    {
        "id": "pl-coding",
        "name": "pl-coding.com",
        "category": "android-blog",
        "desc": "Android 开发教程博客，Kotlin 和 Compose",
        "links": {
            "blog": "https://pl-coding.com/",
            "rss": "https://pl-coding.com/feed/"
        },
        "tags": ["kotlin", "compose", "tutorial"],
        "quality": 4,
    },
    {
        "id": "android-authority-podcast",
        "name": "Android Authority Podcast",
        "category": "android-blog",
        "desc": "Android 权威媒体播客，新设备、应用和系统动态",
        "links": {
            "website": "http://www.androidauthority.com/podcast",
            "rss": "https://rss.libsyn.com/shows/62117/destinations/242501.xml"
        },
        "tags": ["podcast"],
        "quality": 4,
    },
    {
        "id": "nativeguru-blog",
        "name": "NativeGuru",
        "category": "android-blog",
        "desc": "Linux 嵌入式和 Android 安全技术博客",
        "links": {
            "blog": "https://nativeguru.wordpress.com/",
            "rss": "https://nativeguru.wordpress.com/feed/"
        },
        "tags": ["security", "embedded"],
        "quality": 3,
    },
    {
        "id": "liqing-bytedance",
        "name": "离青 (字节跳动)",
        "category": "android-blog",
        "desc": "字节跳动 Android 团队，系统级技术分享",
        "links": {
            "juejin": "https://juejin.cn/user/2585702698590472",
            "rss": "https://rsshub.app/juejin/dynamic/2585702698590472"
        },
        "tags": ["cn", "system"],
        "quality": 4,
    },
    {
        "id": "wangxiaoer-juejin",
        "name": "王小二的技术栈 (掘金)",
        "category": "android-blog",
        "desc": "Android 技术博主，掘金平台活跃",
        "links": {
            "juejin": "https://juejin.cn/user/1821226473634552",
            "rss": "https://rsshub.app/juejin/dynamic/1821226473634552"
        },
        "tags": ["cn"],
        "quality": 3,
    },
    {
        "id": "coder-pig",
        "name": "coder-pig",
        "category": "android-blog",
        "desc": "Android 技术博主，持续更新",
        "links": {
            "juejin": "https://juejin.cn/user/4142615541321928",
            "rss": "https://rsshub.app/juejin/dynamic/4142615541321928"
        },
        "tags": ["cn"],
        "quality": 3,
    },

    # === android-community ===
    {
        "id": "now-in-android",
        "name": "Now in Android",
        "category": "android-community",
        "desc": "Google 官方 Android 新闻播客，紧跟平台最新动态",
        "links": {
            "website": "https://developer.android.com/",
            "rss": "https://feeds.libsyn.com/244409/rss"
        },
        "tags": ["podcast", "official"],
        "quality": 5,
    },
    {
        "id": "all-about-android-twit",
        "name": "All About Android (TWiT)",
        "category": "android-community",
        "desc": "TWiT 网络的 Android 讨论节目",
        "links": {
            "website": "https://twit.tv/shows/all-about-android",
            "rss": "https://feeds.twit.tv/aaa.xml"
        },
        "tags": ["podcast"],
        "quality": 3,
    },

    # === general-tech (CN-Blog picks) ===
    {
        "id": "raye-journey",
        "name": "Raye's Journey",
        "category": "general-tech",
        "desc": "技术和安全博客，内容质量高",
        "links": {
            "blog": "https://rayepeng.net/",
            "rss": "https://rayepeng.net/feed"
        },
        "tags": ["cn"],
        "quality": 4,
    },
    {
        "id": "pythoncat",
        "name": "豌豆花下猫",
        "category": "general-tech",
        "desc": "Python 技术博客，内容质量高",
        "links": {
            "blog": "https://pythoncat.top/",
            "rss": "https://pythoncat.top/rss.xml"
        },
        "tags": ["cn", "python"],
        "quality": 4,
    },
    {
        "id": "jerryqu",
        "name": "JerryQu 的博客",
        "category": "general-tech",
        "desc": "Web 性能和前端技术专家",
        "links": {
            "blog": "https://imququ.com/",
            "rss": "https://imququ.com/rss.html"
        },
        "tags": ["cn", "web-performance"],
        "quality": 4,
    },
    {
        "id": "williamlong",
        "name": "月光博客",
        "category": "general-tech",
        "desc": "中文老牌科技博客，互联网观察",
        "links": {
            "blog": "https://www.williamlong.info/",
            "rss": "https://www.williamlong.info/rss.xml"
        },
        "tags": ["cn", "classic"],
        "quality": 4,
    },
    {
        "id": "owenyoung",
        "name": "Owen的博客",
        "category": "general-tech",
        "desc": "独立开发者博客，工具和效率",
        "links": {
            "blog": "https://www.owenyoung.com/",
            "rss": "https://www.owenyoung.com/atom.xml"
        },
        "tags": ["cn"],
        "quality": 4,
    },
    {
        "id": "diygod",
        "name": "Hi, DIYgod",
        "category": "general-tech",
        "desc": "RSSHub 作者，前端和开源贡献",
        "links": {
            "blog": "https://diygod.cc/",
            "rss": "https://diygod.cc/feed"
        },
        "tags": ["cn", "open-source"],
        "quality": 4,
    },
    {
        "id": "sukka-blog",
        "name": "Sukka's Blog",
        "category": "general-tech",
        "desc": "前端和 Web 性能，技术深度好",
        "links": {
            "blog": "https://blog.skk.moe/",
            "rss": "https://blog.skk.moe/atom.xml"
        },
        "tags": ["cn", "web-performance"],
        "quality": 4,
    },
    {
        "id": "sorrycc",
        "name": "云谦的博客",
        "category": "general-tech",
        "desc": "前端开发者，Umi.js 作者",
        "links": {
            "blog": "https://sorrycc.com/",
            "rss": "https://sorrycc.com/feed"
        },
        "tags": ["cn", "frontend"],
        "quality": 4,
    },
    {
        "id": "baoyu-share",
        "name": "宝玉的分享",
        "category": "general-tech",
        "desc": "AI 和技术分享博客",
        "links": {
            "blog": "https://s.baoyu.io/",
            "rss": "https://s.baoyu.io/feed.xml"
        },
        "tags": ["cn", "ai"],
        "quality": 4,
    },
    {
        "id": "limboy",
        "name": "Limboy",
        "category": "general-tech",
        "desc": "移动端技术专家，iOS 和跨平台",
        "links": {
            "blog": "https://limboy.me/",
            "rss": "https://limboy.me/index.xml"
        },
        "tags": ["cn", "ios"],
        "quality": 4,
    },
    {
        "id": "innei",
        "name": "静かな森",
        "category": "general-tech",
        "desc": "前端开发者博客",
        "links": {
            "blog": "https://innei.in/",
            "rss": "https://innei.in/feed"
        },
        "tags": ["cn", "frontend"],
        "quality": 3,
    },
    {
        "id": "frostming",
        "name": "Frost's Blog",
        "category": "general-tech",
        "desc": "Python 开发者，MVP 和开源贡献",
        "links": {
            "blog": "https://frostming.com/",
            "rss": "https://frostming.com/feed.xml"
        },
        "tags": ["cn", "python"],
        "quality": 4,
    },
    {
        "id": "hn-daily-cn",
        "name": "HackerNews 每日摘要",
        "category": "general-tech",
        "desc": "Hacker News 中文摘要翻译",
        "links": {
            "blog": "https://supertechfans.com/cn/",
            "rss": "https://www.supertechfans.com/cn/index.xml"
        },
        "tags": ["cn", "hn"],
        "quality": 4,
    },
    {
        "id": "techmeme",
        "name": "Techmeme",
        "category": "general-tech",
        "desc": "科技新闻聚合器，行业必读",
        "links": {
            "website": "https://www.techmeme.com/",
            "rss": "https://www.techmeme.com/feed.xml"
        },
        "tags": ["news", "aggregator"],
        "quality": 5,
    },
    {
        "id": "chaoliu-weekly",
        "name": "潮流周刊",
        "category": "general-tech",
        "desc": "Tw93 的科技和潮流周刊",
        "links": {
            "website": "https://weekly.tw93.fun/",
            "rss": "https://weekly.tw93.fun/rss.xml"
        },
        "tags": ["cn", "newsletter", "weekly"],
        "quality": 4,
    },
    {
        "id": "melting-asphalt",
        "name": "Melting Asphalt",
        "category": "general-tech",
        "desc": "Andy Matuschak 深度思考博客，学习科学和工具设计",
        "links": {
            "blog": "https://meltingasphalt.com/",
            "rss": "http://feeds.feedburner.com/MeltingAsphalt"
        },
        "tags": ["en", "learning"],
        "quality": 5,
    },
    {
        "id": "nicholas-carlini",
        "name": "Nicholas Carlini",
        "category": "general-tech",
        "desc": "机器学习安全研究员，技术博客深度极高",
        "links": {
            "blog": "https://nicholas.carlini.com/",
            "rss": "https://nicholas.carlini.com/writing/feed.xml"
        },
        "tags": ["en", "ml-security"],
        "quality": 5,
    },
    {
        "id": "michael-nielsen",
        "name": "Michael Nielsen",
        "category": "general-tech",
        "desc": "量子计算和 AI 研究，写作质量极高",
        "links": {
            "blog": "https://michaelnielsen.org/blog",
            "rss": "https://michaelnielsen.org/blog/feed/"
        },
        "tags": ["en", "research"],
        "quality": 5,
    },
    {
        "id": "wait-but-why",
        "name": "Wait But Why",
        "category": "general-tech",
        "desc": "深度长文博客，用漫画解释复杂概念",
        "links": {
            "blog": "https://waitbutwhy.com/",
            "rss": "https://waitbutwhy.com/feed"
        },
        "tags": ["en", "longform"],
        "quality": 5,
    },
    {
        "id": "steph-ango",
        "name": "Steph Ango",
        "category": "general-tech",
        "desc": "Obsidian CEO，产品和设计博客",
        "links": {
            "blog": "https://stephango.com/",
            "rss": "https://stephango.com/feed.xml"
        },
        "tags": ["en", "product"],
        "quality": 4,
    },
    {
        "id": "paul-graham-essays",
        "name": "Paul Graham Essays",
        "category": "general-tech",
        "desc": "Y Combinator 联合创始人，创业和技术随笔",
        "links": {
            "blog": "https://paulgraham.com/articles.html",
            "rss": "https://rsshub.imlg.co/paulgraham/articles"
        },
        "tags": ["en", "startup"],
        "quality": 5,
    },
    {
        "id": "david-perell",
        "name": "David Perell",
        "category": "general-tech",
        "desc": "写作和思想博客",
        "links": {
            "blog": "https://perell.com/",
            "rss": "https://perell.com/feed/"
        },
        "tags": ["en", "writing"],
        "quality": 4,
    },
    {
        "id": "aeon-magazine",
        "name": "Aeon",
        "category": "general-tech",
        "desc": "深度思想杂志，哲学、科学、文化",
        "links": {
            "website": "https://aeon.co/",
            "rss": "https://aeon.co/feed.rss"
        },
        "tags": ["en", "ideas"],
        "quality": 4,
    },
    {
        "id": "scott-h-young",
        "name": "Scott H Young",
        "category": "general-tech",
        "desc": "学习方法论和效率博客，MIT Challenge 作者",
        "links": {
            "blog": "https://www.scotthyoung.com/blog/",
            "rss": "https://www.scotthyoung.com/blog/feed/"
        },
        "tags": ["en", "learning"],
        "quality": 4,
    },
    {
        "id": "rest-of-world",
        "name": "Rest of World",
        "category": "general-tech",
        "desc": "全球科技报道，聚焦新兴市场",
        "links": {
            "website": "https://restofworld.org/",
            "rss": "https://restofworld.org/feed/latest"
        },
        "tags": ["en", "journalism"],
        "quality": 4,
    },

    # === AI additions from OPML ===
    {
        "id": "sam-altman-blog",
        "name": "Sam Altman Blog",
        "category": "ai",
        "desc": "OpenAI CEO 官方博客",
        "links": {
            "blog": "https://blog.samaltman.com/",
            "rss": "https://blog.samaltman.com/posts.atom"
        },
        "tags": ["llm", "official"],
        "quality": 5,
    },
    {
        "id": "chip-huyen",
        "name": "Chip Huyen",
        "category": "ai",
        "desc": "ML 工程专家，Stanford 讲师，《Designing ML Systems》作者",
        "links": {
            "blog": "https://huyenchip.com/",
            "rss": "https://huyenchip.com/feed.xml"
        },
        "tags": ["ml", "engineering"],
        "quality": 5,
    },
    {
        "id": "matthias-endler",
        "name": "Matthias Endler",
        "category": "general-tech",
        "desc": "Rust 和编译器技术博客",
        "links": {
            "blog": "https://endler.dev/",
            "rss": "https://endler.dev/rss.xml"
        },
        "tags": ["en", "rust"],
        "quality": 3,
    },
]


def generate_opml(data, output_path):
    """Generate feeds.opml from entries.json."""
    categories = {c["id"]: c["name"] for c in data["categories"]}
    
    # Group entries with RSS by category
    grouped = {}
    for entry in data["entries"]:
        links = entry.get("links", {})
        rss_url = links.get("rss")
        if not rss_url:
            continue
        
        cat_id = entry.get("category", "general-tech")
        if cat_id not in grouped:
            grouped[cat_id] = []
        grouped[cat_id].append(entry)
    
    total_feeds = sum(len(v) for v in grouped.values())
    
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<opml version="2.0">',
        '  <head>',
        f'    <title>{data["name"]}</title>',
        f'    <dateCreated>2026-04-11T00:00:00Z</dateCreated>',
        f'    <description>{data["description"]}</description>',
        '  </head>',
        '  <body>',
    ]
    
    for cat_id, cat_name in categories.items():
        entries = grouped.get(cat_id, [])
        if not entries:
            continue
        cat_name_escaped = cat_name.replace('&', '&amp;').replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
        lines.append(f'    <outline text="{cat_name_escaped}">')
        for entry in entries:
            links = entry.get("links", {})
            title = entry["name"]
            html_url = links.get("blog") or links.get("website") or ""
            xml_url = links.get("rss", "")
            
            # Escape XML special chars in title
            title_escaped = title.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")
            
            lines.append(f'      <outline text="{title_escaped}" title="{title_escaped}" type="rss" xmlUrl="{xml_url}" htmlUrl="{html_url}"/>')
        lines.append('    </outline>')
    
    lines.append('  </body>')
    lines.append('</opml>')
    lines.append('')
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    
    return total_feeds


def update_readme_generator(feed_count):
    """Add OPML download section to generate-readme.py."""
    readme_path = os.path.join(os.path.dirname(__file__), "generate-readme.py")
    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Find the "### 自动维护" section and insert before it
    opml_section = f"""
    lines.append("### 订阅")
    lines.append("")
    lines.append(f"- 📡 [OPML 文件](data/feeds.opml) — 导入到 RSS 阅读器（Inoreader、Feedly 等）")
    lines.append(f"- 包含 {feed_count} 个可用 RSS 源")
    lines.append("")

"""
    
    marker = '    lines.append("### 自动维护")'
    if marker in content and "OPML 文件" not in content:
        content = content.replace(marker, opml_section.strip() + "\n" + marker)
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("generate-readme.py updated with OPML section")
    elif "OPML 文件" in content:
        # Update count
        import re as _re
        content = _re.sub(r'包含 \d+ 个可用 RSS 源', f'包含 {feed_count} 个可用 RSS 源', content)
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"generate-readme.py OPML count updated to {feed_count}")
    else:
        print("Warning: Could not find insertion point in generate-readme.py")


def main():
    print("=" * 60)
    print("Integrating follow.opml into entries.json")
    print("=" * 60)
    
    data = load_entries()
    existing_ids = get_existing_ids(data)
    existing_domains = get_existing_domains(data)
    
    print(f"\nExisting entries: {len(data['entries'])}")
    print(f"Existing IDs: {len(existing_ids)}")
    
    # Parse OPML for stats
    opml_entries = parse_opml(OPML_PATH)
    print(f"OPML sources parsed: {len(opml_entries)}")
    
    # Count by category
    cat_counts = {}
    for cat, title, xml, html in opml_entries:
        cat_counts[cat] = cat_counts.get(cat, 0) + 1
    print("\nOPML categories:")
    for cat, count in sorted(cat_counts.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")
    
    # Add new entries (dedup by id)
    added = 0
    skipped = 0
    for entry in NEW_ENTRIES:
        if entry["id"] in existing_ids or entry["id"] in SKIP_IDS:
            skipped += 1
            continue
        data["entries"].append(entry)
        existing_ids.add(entry["id"])
        added += 1
    
    print(f"\nNew entries added: {added}")
    print(f"Skipped (already exist): {skipped}")
    print(f"Total entries: {len(data['entries'])}")
    
    # Save entries.json
    save_entries(data)
    
    # Generate feeds.opml
    feed_count = generate_opml(data, OPML_OUT_PATH)
    print(f"\nfeeds.opml generated: {feed_count} RSS feeds")
    
    # Update README generator
    update_readme_generator(feed_count)
    
    print("\n✅ Done!")


if __name__ == "__main__":
    main()
