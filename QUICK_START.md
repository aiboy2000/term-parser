# 快速启动指南 - Python 3.12

## 问题解决方案

您遇到的是Python 3.12兼容性问题。这里是完全兼容的解决方案：

## 方案1: 超轻量版（推荐）

### 1. 安装最少依赖
```bash
# 激活虚拟环境
venv\Scripts\activate

# 安装最基础的包
pip install fastapi uvicorn pydantic

# 或者使用兼容文件
pip install -r requirements-py312.txt
```

### 2. 运行超轻量版
```bash
python main_minimal.py
```

### 3. 测试功能
访问: http://localhost:8000/demo

## 方案2: 使用预编译包

```bash
# 使用预编译的numpy（如果需要）
pip install --only-binary=numpy numpy

# 或者完全跳过numpy
pip install fastapi uvicorn pydantic sentence-transformers
```

## 功能特点

### 超轻量版 (main_minimal.py)
- ✅ 零编译依赖
- ✅ 内置建筑专业词典
- ✅ 正则表达式模式匹配
- ✅ REST API接口
- ✅ 完全兼容Python 3.12

### API端点
- `POST /api/v1/extract` - 文本术语提取
- `POST /api/v1/search` - 术语搜索
- `GET /api/v1/terms` - 查看所有术语
- `GET /demo` - 演示功能

## 使用示例

### 术语提取
```bash
curl -X POST "http://localhost:8000/api/v1/extract" \
  -H "Content-Type: application/json" \
  -d '{"text": "鉄筋コンクリート造の基礎工事を実施します。RC構造で品質管理を行います。"}'
```

### 术语搜索
```bash
curl -X POST "http://localhost:8000/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "コンクリート", "limit": 5}'
```

## 如果仍然需要高级功能

### 选择其他Python版本
```bash
# 如果可能，使用Python 3.10或3.11
pyenv install 3.11.0
pyenv local 3.11.0
```

### 使用Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements-basic.txt .
RUN pip install -r requirements-basic.txt
COPY . .
CMD ["python", "main.py"]
```

## 验证安装成功

```bash
# 检查API是否运行
curl http://localhost:8000/health

# 查看API文档
# 访问 http://localhost:8000/docs
```

## 下一步

1. **立即可用**: 使用 `main_minimal.py` 开始工作
2. **扩展功能**: 后续可以逐步添加更多依赖
3. **生产部署**: 考虑使用Docker或其他Python版本

现在就试试超轻量版吧！