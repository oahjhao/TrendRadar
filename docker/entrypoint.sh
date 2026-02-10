#!/bin/bash
set -e

# 检查配置文件
if [ ! -f "/app/config/config.yaml" ]; then
    echo "❌ 配置文件 config.yaml 缺失"
    exit 1
fi

# 如果没有设置 KEYWORDS 环境变量，则要求 frequency_words.txt 存在
if [ -z "${KEYWORDS:-}" ] && [ ! -f "/app/config/frequency_words.txt" ]; then
    echo "❌ 配置文件 frequency_words.txt 缺失（未设置 KEYWORDS 环境变量）"
    exit 1
fi

# 保存环境变量
env >> /etc/environment

# 如果设置了 KEYWORDS 环境变量，强制单次执行模式
if [ -n "${KEYWORDS:-}" ]; then
    echo "🔑 检测到 KEYWORDS 环境变量: ${KEYWORDS}"
    echo "🔄 关键词模式：执行一次后退出"
    exec /usr/local/bin/python -m trendradar
fi

case "${RUN_MODE:-cron}" in
"once")
    echo "🔄 单次执行"
    exec /usr/local/bin/python -m trendradar
    ;;
"cron")
    # 生成 crontab
    echo "${CRON_SCHEDULE:-15 8,12,16,20 * * *} cd /app && /usr/local/bin/python -m trendradar" > /tmp/crontab
    
    echo "📅 生成的crontab内容:"
    cat /tmp/crontab

    if ! /usr/local/bin/supercronic -test /tmp/crontab; then
        echo "❌ crontab格式验证失败"
        exit 1
    fi

    # 立即执行一次（如果配置了）
    if [ "${IMMEDIATE_RUN:-false}" = "true" ]; then
        echo "▶️ 立即执行一次"
        /usr/local/bin/python -m trendradar
    fi

    # 启动 Web 服务器（如果配置了）
    if [ "${ENABLE_WEBSERVER:-false}" = "true" ]; then
        echo "🌐 启动 Web 服务器..."
        /usr/local/bin/python manage.py start_webserver
    fi

    echo "⏰ 启动supercronic: ${CRON_SCHEDULE:-*/30 * * * *}"
    echo "🎯 supercronic 将作为 PID 1 运行"

    exec /usr/local/bin/supercronic -passthrough-logs /tmp/crontab
    exec /usr/local/bin/python -m trendradar
    ;;
*)
    exec "$@"
    ;;
esac
