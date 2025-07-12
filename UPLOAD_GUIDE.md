# 文件上传功能使用指南

## 概述

增强版术语抽取API现在支持从RAG系统或其他来源上传专业术语文件，支持以下格式：
- **Text (.txt)** - 纯文本格式
- **CSV (.csv)** - 表格格式  
- **Markdown (.md)** - 文档格式

## 支持的文件格式

### 1. Text文件格式 (.txt)

```
# 支持注释行
术语名|分类|别名1,别名2
预应力混凝土|構造|PC,プレストレスト
钢筋混凝土|構造|RC,鉄筋コンクリート
```

**格式规则：**
- 使用 `|` 分隔字段
- 第一字段：术语名（必需）
- 第二字段：分类（可选，默认"一般"）
- 第三字段：别名（可选，用逗号分隔）
- `#` 开头的行为注释

### 2. CSV文件格式 (.csv)

```csv
term,category,aliases
高强度混凝土,構造,"高强混凝土,HPC"
轻质混凝土,構造,"軽量コンクリート,LC"
```

**支持的列名：**
- **术语**: `term`, `术语`, `專門用語`, `名称`
- **分类**: `category`, `分类`, `カテゴリ`, `類別`
- **别名**: `aliases`, `别名`, `エイリアス`, `別稱`

### 3. Markdown文件格式 (.md)

```markdown
# 主分类

## 子分类

- 术语名 (别名1, 别名2)
- 另一个术语

| 术语 | 分类 | 别名 |
|------|------|------|
| 进度计划 | 管理 | スケジュール,工程表 |
```

**支持特性：**
- 标题自动作为分类
- 列表项作为术语
- 表格格式
- 括号内自动识别为别名

## API使用方法

### 1. 文件上传

```bash
curl -X POST "http://localhost:8000/api/v1/upload" \
  -F "file=@your_terms_file.txt"
```

### 2. 手动添加单个术语

```bash
curl -X POST "http://localhost:8000/api/v1/terms/add" \
  -H "Content-Type: application/json" \
  -d '{
    "term": "新术语",
    "category": "分类",
    "aliases": ["别名1", "别名2"]
  }'
```

### 3. 删除术语

```bash
curl -X DELETE "http://localhost:8000/api/v1/terms/delete/术语名"
```

### 4. 查看统计信息

```bash
curl "http://localhost:8000/api/v1/terms/stats"
```

### 5. 查看支持的格式

```bash
curl "http://localhost:8000/api/v1/upload/formats"
```

## 响应示例

### 上传成功响应
```json
{
  "message": "成功处理 sample_terms.txt",
  "processed_count": 15,
  "added_terms": ["预应力混凝土", "钢结构", "中央空调"],
  "skipped_terms": ["鉄筋コンクリート"]
}
```

### 统计信息响应
```json
{
  "total_terms": 45,
  "default_terms": 15,
  "custom_terms": 30,
  "categories": {
    "構造": 20,
    "設備": 15,
    "施工": 8,
    "管理": 2
  },
  "storage_file": "custom_terms.json"
}
```

## 与RAG系统集成

### 1. 从RAG系统导出术语

RAG系统可以将提取的术语导出为支持的格式：

```python
# RAG系统示例代码
def export_terms_to_csv(extracted_terms):
    with open('rag_terms.csv', 'w', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['term', 'category', 'aliases'])
        for term in extracted_terms:
            writer.writerow([term.name, term.category, ','.join(term.aliases)])
```

### 2. 自动上传到术语抽取系统

```python
import requests

def upload_terms_file(file_path):
    with open(file_path, 'rb') as f:
        response = requests.post(
            "http://localhost:8000/api/v1/upload",
            files={"file": f}
        )
    return response.json()
```

## 注意事项

1. **文件编码**: 必须使用UTF-8编码
2. **文件大小**: 建议不超过10MB
3. **术语重复**: 重复的术语会被跳过
4. **内置术语**: 无法删除系统内置的术语
5. **持久化**: 自定义术语会保存到 `custom_terms.json` 文件

## 示例文件

项目中提供了示例文件：
- `examples/sample_terms.txt` - Text格式示例
- `examples/sample_terms.csv` - CSV格式示例  
- `examples/sample_terms.md` - Markdown格式示例

## 测试上传功能

```bash
# 启动服务器
python main_enhanced.py

# 测试上传示例文件
curl -X POST "http://localhost:8000/api/v1/upload" \
  -F "file=@examples/sample_terms.txt"

# 查看结果
curl "http://localhost:8000/api/v1/terms/stats"
```