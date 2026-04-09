---
name: wp-blog-poster
description: ACDesign 网站自动发文 - 搜索香港装修热点话题，AI 撰写繁体中文+英文双语文章，Imagen 生成配图，WordPress REST API 自动发布
version: 1.0.0
author: ymj
created_at: 2026-04-09
updated_at: 2026-04-09
license: MIT
dependencies:
  - image-gen
triggers:
  - /wp-blog-poster
  - 發布裝修文章
  - post blog article
---

# WordPress 自动发文 Skill

每次运行发布 1 篇香港装修知识文章到 www.acdesign.com.hk。

## 执行流程

按以下步骤严格执行：

### Step 1: 搜索热点话题

用 WebSearch 搜索以下关键词，寻找近 7 天内的香港装修相关热点：

```
搜索词列表（每次选 2-3 个搜索）：
- "香港裝修 新聞 2026"
- "裝修公司 投訴 香港"
- "室內設計 趨勢 香港"
- "香港樓市 裝修"
- "裝修 消委會"
- "公屋裝修 2026"
- "裝修糾紛 香港"
```

分析搜索结果：
- 如果发现近 7 天的热点新闻（公司倒闭、政策变化、消委会报告、楼市变化等）→ **用热点写文**
- 如果没有明显热点 → **从话题库选题**

### Step 2: 选择话题

**热点模式**：根据搜索到的热点，拟定一个吸引眼球的标题。例如：
- 新闻："XX裝修公司結業" → 标题："裝修公司突然結業點算？3招保障你的裝修權益"
- 新闻："公屋加租" → 标题："公屋裝修慳錢攻略：低預算也能住得舒適"
- 新闻："新盤交樓質量差" → 标题："新盤收樓驗樓全攻略：10個必檢位置"

**常青模式**：从 `lib/topics.yaml` 中选一个话题（检查 `lib/published_log.json` 确保不重复）。

### Step 3: 检查重复

读取 `lib/published_log.json`，确认今天的话题不与已发布的文章重复（标题相似度 > 70% 视为重复）。

### Step 4: 撰写文章

#### 繁体中文版（800-1200 字）

文章结构：
```
標題：[吸引眼球的繁体中文标题]

<h2>引言</h2>
<p>[开篇 2-3 句，点出痛点或热点，含主关键词]</p>

<h2>[要点一标题]</h2>
<p>[详细说明，200-300字，含相关关键词]</p>

<h2>[要点二标题]</h2>
<p>[详细说明，200-300字]</p>

<h2>[要点三标题]</h2>
<p>[详细说明，200-300字]</p>

<h2>總結</h2>
<p>[总结要点 + 自然引导到公司服务]</p>
<p>如果你正在計劃裝修，歡迎聯絡<strong>藝創室內設計</strong>，我們提供免費度尺及報價服務。致電 <a href="tel:+85231051661">3105 1661</a> 或 <a href="https://wa.me/85252221129">WhatsApp 查詢</a>。</p>

<hr>

<p><strong>相關內容：</strong></p>
<ul>
<li><a href="https://www.acdesign.com.hk/works/house/">查看我們的住宅設計作品</a></li>
<li><a href="https://www.acdesign.com.hk/service/69/">了解我們的住宅設計服務</a></li>
<li><a href="https://www.acdesign.com.hk/contactus/">聯絡我們免費諮詢</a></li>
</ul>
```

#### 英文版（附在文末）

```
<hr>
<h2>English Summary</h2>
<p>[500-800 words English version of the article]</p>
<p>Contact <strong>Art Creation Interior Design</strong> for a free consultation: <a href="tel:+85231051661">3105 1661</a></p>
```

#### 写作要求
- 使用**繁体中文**（香港用语：「點」「唔」「慳」「揀」）
- 语气专业但亲切，像设计师朋友给建议
- 包含具体数字和实用信息（价格范围、尺寸、品牌名）
- 自然插入关键词，不堆砌
- CTA 自然融入，不生硬推销

### Step 5: 生成配图

运行以下 Python 代码生成特色图片：

```python
import sys
sys.path.insert(0, 'SKILL_DIR/lib')
from image_helper import generate_image

# 根据话题生成英文 prompt
image_path = generate_image(
    topic="[article topic in English, e.g., 'modern kitchen renovation']",
    aspect_ratio="16:9",
    output_dir="SKILL_DIR/lib/temp"
)
print(f"Image generated: {image_path}")
```

其中 SKILL_DIR 替换为 `~/.claude/skills/wp-blog-poster` 的实际绝对路径。

### Step 6: 发布到 WordPress

运行以下 Python 代码发布文章：

```python
import sys, json, os
sys.path.insert(0, 'SKILL_DIR/lib')
from wp_publisher import create_post, upload_media, get_or_create_category, get_or_create_tag

# 1. 上传配图
media_id = upload_media(
    image_path="[Step 5 生成的图片路径]",
    alt_text="[文章主关键词] - 藝創室內設計",
    title="[文章标题]"
)
print(f"Media uploaded: ID={media_id}")

# 2. 获取/创建分类
# 知识类文章用 "裝修知識"，问答类用 "faq"
cat_id = get_or_create_category("[分类名]", "[slug]")
print(f"Category: ID={cat_id}")

# 3. 创建标签
tag_ids = []
for tag_name in ["[关键词1]", "[关键词2]", "[关键词3]"]:
    tid = get_or_create_tag(tag_name)
    tag_ids.append(tid)
    print(f"Tag '{tag_name}': ID={tid}")

# 4. 发布文章
result = create_post(
    title="[繁体中文标题]",
    content="[完整 HTML 内容，含中文版+英文版]",
    category_ids=[cat_id],
    tag_ids=tag_ids,
    featured_media_id=media_id,
    status="publish",
    excerpt="[150字摘要]"
)
print(f"Published: {result['url']}")
```

### Step 7: 记录发布

将发布信息追加到 `lib/published_log.json`：

```python
import json, os
from datetime import datetime

log_path = "SKILL_DIR/lib/published_log.json"
with open(log_path, 'r') as f:
    log = json.load(f)

log.append({
    "date": datetime.now().strftime("%Y-%m-%d"),
    "title": "[文章标题]",
    "url": "[文章URL]",
    "is_trending": True/False,
    "category": "[分类名]",
    "keywords": ["关键词1", "关键词2"]
})

with open(log_path, 'w') as f:
    json.dump(log, f, ensure_ascii=False, indent=2)
```

### Step 8: 报告结果

输出发布摘要：
```
✅ 文章發布成功
標題：[标题]
網址：[URL]
分類：[分类]
標籤：[标签列表]
類型：熱點文章 / 常青話題
配圖：已生成並設為特色圖片
```

## 注意事项

- 每次只发布 1 篇文章
- 必须先搜索热点，有热点优先用热点
- 文章必须原创，不抄袭搜索结果
- 图片使用 AI 生成，不用网络图片
- 发布后清理临时图片文件
