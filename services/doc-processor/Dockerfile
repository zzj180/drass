# 优化的Document Processor Dockerfile
# 使用国内镜像源加速构建

FROM python:3.11-slim

# 设置环境变量
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py

# 配置Debian镜像源（使用清华大学镜像）
RUN echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ bookworm main" > /etc/apt/sources.list && \
    echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ bookworm-updates main" >> /etc/apt/sources.list && \
    echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian-security bookworm-security main" >> /etc/apt/sources.list

# 更新包列表并安装最小化依赖
RUN apt-get update && apt-get install -y \
    # 基础工具
    curl \
    wget \
    # 轻量级PDF处理工具
    poppler-utils \
    # 基础图像处理
    libmagic1 \
    # 最小化OCR支持（仅英文）
    tesseract-ocr \
    tesseract-ocr-eng \
    # 清理
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get autoremove -y

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 配置pip使用国内镜像源以加速下载
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple/ && \
    pip config set install.trusted-host pypi.tuna.tsinghua.edu.cn && \
    pip config set global.extra-index-url "https://mirrors.aliyun.com/pypi/simple/ https://pypi.douban.com/simple/"

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p /app/uploads /app/processed /app/temp

# 暴露端口
EXPOSE 5003

# 启动命令
CMD ["python", "app.py"]