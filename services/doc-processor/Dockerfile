FROM python:3.11-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    # 文档转换工具
    pandoc \
    # PDF处理
    poppler-utils \
    # Office文档处理
    libreoffice \
    # OCR支持
    tesseract-ocr \
    tesseract-ocr-chi-sim \
    tesseract-ocr-eng \
    # 图像处理
    libmagic1 \
    # 清理
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 配置pip使用阿里云镜像源以加速下载
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/ && \
    pip config set install.trusted-host mirrors.aliyun.com

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p /app/uploads /app/processed /app/temp

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py

# 暴露端口
EXPOSE 5003

# 启动命令
CMD ["python", "app.py"]