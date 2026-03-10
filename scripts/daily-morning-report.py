#!/usr/bin/env python3
"""
TrendRadar 每日晨报脚本
每天早晨 9 点执行，推送：
1. 当日榜单 TOP5
2. AI 相关热点新闻
"""

import os
import re
import requests
import json
from datetime import datetime
from collections import Counter

# TrendRadar 输出目录
OUTPUT_DIR = "/home/admin/.openclaw/data/trendradar/output"
TODAY = datetime.now().strftime("%Y-%m-%d")


def get_latest_txt_file():
    """获取今天最新的 txt 文件"""
    today_dir = os.path.join(OUTPUT_DIR, TODAY, "txt")
    if not os.path.exists(today_dir):
        return None
    
    txt_files = [f for f in os.listdir(today_dir) if f.endswith('.txt')]
    if not txt_files:
        return None
    
    # 按时间排序，取最新的
    txt_files.sort(reverse=True)
    return os.path.join(today_dir, txt_files[0])


def parse_news_file(filepath):
    """解析新闻文件，返回平台新闻列表和频率统计"""
    platforms = {}
    current_platform = None
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            # 平台行格式：platform | 平台名称
            if ' | ' in line and not line.startswith('1.'):
                parts = line.split(' | ')
                if len(parts) == 2:
                    current_platform = {
                        'id': parts[0],
                        'name': parts[1],
                        'news': []
                    }
                    platforms[parts[0]] = current_platform
            # 新闻行格式：1. 标题 [URL:xxx]
            elif line.startswith(tuple(f"{i}." for i in range(1, 50))) and current_platform:
                # 去掉 URL
                title = re.sub(r'\s*\[URL:.*\]', '', line)
                current_platform['news'].append(title)
    
    return platforms


def calculate_frequency(platforms, keywords):
    """计算关键词频率"""
    frequency = Counter()
    
    for platform_id, platform_data in platforms.items():
        for news in platform_data['news']:
            for keyword in keywords:
                if keyword.lower() in news.lower():
                    frequency[keyword] += 1
    
    return frequency


def search_ai_news(platforms):
    """搜索 AI 相关新闻"""
    ai_keywords = ['AI', '人工智能', '大模型', '机器学习', '深度学习', '智能', '算法']
    ai_news = []
    
    for platform_id, platform_data in platforms.items():
        for news in platform_data['news']:
            for keyword in ai_keywords:
                if keyword.lower() in news.lower():
                    ai_news.append({
                        'platform': platform_data['name'],
                        'title': news
                    })
                    break
    
    return ai_news


def format_dingtalk_message(top5, ai_news):
    """格式化 DingTalk 消息"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    message = f"## 📊 TrendRadar 每日晨报 ({now})\n\n"
    
    # TOP5 榜单
    message += "### 🔥 今日热点 TOP5\n\n"
    if top5:
        for i, (keyword, count) in enumerate(top5[:5], 1):
            message += f"{i}. **{keyword}** - {count} 条新闻\n"
    else:
        message += "暂无数据\n"
    
    message += "\n---\n\n"
    
    # AI 相关新闻
    message += "### 🤖 AI 热点新闻\n\n"
    if ai_news:
        for i, news in enumerate(ai_news[:5], 1):
            title = news['title']
            platform = news['platform']
            # 截断过长的标题
            if len(title) > 50:
                title = title[:47] + "..."
            message += f"{i}. [{platform}] {title}\n"
    else:
        message += "暂无 AI 相关新闻\n"
    
    message += "\n---\n_由 TrendRadar + OpenClaw 自动生成_"
    
    return message


def send_dingtalk(message):
    """发送 DingTalk 消息"""
    # 使用 notify.sh 脚本发送（已调试通过）
    import subprocess
    import os
    
    try:
        # 使用 notify.sh 发送
        result = subprocess.run(
            ['/home/admin/.openclaw/scripts/notify.sh', message],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            timeout=60
        )
        
        if result.returncode == 0:
            print("✅ 消息发送成功")
            return True
        else:
            print(f"❌ 发送失败：{result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ 发送异常：{e}")
        return False


def main():
    print("开始生成每日晨报...")
    
    # 获取最新的 txt 文件
    txt_file = get_latest_txt_file()
    if not txt_file:
        print(f"❌ 未找到今天的新闻文件 ({TODAY})")
        # 尝试运行爬虫
        print("🔄 尝试运行 TrendRadar 爬虫...")
        os.system("cd /home/admin/.openclaw/workspace/projects/TrendRadar && ./run-local.sh")
        txt_file = get_latest_txt_file()
        
        if not txt_file:
            print("❌ 仍然未找到数据，退出")
            return
    
    print(f"📄 读取文件：{txt_file}")
    
    # 解析新闻
    platforms = parse_news_file(txt_file)
    print(f"✅ 解析完成：{len(platforms)} 个平台")
    
    # 定义关注关键词
    keywords = ['AI', '人工智能', '大模型', '机器学习', '深度学习', 
                '量化交易', '跨境电商', '芯片', '存储', '白银',
                '智能', '算法', '模型', '数据', '科技']
    
    # 计算频率
    frequency = calculate_frequency(platforms, keywords)
    top5 = frequency.most_common(5)
    
    # 搜索 AI 新闻
    ai_news = search_ai_news(platforms)
    
    # 格式化消息
    message = format_dingtalk_message(top5, ai_news)
    
    # 输出到 stdout
    print("\n" + "="*50)
    print(message)
    print("="*50 + "\n")
    
    # 发送 DingTalk
    send_dingtalk(message)
    
    print("晨报生成完成")


if __name__ == "__main__":
    main()
