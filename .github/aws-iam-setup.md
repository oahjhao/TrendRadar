# AWS IAM Role 配置指南（GitHub Actions OIDC）

## 概述
配置 AWS IAM Role 允许 GitHub Actions 安全地访问 AWS ECR，无需存储长期凭证。

## 步骤1：创建 IAM Role

### 1.1 创建信任策略
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::648104168728:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:oahjhao/TrendRadar:*"
        }
      }
    }
  ]
}
```

### 1.2 创建 IAM Role
```bash
aws iam create-role \
  --role-name github-actions-role \
  --assume-role-policy-document file://trust-policy.json \
  --description "Role for GitHub Actions to push to ECR" \
  --region us-west-2
```

## 步骤2：附加权限策略

### 2.1 创建权限策略
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:GetRepositoryPolicy",
        "ecr:DescribeRepositories",
        "ecr:ListImages",
        "ecr:DescribeImages",
        "ecr:BatchGetImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload",
        "ecr:PutImage"
      ],
      "Resource": "arn:aws:ecr:us-west-2:648104168728:repository/shanavasa/trendradar-app"
    },
    {
      "Effect": "Allow",
      "Action": "ecr:GetAuthorizationToken",
      "Resource": "*"
    }
  ]
}
```

### 2.2 附加策略到 Role
```bash
aws iam put-role-policy \
  --role-name github-actions-role \
  --policy-name ECRPushPolicy \
  --policy-document file://ecr-policy.json \
  --region us-west-2
```

## 步骤3：配置 GitHub Secrets（备选方案）

如果不想使用 OIDC，可以使用传统方式：

### 3.1 创建 IAM 用户
```bash
aws iam create-user --user-name github-actions-user
```

### 3.2 创建访问密钥
```bash
aws iam create-access-key --user-name github-actions-user
```

### 3.3 在 GitHub 设置 Secrets
```
Settings → Secrets and variables → Actions → New repository secret

添加：
- AWS_ACCESS_KEY_ID: <从上面获取>
- AWS_SECRET_ACCESS_KEY: <从上面获取>
```

## 步骤4：验证配置

### 4.1 测试 OIDC 连接
```bash
# 在 GitHub Actions workflow 中测试
aws sts get-caller-identity
```

### 4.2 测试 ECR 访问
```bash
aws ecr describe-repositories --region us-west-2
```

## 故障排除

### 问题1：权限不足
```
Error: User is not authorized to perform: ecr:PutImage
```
**解决**：检查 IAM Role 权限策略，确保包含所有必要的 ECR 操作。

### 问题2：OIDC 配置错误
```
Error: Not authorized to perform sts:AssumeRoleWithWebIdentity
```
**解决**：检查信任策略中的条件，确保 GitHub 仓库路径正确。

### 问题3：ECR 仓库不存在
```
Error: RepositoryNotFoundException
```
**解决**：先创建 ECR 仓库：
```bash
aws ecr create-repository \
  --repository-name shanavasa/trendradar-app \
  --region us-west-2
```

## 安全最佳实践

### 1. 最小权限原则
- 只授予必要的 ECR 权限
- 限制到特定仓库

### 2. 定期审计
```bash
# 查看 Role 的使用情况
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=AssumeRoleWithWebIdentity \
  --region us-west-2
```

### 3. 监控和告警
- 设置 CloudWatch 告警监控异常访问
- 定期轮换策略（如果使用传统方式）

## 相关资源

### AWS 文档
- [GitHub Actions 与 AWS 集成](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_oidc_github-actions.html)
- [ECR 权限管理](https://docs.aws.amazon.com/AmazonECR/latest/userguide/security-iam.html)

### GitHub 文档
- [使用 OIDC 与 AWS 集成](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services)

### 示例仓库
- [aws-actions/configure-aws-credentials](https://github.com/aws-actions/configure-aws-credentials)
- [aws-actions/amazon-ecr-login](https://github.com/aws-actions/amazon-ecr-login)