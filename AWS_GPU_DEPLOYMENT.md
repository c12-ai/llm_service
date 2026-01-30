# GPU Docker 部署到 AWS 完整指南

本指南详细说明如何将 LLM Service 打包为 GPU Docker 镜像并部署到 AWS 机器上运行。

## 📋 目录
1. [本地准备工作](#1-本地准备工作)
2. [构建 Docker 镜像](#2-构建-docker-镜像)
3. [推送镜像到仓库](#3-推送镜像到仓库)
4. [AWS 环境准备](#4-aws-环境准备)
5. [在 AWS 上部署](#5-在-aws-上部署)
6. [验证和测试](#6-验证和测试)
7. [故障排查](#7-故障排查)

---

## 1. 本地准备工作

### 1.1 确认项目文件完整
```bash
# 在项目根目录检查必要文件
ls -la
```

确保包含以下文件：
- `Dockerfile` (GPU 版本)
- `docker-compose.yml`
- `llm_service.py`
- `config.py`
- `requirements.txt`

### 1.2 安装 Docker 和 AWS CLI
```bash
# 检查 Docker 版本
docker --version

# 检查 AWS CLI 版本
aws --version

# 如果未安装 AWS CLI，使用 homebrew 安装 (macOS)
brew install awscli
```

### 1.3 配置 AWS 凭证
```bash
# 配置 AWS 访问密钥
aws configure

# 输入以下信息:
# AWS Access Key ID: [你的访问密钥]
# AWS Secret Access Key: [你的密钥]
# Default region name: [例如: us-west-2]
# Default output format: json
```

---

## 2. 构建 Docker 镜像

### 2.1 修改 docker-compose.yml（可选）
根据 AWS 环境修改配置：

```yaml
# 如果需要在 AWS 上使用不同的模型路径，创建 docker-compose.aws.yml
version: '3.8'

services:
  llm-service:
    build: .
    container_name: qwen-llm-service
    ports:
      - "8000:8000"
    volumes:
      # AWS 上的模型目录
      - /home/ubuntu/models:/models:ro
    environment:
      - MODEL_PATH=/models/Qwen2.5-7B-Instruct
      - SERVICE_HOST=0.0.0.0
      - SERVICE_PORT=8000
      - TENSOR_PARALLEL_SIZE=1
      - GPU_MEMORY_UTILIZATION=0.9
      - MAX_MODEL_LEN=4096
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    restart: unless-stopped
```

### 2.2 构建镜像
```bash
# 构建 GPU 版本的 Docker 镜像
docker build -t llm-service:gpu -f Dockerfile .

# 为镜像添加版本标签
docker tag llm-service:gpu llm-service:gpu-v1.0

# 验证镜像已创建
docker images | grep llm-service
```

### 2.3 本地测试（如果有 GPU）
```bash
# 如果本地有 NVIDIA GPU，可以先测试
docker run --gpus all \
  -p 8000:8000 \
  -v /path/to/models:/models:ro \
  -e MODEL_PATH=/models/Qwen2.5-7B-Instruct \
  llm-service:gpu

# 在另一个终端测试
curl http://localhost:8000/health
```

---

## 3. 推送镜像到仓库

### 方案 A: 推送到 Amazon ECR (推荐)

#### 3.1 创建 ECR 仓库
```bash
# 设置区域变量
export AWS_REGION=us-west-2
export ECR_REPO_NAME=llm-service

# 创建 ECR 仓库
aws ecr create-repository \
    --repository-name ${ECR_REPO_NAME} \
    --region ${AWS_REGION} \
    --image-scanning-configuration scanOnPush=true

# 获取仓库 URI
export ECR_URI=$(aws ecr describe-repositories \
    --repository-names ${ECR_REPO_NAME} \
    --region ${AWS_REGION} \
    --query 'repositories[0].repositoryUri' \
    --output text)

echo "ECR URI: ${ECR_URI}"
```

#### 3.2 登录到 ECR
```bash
# 获取 AWS 账户 ID
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# 登录到 ECR
aws ecr get-login-password --region ${AWS_REGION} | \
    docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com
```

#### 3.3 标记并推送镜像
```bash
# 标记镜像
docker tag llm-service:gpu ${ECR_URI}:latest
docker tag llm-service:gpu ${ECR_URI}:v1.0

# 推送镜像到 ECR
docker push ${ECR_URI}:latest
docker push ${ECR_URI}:v1.0

# 验证镜像已上传
aws ecr list-images --repository-name ${ECR_REPO_NAME} --region ${AWS_REGION}
```

### 方案 B: 推送到 Docker Hub

```bash
# 登录 Docker Hub
docker login

# 标记镜像（替换 your-username）
docker tag llm-service:gpu your-username/llm-service:gpu-v1.0
docker tag llm-service:gpu your-username/llm-service:gpu-latest

# 推送镜像
docker push your-username/llm-service:gpu-v1.0
docker push your-username/llm-service:gpu-latest
```

---

## 4. AWS 环境准备

### 4.1 选择合适的 EC2 实例

推荐的 GPU 实例类型：
- **g4dn.xlarge**: 1x NVIDIA T4 (16GB), 适合小模型（如 Qwen 7B）
- **g4dn.2xlarge**: 1x NVIDIA T4 (16GB), 更多 CPU 和内存
- **g5.xlarge**: 1x NVIDIA A10G (24GB), 适合中型模型（如 Qwen 14B）
- **g5.2xlarge**: 1x NVIDIA A10G (24GB), 更多资源
- **p3.2xlarge**: 1x NVIDIA V100 (16GB), 高性能
- **p4d.24xlarge**: 8x NVIDIA A100 (40GB), 大型模型

### 4.2 启动 EC2 实例

```bash
# 设置变量
export KEY_NAME=your-key-pair-name
export SECURITY_GROUP_ID=sg-xxxxxxxxx
export SUBNET_ID=subnet-xxxxxxxxx
export INSTANCE_TYPE=g4dn.xlarge

# 使用 Deep Learning AMI (Ubuntu) - 已预装 NVIDIA 驱动和 Docker
export AMI_ID=ami-0c2d06d50ce30b442  # Deep Learning AMI GPU PyTorch 2.0 (Ubuntu 20.04)
# 注意: AMI ID 因区域而异，请查询最新的 Deep Learning AMI

# 启动实例
aws ec2 run-instances \
    --image-id ${AMI_ID} \
    --instance-type ${INSTANCE_TYPE} \
    --key-name ${KEY_NAME} \
    --security-group-ids ${SECURITY_GROUP_ID} \
    --subnet-id ${SUBNET_ID} \
    --block-device-mappings '[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":200,"VolumeType":"gp3"}}]' \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=llm-service-gpu}]' \
    --region ${AWS_REGION}

# 获取实例 ID
export INSTANCE_ID=$(aws ec2 describe-instances \
    --filters "Name=tag:Name,Values=llm-service-gpu" "Name=instance-state-name,Values=running" \
    --query 'Reservations[0].Instances[0].InstanceId' \
    --output text \
    --region ${AWS_REGION})

# 获取公网 IP
export PUBLIC_IP=$(aws ec2 describe-instances \
    --instance-ids ${INSTANCE_ID} \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text \
    --region ${AWS_REGION})

echo "Instance ID: ${INSTANCE_ID}"
echo "Public IP: ${PUBLIC_IP}"
```

### 4.3 配置安全组

```bash
# 允许 SSH 访问（22 端口）
aws ec2 authorize-security-group-ingress \
    --group-id ${SECURITY_GROUP_ID} \
    --protocol tcp \
    --port 22 \
    --cidr 0.0.0.0/0 \
    --region ${AWS_REGION}

# 允许服务端口访问（8000 端口）
aws ec2 authorize-security-group-ingress \
    --group-id ${SECURITY_GROUP_ID} \
    --protocol tcp \
    --port 8000 \
    --cidr 0.0.0.0/0 \
    --region ${AWS_REGION}
```

### 4.4 连接到 EC2 实例

```bash
# SSH 连接到实例
ssh -i ~/.ssh/${KEY_NAME}.pem ubuntu@${PUBLIC_IP}
```

---

## 5. 在 AWS 上部署

### 5.1 在 EC2 上准备环境

```bash
# 连接到 EC2 后，更新系统
sudo apt-get update
sudo apt-get upgrade -y

# 验证 NVIDIA 驱动
nvidia-smi

# 验证 Docker 是否已安装
docker --version

# 如果未安装 Docker，执行以下命令
# distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
# curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
# curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
# sudo apt-get update
# sudo apt-get install -y nvidia-docker2
# sudo systemctl restart docker

# 验证 nvidia-docker
sudo docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu20.04 nvidia-smi

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
docker-compose --version
```

### 5.2 准备模型文件

```bash
# 创建模型目录
mkdir -p ~/models
cd ~/models

# 方案 A: 从 ModelScope 下载（如果 AWS 实例可以访问）
pip install modelscope
python -c "from modelscope import snapshot_download; snapshot_download('qwen/Qwen2.5-7B-Instruct', cache_dir='/home/ubuntu/models')"

# 方案 B: 从 S3 下载（推荐，更快）
# 先在本地上传模型到 S3
# aws s3 cp /path/to/models s3://your-bucket/models --recursive
# 然后在 EC2 上下载
# aws s3 sync s3://your-bucket/models /home/ubuntu/models

# 方案 C: 使用 SCP 从本地传输
# 在本地执行:
# scp -r -i ~/.ssh/${KEY_NAME}.pem /path/to/models ubuntu@${PUBLIC_IP}:~/models
```

### 5.3 拉取并运行 Docker 镜像

#### 使用 ECR 镜像

```bash
# 登录到 ECR
aws ecr get-login-password --region ${AWS_REGION} | \
    sudo docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

# 拉取镜像
sudo docker pull ${ECR_URI}:latest

# 运行容器
sudo docker run -d \
    --name llm-service \
    --gpus all \
    -p 8000:8000 \
    -v /home/ubuntu/models:/models:ro \
    -e MODEL_PATH=/models/Qwen2.5-7B-Instruct \
    -e SERVICE_HOST=0.0.0.0 \
    -e SERVICE_PORT=8000 \
    -e TENSOR_PARALLEL_SIZE=1 \
    -e GPU_MEMORY_UTILIZATION=0.9 \
    -e MAX_MODEL_LEN=4096 \
    --restart unless-stopped \
    ${ECR_URI}:latest

# 查看容器日志
sudo docker logs -f llm-service
```

#### 使用 Docker Compose（推荐）

```bash
# 创建项目目录
mkdir -p ~/llm-service
cd ~/llm-service

# 创建 docker-compose.yml
cat > docker-compose.yml <<'EOF'
version: '3.8'

services:
  llm-service:
    image: ${ECR_URI}:latest
    container_name: qwen-llm-service
    ports:
      - "8000:8000"
    volumes:
      - /home/ubuntu/models:/models:ro
    environment:
      - MODEL_PATH=/models/Qwen2.5-7B-Instruct
      - SERVICE_HOST=0.0.0.0
      - SERVICE_PORT=8000
      - TENSOR_PARALLEL_SIZE=1
      - GPU_MEMORY_UTILIZATION=0.9
      - MAX_MODEL_LEN=4096
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    restart: unless-stopped
EOF

# 启动服务
sudo docker-compose up -d

# 查看日志
sudo docker-compose logs -f
```

---

## 6. 验证和测试

### 6.1 健康检查

```bash
# 在 EC2 实例上检查
curl http://localhost:8000/health

# 从本地检查（使用公网 IP）
curl http://${PUBLIC_IP}:8000/health
```

### 6.2 测试生成接口

```bash
# 测试基本生成
curl -X POST http://${PUBLIC_IP}:8000/v1/generate \
    -H "Content-Type: application/json" \
    -d '{
        "prompt": "你好，请介绍一下人工智能",
        "max_tokens": 100,
        "temperature": 0.7
    }'

# 测试聊天接口
curl -X POST http://${PUBLIC_IP}:8000/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{
        "messages": [
            {"role": "user", "content": "什么是深度学习？"}
        ],
        "max_tokens": 100
    }'
```

### 6.3 性能测试

```bash
# 监控 GPU 使用情况
watch -n 1 nvidia-smi

# 查看容器资源使用
sudo docker stats llm-service

# 压力测试（使用 Apache Bench）
sudo apt-get install -y apache2-utils
ab -n 100 -c 10 -p test_request.json -T application/json http://localhost:8000/v1/generate
```

### 6.4 设置开机自启动

```bash
# Docker 服务开机自启
sudo systemctl enable docker

# 使用 docker-compose 的话，创建 systemd 服务
sudo cat > /etc/systemd/system/llm-service.service <<'EOF'
[Unit]
Description=LLM Service
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/ubuntu/llm-service
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

# 启用服务
sudo systemctl enable llm-service
sudo systemctl start llm-service

# 检查状态
sudo systemctl status llm-service
```

---

## 7. 故障排查

### 7.1 常见问题

#### 问题: 容器无法启动
```bash
# 查看详细日志
sudo docker logs llm-service

# 检查 GPU 可用性
nvidia-smi
sudo docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu20.04 nvidia-smi
```

#### 问题: 找不到模型文件
```bash
# 检查模型路径是否正确
ls -la /home/ubuntu/models/

# 检查容器内的挂载
sudo docker exec -it llm-service ls -la /models/
```

#### 问题: GPU 内存不足
```bash
# 调整 GPU 内存利用率
# 在环境变量中设置较小的值
-e GPU_MEMORY_UTILIZATION=0.7

# 或减少 max_model_len
-e MAX_MODEL_LEN=2048
```

#### 问题: 网络无法访问
```bash
# 检查安全组规则
aws ec2 describe-security-groups --group-ids ${SECURITY_GROUP_ID} --region ${AWS_REGION}

# 检查容器端口映射
sudo docker ps

# 在实例上测试
curl http://localhost:8000/health
```

### 7.2 日志收集

```bash
# 收集容器日志
sudo docker logs llm-service > llm-service.log 2>&1

# 收集系统日志
sudo journalctl -u docker > docker.log

# GPU 信息
nvidia-smi > gpu-info.log
```

### 7.3 容器管理命令

```bash
# 停止容器
sudo docker stop llm-service

# 重启容器
sudo docker restart llm-service

# 删除容器
sudo docker rm -f llm-service

# 清理未使用的镜像
sudo docker system prune -a

# 更新镜像
sudo docker pull ${ECR_URI}:latest
sudo docker-compose down
sudo docker-compose up -d
```

---

## 8. 成本优化建议

### 8.1 使用 Spot 实例
对于非关键工作负载，使用 Spot 实例可节省高达 90% 的成本：

```bash
# 启动 Spot 实例
aws ec2 run-instances \
    --image-id ${AMI_ID} \
    --instance-type ${INSTANCE_TYPE} \
    --instance-market-options 'MarketType=spot,SpotOptions={MaxPrice=0.5,SpotInstanceType=one-time}' \
    --key-name ${KEY_NAME} \
    --security-group-ids ${SECURITY_GROUP_ID} \
    --region ${AWS_REGION}
```

### 8.2 自动扩缩容
使用 AWS Auto Scaling 根据负载自动调整实例数量。

### 8.3 使用推理优化的实例
考虑使用 AWS Inferentia (inf1) 或 Trainium 实例以降低成本。

---

## 9. 监控和告警

### 9.1 CloudWatch 监控

```bash
# 安装 CloudWatch 代理
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i -E ./amazon-cloudwatch-agent.deb

# 配置和启动代理
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
    -a fetch-config \
    -m ec2 \
    -s \
    -c file:/opt/aws/amazon-cloudwatch-agent/etc/config.json
```

### 9.2 设置告警

在 AWS Console 中配置 CloudWatch Alarms:
- CPU 使用率 > 80%
- GPU 使用率 > 90%
- 内存使用率 > 85%
- 磁盘使用率 > 80%

---

## 10. 安全最佳实践

1. **最小权限原则**: 为 IAM 角色分配最小必要权限
2. **安全组限制**: 仅允许必要的 IP 和端口访问
3. **密钥管理**: 使用 AWS Secrets Manager 存储敏感信息
4. **定期更新**: 及时更新 Docker 镜像和系统补丁
5. **启用加密**: 对 EBS 卷和 S3 存储启用加密
6. **审计日志**: 启用 CloudTrail 记录 API 调用

---

## 附录

### A. 快速部署脚本

创建一个自动化部署脚本 `deploy-aws.sh`:

```bash
#!/bin/bash
set -e

# 配置变量
export AWS_REGION=${AWS_REGION:-us-west-2}
export ECR_REPO_NAME=${ECR_REPO_NAME:-llm-service}
export INSTANCE_TYPE=${INSTANCE_TYPE:-g4dn.xlarge}

echo "=== Step 1: 构建 Docker 镜像 ==="
docker build -t llm-service:gpu .

echo "=== Step 2: 推送到 ECR ==="
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export ECR_URI=${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_NAME}

aws ecr get-login-password --region ${AWS_REGION} | \
    docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

docker tag llm-service:gpu ${ECR_URI}:latest
docker push ${ECR_URI}:latest

echo "=== Step 3: 部署完成 ==="
echo "ECR URI: ${ECR_URI}:latest"
echo "现在可以在 EC2 实例上拉取并运行此镜像"
```

### B. 环境变量参考

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| MODEL_PATH | /models | 模型文件路径 |
| SERVICE_HOST | 0.0.0.0 | 服务监听地址 |
| SERVICE_PORT | 8000 | 服务端口 |
| TENSOR_PARALLEL_SIZE | 1 | GPU 并行数量 |
| GPU_MEMORY_UTILIZATION | 0.9 | GPU 内存利用率 (0-1) |
| MAX_MODEL_LEN | 4096 | 最大序列长度 |

---

## 总结

按照以上步骤，你应该能够成功将 LLM Service 部署到 AWS GPU 实例上。关键步骤包括：

1. ✅ 本地构建并测试 Docker 镜像
2. ✅ 推送镜像到 ECR
3. ✅ 启动配置好的 GPU EC2 实例
4. ✅ 在实例上部署和运行服务
5. ✅ 验证和监控服务运行状态

如有问题，请参考故障排查章节或查看容器日志。
