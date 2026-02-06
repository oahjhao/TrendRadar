#!/bin/bash
# TrendRadar 按需执行镜像构建脚本

set -e

# 配置
IMAGE_NAME="trendradar-on-demand"
IMAGE_TAG="latest"
DOCKERFILE="docker/Dockerfile.on-demand"

echo "=== 构建 TrendRadar 按需执行镜像 ==="
echo "镜像名称: ${IMAGE_NAME}:${IMAGE_TAG}"
echo "Dockerfile: ${DOCKERFILE}"
echo ""

# 检查 Docker 是否运行
if ! docker info > /dev/null 2>&1; then
    echo "错误: Docker 未运行或当前用户无权限"
    exit 1
fi

# 构建镜像
echo "开始构建镜像..."
docker build -f "${DOCKERFILE}" -t "${IMAGE_NAME}:${IMAGE_TAG}" .

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 镜像构建成功: ${IMAGE_NAME}:${IMAGE_TAG}"
    echo ""
    echo "使用示例:"
    echo "1. 本地测试:"
    echo "   docker run --rm \\"
    echo "     -e TRENDRADAR_KEYWORDS=\"AI,区块链\" \\"
    echo "     ${IMAGE_NAME}:${IMAGE_TAG} --once"
    echo ""
    echo "2. 带配置文件:"
    echo "   docker run --rm \\"
    echo "     -v \$(pwd)/config:/app/config \\"
    echo "     -v \$(pwd)/output:/app/output \\"
    echo "     -e TRENDRADAR_KEYWORDS=\"科技,创新\" \\"
    echo "     ${IMAGE_NAME}:${IMAGE_TAG} --once"
    echo ""
    echo "3. ECS 任务格式:"
    echo "   docker run --rm \\"
    echo "     -e TRENDRADAR_KEYWORDS=\"#关键词1#关键词2\" \\"
    echo "     -e DINGTALK_WEBHOOK_URL=\"your_webhook_url\" \\"
    echo "     ${IMAGE_NAME}:${IMAGE_TAG} --once"
else
    echo "❌ 镜像构建失败"
    exit 1
fi