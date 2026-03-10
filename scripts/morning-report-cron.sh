#!/bin/bash
# TrendRadar 每日晨报 - Cron 脚本
# 每天早晨 9 点执行
# 1. 先运行爬虫获取最新数据
# 2. 生成并推送晨报

set -e

SCRIPT_DIR="/home/admin/.openclaw/workspace/projects/TrendRadar"
LOG_FILE="/home/admin/.openclaw/data/trendradar/logs/morning-report.log"

# 创建日志目录
mkdir -p "$(dirname "$LOG_FILE")"

echo "===== TrendRadar 每日晨报 $(date '+%Y-%m-%d %H:%M:%S') =====" >> "$LOG_FILE"

# 1. 运行爬虫获取最新数据
echo "🚀 启动 TrendRadar 爬虫..." >> "$LOG_FILE"
cd "$SCRIPT_DIR"
if ./run-local.sh >> "$LOG_FILE" 2>&1; then
    echo "✅ 爬虫执行成功" >> "$LOG_FILE"
else
    echo "❌ 爬虫执行失败" >> "$LOG_FILE"
fi

# 2. 生成并推送晨报
echo "📊 生成晨报..." >> "$LOG_FILE"
if python3 "$SCRIPT_DIR/scripts/daily-morning-report.py" >> "$LOG_FILE" 2>&1; then
    echo "✅ 晨报推送成功" >> "$LOG_FILE"
else
    echo "❌ 晨报推送失败" >> "$LOG_FILE"
fi

echo "===== 完成 =====" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"
