#!/usr/bin/env python3
"""
提取 AI 相关新闻 Top20，带可跳转链接
"""

import os
import re
from datetime import datetime

OUTPUT_DIR = "/home/admin/.openclaw/data/trendradar/output/2026-03-09/txt"

# AI 相关关键词（按优先级排序）
AI_KEYWORDS = ['OpenAI', 'GPT', '人工智能', 'AI', '大模型', '机器学习', '深度学习', '神经网络']
# 排除误匹配的词
EXCLUDE_KEYWORDS = ['智能手', '智能家居', '智能手机', '智能汽车']

def get_latest_file():
    """获取最新的 txt 文件"""
    files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith('.txt')]
    if not files:
        return None
    files.sort(reverse=True)
    return os.path.join(OUTPUT_DIR, files[0])

def parse_and_filter(filepath):
    """解析文件并筛选 AI 新闻，保留 URL"""
    ai_news = []
    current_platform = None
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            # 平台行
            if ' | ' in line and not line.startswith(tuple(f"{i}." for i in range(1, 50))):
                parts = line.split(' | ')
                if len(parts) == 2:
                    current_platform = parts[1]
            
            # 新闻行
            elif current_platform and re.match(r'^\d+\.\s+.+', line):
                # 提取标题（去掉序号和 URL）
                title_match = re.match(r'^\d+\.\s*(.+?)\s*\[URL:', line)
                if not title_match:
                    continue
                
                title = title_match.group(1).strip()
                
                # 提取 URL
                url_match = re.search(r'\[URL:([^\]]+)\]', line)
                url = url_match.group(1) if url_match else None
                
                # 先排除误匹配
                skip = False
                for exclude in EXCLUDE_KEYWORDS:
                    if exclude in title:
                        skip = True
                        break
                if skip:
                    continue
                
                # 检查标题是否包含 AI 关键词（只匹配标题，不匹配 URL）
                for keyword in AI_KEYWORDS:
                    match_found = False
                    # 精确匹配
                    if keyword in title:
                        match_found = True
                    # 小写匹配（针对英文短词）
                    elif len(keyword) <= 3 and re.search(r'\b' + re.escape(keyword) + r'\b', title, re.IGNORECASE):
                        match_found = True
                    
                    if match_found:
                        ai_news.append({
                            'platform': current_platform,
                            'title': title,
                            'url': url,
                            'keyword': keyword
                        })
                        break
    
    return ai_news

def format_dingtalk_message(ai_news, top_n=20):
    """格式化 DingTalk 消息，带可点击链接"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    message = f"## 🤖 AI 相关新闻 Top{top_n}\n\n"
    message += f"**数据来源**: TrendRadar ({now})  \n"
    message += f"**共计**: {len(ai_news)} 条 AI 新闻\n\n"
    message += "---\n\n"
    
    for i, news in enumerate(ai_news[:top_n], 1):
        platform = news['platform']
        title = news['title']
        url = news['url']
        
        # 截断过长的标题
        if len(title) > 45:
            title = title[:42] + "..."
        
        if url:
            # DingTalk Markdown 链接格式：[文本](URL)
            message += f"{i}. **[{platform}]** [{title}]({url})\n"
        else:
            message += f"{i}. **[{platform}]** {title}\n"
    
    message += f"\n---\n_由 TrendRadar + OpenClaw 自动生成_"
    
    return message

def main():
    filepath = get_latest_file()
    if not filepath:
        print("❌ 未找到数据文件")
        return
    
    print(f"📄 文件：{filepath}\n")
    
    ai_news = parse_and_filter(filepath)
    
    print(f"🔍 找到 {len(ai_news)} 条 AI 相关新闻\n")
    
    # 生成消息
    message = format_dingtalk_message(ai_news, top_n=20)
    
    print("=" * 70)
    print(message)
    print("=" * 70)
    
    # 发送 DingTalk
    import subprocess
    result = subprocess.run(
        ['/home/admin/.openclaw/scripts/notify.sh', message],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        timeout=60
    )
    
    if result.returncode == 0:
        print("\n✅ 消息发送成功")
    else:
        print(f"\n❌ 发送失败：{result.stderr}")

if __name__ == "__main__":
    main()
