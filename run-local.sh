#!/bin/bash
# TrendRadar 本地容器执行脚本
# 支持关键词搜索或热点查询
#
# 用法:
#   ./run-local.sh                    # 热点模式
#   ./run-local.sh "AI,区块链"         # 关键词搜索
#   ./run-local.sh "新能源" --hot      # 热点+关键词

set -e

echo "🚀 TrendRadar 本地容器执行脚本"
echo "============================================"

# 配置
IMAGE_NAME="trendradar-local"
CONTAINER_NAME="trendradar-run"
PROJECT_DIR="/home/admin/.openclaw/workspace/projects/TrendRadar"
DATA_DIR="/home/admin/.openclaw/data/trendradar"

# 解析参数
KEYWORDS=""
MODE="current"

if [ $# -gt 0 ]; then
    # 第一个参数作为关键词
    KEYWORDS="$1"
    shift
fi

# 检查镜像是否存在，不存在则构建
if ! docker images "$IMAGE_NAME" | grep -q "$IMAGE_NAME"; then
    echo "🛠 构建镜像 $IMAGE_NAME..."
    
    # 使用 Dockerfile.on-demand 作为基础
    cd "$PROJECT_DIR"
    
    # 创建临时 Dockerfile
    cat > /tmp/Dockerfile.trendradar << 'DOCKERFILE'
FROM docker.io/python:3.10-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl ca-certificates bash && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY trendradar/ ./trendradar/
COPY config/ ./config/

# 创建输出目录
RUN mkdir -p /app/output

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    CONFIG_PATH=/app/config/config.yaml \
    DOCKER_CONTAINER=true \
    TZ=Asia/Shanghai

# 创建入口脚本
RUN echo '#!/bin/bash\n\
echo "=== TrendRadar 执行 ==="\n\
echo "时间: $(date)"\n\
echo "关键词: ${TRENDRADAR_KEYWORDS:-热点模式}"\n\
echo "==="\n\
cd /app\n\
python -m trendradar "$@"\n\
EXIT_CODE=$?\n\
echo "执行完成，退出码: $EXIT_CODE"\n\
exit $EXIT_CODE' > /entrypoint.sh && chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["--once"]
DOCKERFILE

    # 构建镜像
    docker build -f /tmp/Dockerfile.trendradar -t "$IMAGE_NAME" .
    echo "✅ 镜像构建完成"
else
    echo "✅ 镜像已存在"
fi

# 创建输出目录
mkdir -p "$DATA_DIR/output"

# 清理旧容器
docker rm -f "$CONTAINER_NAME" 2>/dev/null || true

# 准备环境变量
ENV_VARS="-e TZ=Asia/Shanghai"
if [ -n "$KEYWORDS" ]; then
    ENV_VARS="$ENV_VARS -e TRENDRADAR_KEYWORDS=$KEYWORDS"
    echo "🔍 关键词模式: $KEYWORDS"
else
    echo "🔥 热点模式"
fi

# 运行容器
echo ""
echo "🚀 启动 TrendRadar 容器..."
docker run --rm \
    --name "$CONTAINER_NAME" \
    -v "$DATA_DIR/output:/app/output" \
    -v "$DATA_DIR/config:/app/config:ro" \
    $ENV_VARS \
    "$IMAGE_NAME" \
    --once

EXIT_CODE=$?

# 推送结果
if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "✅ TrendRadar 执行成功"
    
    # 读取最新的输出文件并推送
    TODAY=$(date '+%Y-%m-%d')
    OUTPUT_DIR="$DATA_DIR/output/$TODAY/txt"
    
    if [ -d "$OUTPUT_DIR" ]; then
        # 找到最新的 txt 文件
        LATEST_TXT=$(ls -t "$OUTPUT_DIR"/*.txt 2>/dev/null | head -1)
        
        if [ -n "$LATEST_TXT" ] && [ -f "$LATEST_TXT" ]; then
            echo "📄 读取结果文件: $LATEST_TXT"
            
            # 提取 Top 30 条新闻（每个平台前5条）
            PUSH_CONTENT=$(awk '
            BEGIN { platform=""; count=0; total=0 }
            /^[a-z]+ \| / { 
                platform=$0; 
                count=0; 
                if (total > 0) print "";
                print "\n" platform;
                next 
            }
            /^[0-9]+\./ && count < 5 && total < 30 {
                # 去掉 URL 部分
                gsub(/ \[URL:.*\]/, "");
                print $0;
                count++;
                total++
            }
            ' "$LATEST_TXT" | head -100)
            
            # 构建完整消息
            MESSAGE="📰 TrendRadar 热点新闻\n"
            MESSAGE="$MESSAGE\n时间: $(date '+%Y-%m-%d %H:%M:%S')\n"
            if [ -n "$KEYWORDS" ]; then
                MESSAGE="$MESSAGE关键词: $KEYWORDS\n"
            fi
            MESSAGE="$MESSAGE\n$PUSH_CONTENT"
            
            # 发送推送
            if [ -f "/home/admin/.openclaw/scripts/notify.sh" ]; then
                bash /home/admin/.openclaw/scripts/notify.sh "$MESSAGE" || true
            fi
        else
            echo "⚠️  未找到输出文件"
        fi
    else
        echo "⚠️  未找到今日输出目录: $OUTPUT_DIR"
    fi
else
    echo ""
    echo "❌ TrendRadar 执行失败 (退出码: $EXIT_CODE)"
    exit $EXIT_CODE
fi

echo ""
echo "📁 输出目录: $DATA_DIR/output"
