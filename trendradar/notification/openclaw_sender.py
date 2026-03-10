# coding=utf-8
"""
OpenClaw 消息发送器
通过 OpenClaw Gateway 发送消息到 DingTalk 单聊
"""

import json
import os
from typing import Dict, Optional
import urllib.request
import urllib.error


# 配置
DEFAULT_GATEWAY_URL = "http://127.0.0.1:18789"
DEFAULT_TARGET = "agent:main:dingtalk:direct:01443329476136537748"


def send_to_openclaw(
    content: str,
    title: str = "TrendRadar",
    msg_type: str = "markdown",
    target: Optional[str] = None,
    gateway_url: Optional[str] = None,
    gateway_token: Optional[str] = None,
) -> bool:
    """
    通过 OpenClaw Gateway 发送消息
    
    Args:
        content: 消息内容
        title: 消息标题
        msg_type: 消息类型 (markdown 或 text)
        target: 目标会话 ID
        gateway_url: Gateway URL
        gateway_token: Gateway 认证 Token
        
    Returns:
        bool: 是否发送成功
    """
    gateway_url = gateway_url or os.getenv("OPENCLAW_GATEWAY_URL", DEFAULT_GATEWAY_URL)
    gateway_token = gateway_token or os.getenv(
        "OPENCLAW_GATEWAY_TOKEN",
        "0549b991371eada2b8060109e4d79524c81a115c3e6d9e68136fb69411c19760"
    )
    target = target or os.getenv("OPENCLAW_TARGET", DEFAULT_TARGET)
    
    # 构建 markdown 内容
    if msg_type == "markdown":
        full_content = f"## {title}\n\n{content}"
    else:
        full_content = f"{title}\n\n{content}"
    
    payload = {
        "target": target,
        "message": {
            "type": msg_type,
            "content": full_content
        }
    }
    
    url = f"{gateway_url}/api/v1/message"
    headers = {
        "Authorization": f"Bearer {gateway_token}",
        "Content-Type": "application/json"
    }
    
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            url,
            data=data,
            headers=headers,
            method='POST'
        )
        
        with urllib.request.urlopen(req, timeout=30) as response:
            if response.status in (200, 202):
                print(f"✅ OpenClaw 消息发送成功")
                return True
            else:
                print(f"❌ OpenClaw 消息发送失败 (HTTP {response.status})")
                return False
                
    except Exception as e:
        print(f"❌ OpenClaw 发送失败: {e}")
        return False


def send_report_to_openclaw(
    report_data: Dict,
    report_type: str,
    mode: str = "daily",
) -> bool:
    """
    发送 TrendRadar 报告到 OpenClaw
    
    Args:
        report_data: 报告数据
        report_type: 报告类型
        mode: 报告模式
        
    Returns:
        bool: 是否发送成功
    """
    # 获取报告内容
    content = report_data.get("content", "")
    if not content:
        print("报告内容为空，跳过发送")
        return False
    
    title = f"TrendRadar 热点分析报告 - {report_type}"
    
    return send_to_openclaw(
        content=content,
        title=title,
        msg_type="markdown"
    )
