# Installation Guide

## Windows安装指南

### 1. 环境准备
```bash
# 确保Python 3.8+已安装
python --version

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
venv\Scripts\activate
```

### 2. 分步安装依赖

#### Step 1: 更新基础工具
```bash
# 更新pip
python -m pip install --upgrade pip

# 安装基础构建工具
pip install setuptools wheel build
```

#### Step 2: 安装基础依赖
```bash
pip install -r requirements-basic.txt
```

#### Step 3: 安装NLP依赖
```bash
pip install -r requirements-nlp.txt
```

#### Step 4: 安装日语处理(可选)
```bash
# 如果需要日语分词功能
pip install mecab-python3 sudachipy sudachidict-core
```

### 3. 测试安装
```bash
# 运行基础测试
python test_basic.py

# 启动API服务器
python main.py
```

## 如果安装仍然失败

### 选项1: 使用预编译包
```bash
# 使用conda替代pip
conda install -c conda-forge sentence-transformers faiss-cpu
```

### 选项2: 跳过可选依赖
修改代码以跳过某些功能：

```python
# 在pdf_extractor.py中添加
try:
    from sudachipy import tokenizer, dictionary
    HAS_SUDACHI = True
except ImportError:
    HAS_SUDACHI = False
    print("Warning: SudachiPy not available. Using simple text processing.")
```

### 选项3: 最小版本运行
只安装核心依赖：
```bash
pip install fastapi uvicorn pydantic numpy pandas
```

然后使用简化的文本处理功能。

## 故障排除

### 常见错误及解决方案

1. **setuptools错误**
   ```bash
   pip install --upgrade setuptools
   ```

2. **编译错误**
   ```bash
   # 安装Microsoft C++ Build Tools
   # 或使用预编译wheel
   pip install --only-binary=all package_name
   ```

3. **内存不足**
   ```bash
   # 增加pip缓存
   pip install --no-cache-dir package_name
   ```

4. **网络问题**
   ```bash
   # 使用国内镜像
   pip install -i https://pypi.tuna.tsinghua.edu.cn/simple package_name
   ```

## 验证安装
```bash
# 检查核心功能
python -c "import fastapi, uvicorn; print('Core API ready')"

# 检查NLP功能
python -c "import sentence_transformers; print('NLP ready')"

# 运行完整测试
python -m unittest discover tests
```