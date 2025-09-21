#!/bin/bash

# 生产环境备份脚本
BACKUP_DIR="/home/qwkj/drass/production/backups/daily"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="$BACKUP_DIR/$DATE"

# 创建备份目录
mkdir -p "$BACKUP_PATH"

# 备份数据库
if [ -f "/home/qwkj/drass/data/database.db" ]; then
    cp /home/qwkj/drass/data/database.db "$BACKUP_PATH/"
fi

# 备份文档数据
if [ -d "/home/qwkj/drass/data/uploads" ]; then
    tar -czf "$BACKUP_PATH/uploads.tar.gz" -C /home/qwkj/drass/data uploads
fi

# 备份向量数据库
if [ -d "/home/qwkj/drass/data/chromadb" ]; then
    tar -czf "$BACKUP_PATH/chromadb.tar.gz" -C /home/qwkj/drass/data chromadb
fi

# 备份配置文件
cp -r /home/qwkj/drass/production/configs "$BACKUP_PATH/"

# 创建备份清单
cat > "$BACKUP_PATH/manifest.txt" << EOL
磐石数据合规分析系统生产环境备份
备份时间: $(date)
备份版本: 1.0.0

包含内容:
- 数据库文件 (database.db)
- 文档数据 (uploads.tar.gz)
- 向量数据库 (chromadb.tar.gz)
- 配置文件 (configs/)

备份大小: $(du -sh "$BACKUP_PATH" | cut -f1)
EOL

echo "备份完成: $BACKUP_PATH"
