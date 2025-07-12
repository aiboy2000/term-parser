"""
Enhanced version with file upload support for terms management
Supports markdown, text, and CSV file uploads from RAG systems
"""
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import re
import json
import csv
import io
from typing import List, Optional, Dict
from pathlib import Path

app = FastAPI(
    title="Enhanced Term Extractor API",
    description="建筑业专业术语抽取API - 支持文件上传和术语管理",
    version="2.0.0-enhanced"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据模型
class ExtractRequest(BaseModel):
    text: str
    min_confidence: Optional[float] = 0.5

class TermInfo(BaseModel):
    term: str
    confidence: float
    category: str

class ExtractResponse(BaseModel):
    terms: List[TermInfo]
    count: int

class SearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 10

class AddTermRequest(BaseModel):
    term: str
    category: str
    aliases: Optional[List[str]] = []
    confidence: Optional[float] = 0.9

class UploadResponse(BaseModel):
    message: str
    processed_count: int
    added_terms: List[str]
    skipped_terms: List[str]

class TermManagementResponse(BaseModel):
    message: str
    affected_count: int

# 持久化存储文件
TERMS_STORAGE_FILE = "custom_terms.json"

# 建筑业专业术语词典（默认内置）
DEFAULT_CONSTRUCTION_TERMS = {
    "鉄筋コンクリート": {"aliases": ["RC", "鉄コン"], "category": "構造"},
    "プレストレストコンクリート": {"aliases": ["PC"], "category": "構造"},
    "鉄骨鉄筋コンクリート": {"aliases": ["SRC"], "category": "構造"},
    "基礎工事": {"aliases": ["基礎"], "category": "施工"},
    "躯体工事": {"aliases": ["躯体"], "category": "施工"},
    "仕上工事": {"aliases": ["仕上げ"], "category": "施工"},
    "空調設備": {"aliases": ["空調", "エアコン"], "category": "設備"},
    "給排水設備": {"aliases": ["給排水"], "category": "設備"},
    "電気設備": {"aliases": ["電気"], "category": "設備"},
    "品質管理": {"aliases": ["品質"], "category": "管理"},
    "安全管理": {"aliases": ["安全"], "category": "管理"},
    "施工管理": {"aliases": ["施工"], "category": "管理"},
    "耐震構造": {"aliases": ["耐震"], "category": "構造"},
    "免震構造": {"aliases": ["免震"], "category": "構造"},
    "制震構造": {"aliases": ["制震"], "category": "構造"},
}

# 动态术语词典（可修改）
CONSTRUCTION_TERMS = DEFAULT_CONSTRUCTION_TERMS.copy()

def load_custom_terms():
    """从文件加载自定义术语"""
    global CONSTRUCTION_TERMS
    try:
        if Path(TERMS_STORAGE_FILE).exists():
            with open(TERMS_STORAGE_FILE, 'r', encoding='utf-8') as f:
                custom_terms = json.load(f)
                CONSTRUCTION_TERMS.update(custom_terms)
                print(f"📚 加载了 {len(custom_terms)} 个自定义术语")
    except Exception as e:
        print(f"⚠️ 加载自定义术语失败: {e}")

def save_custom_terms():
    """保存自定义术语到文件"""
    try:
        # 只保存非默认的术语
        custom_terms = {k: v for k, v in CONSTRUCTION_TERMS.items() 
                       if k not in DEFAULT_CONSTRUCTION_TERMS}
        with open(TERMS_STORAGE_FILE, 'w', encoding='utf-8') as f:
            json.dump(custom_terms, f, ensure_ascii=False, indent=2)
        print(f"💾 保存了 {len(custom_terms)} 个自定义术语")
    except Exception as e:
        print(f"⚠️ 保存自定义术语失败: {e}")

def parse_text_file(content: str) -> List[Dict]:
    """解析text文件内容提取术语"""
    terms = []
    lines = content.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # 支持多种格式：
        # 1. 简单术语：术语名
        # 2. 带分类：术语名|分类
        # 3. 带别名：术语名|分类|别名1,别名2
        parts = line.split('|')
        
        term = parts[0].strip()
        category = parts[1].strip() if len(parts) > 1 else "一般"
        aliases = [a.strip() for a in parts[2].split(',')] if len(parts) > 2 else []
        
        if term:
            terms.append({
                "term": term,
                "category": category,
                "aliases": aliases
            })
    
    return terms

def parse_csv_file(content: str) -> List[Dict]:
    """解析CSV文件内容提取术语"""
    terms = []
    
    try:
        reader = csv.DictReader(io.StringIO(content))
        
        for row in reader:
            # 支持的CSV列名（灵活匹配）
            term = (row.get('term') or row.get('术语') or 
                   row.get('專門用語') or row.get('名称') or "").strip()
            
            category = (row.get('category') or row.get('分类') or 
                       row.get('カテゴリ') or row.get('類別') or "一般").strip()
            
            aliases_str = (row.get('aliases') or row.get('别名') or 
                          row.get('エイリアス') or row.get('別稱') or "")
            
            aliases = [a.strip() for a in aliases_str.split(',') if a.strip()]
            
            if term:
                terms.append({
                    "term": term,
                    "category": category,
                    "aliases": aliases
                })
                
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"CSV解析错误: {e}")
    
    return terms

def parse_markdown_file(content: str) -> List[Dict]:
    """解析Markdown文件内容提取术语"""
    terms = []
    current_category = "一般"
    
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        
        # 检测标题作为分类
        if line.startswith('#'):
            current_category = line.lstrip('#').strip()
            continue
        
        # 检测列表项作为术语
        if line.startswith('-') or line.startswith('*'):
            term_line = line.lstrip('-*').strip()
            
            # 支持格式：- 术语名 (别名1, 别名2)
            if '(' in term_line and ')' in term_line:
                term = term_line.split('(')[0].strip()
                aliases_part = term_line.split('(')[1].split(')')[0]
                aliases = [a.strip() for a in aliases_part.split(',')]
            else:
                term = term_line
                aliases = []
            
            if term:
                terms.append({
                    "term": term,
                    "category": current_category,
                    "aliases": aliases
                })
        
        # 检测表格行
        elif '|' in line and not line.startswith('|---'):
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 3:  # 至少有术语和分类列
                term = parts[1] if len(parts) > 1 else ""
                category = parts[2] if len(parts) > 2 else current_category
                aliases_str = parts[3] if len(parts) > 3 else ""
                aliases = [a.strip() for a in aliases_str.split(',') if a.strip()]
                
                if term and term != "术语":
                    terms.append({
                        "term": term,
                        "category": category,
                        "aliases": aliases
                    })
    
    return terms

def add_term_to_dictionary(term: str, category: str, aliases: List[str] = None) -> bool:
    """添加术语到词典"""
    if aliases is None:
        aliases = []
        
    if term not in CONSTRUCTION_TERMS:
        CONSTRUCTION_TERMS[term] = {
            "category": category,
            "aliases": aliases
        }
        return True
    return False

# 正规表达式模式
TERM_PATTERNS = [
    (r'[ァ-ヴー]{3,}', "カタカナ", 0.7),  # カタカナ用语
    (r'[一-龯]{2,}[工事|施工|構造|材料|設備|管理]', "建築専門", 0.9),  # 建筑专门用语
    (r'[A-Z]{2,}', "略語", 0.8),  # 略语
    (r'\d+[級|種|号|型|㎜|cm|m|階]', "規格", 0.8),  # 规格・尺寸
    (r'[一-龯]{2,}[性|度|率|量|値]', "性能", 0.6),  # 性能相关
]

def extract_terms_minimal(text: str, min_confidence: float = 0.5) -> List[dict]:
    """轻量版术语抽取"""
    found_terms = []
    seen_terms = set()
    
    # 1. 既知的专门用语检查
    for term, info in CONSTRUCTION_TERMS.items():
        if term in text and term not in seen_terms:
            seen_terms.add(term)
            found_terms.append({
                "term": term,
                "confidence": 0.95,
                "category": info["category"]
            })
        
        # 别名也检查
        for alias in info["aliases"]:
            if alias in text and alias not in seen_terms:
                seen_terms.add(alias)
                found_terms.append({
                    "term": alias,
                    "confidence": 0.85,
                    "category": info["category"]
                })
    
    # 2. 模式匹配
    for pattern, category, confidence in TERM_PATTERNS:
        matches = re.findall(pattern, text)
        for match in matches:
            if match not in seen_terms and len(match) >= 2:
                seen_terms.add(match)
                found_terms.append({
                    "term": match,
                    "confidence": confidence,
                    "category": category
                })
    
    # 3. 可信度过滤
    return [term for term in found_terms if term["confidence"] >= min_confidence]

def search_terms(query: str, limit: int = 10) -> List[dict]:
    """术语检索"""
    results = []
    query_lower = query.lower()
    
    # 既知的术语检索
    for term, info in CONSTRUCTION_TERMS.items():
        if query in term or query_lower in term.lower():
            results.append({
                "term": term,
                "confidence": 0.95,
                "category": info["category"]
            })
        
        # 别名检索
        for alias in info["aliases"]:
            if query in alias or query_lower in alias.lower():
                results.append({
                    "term": alias,
                    "confidence": 0.85,
                    "category": info["category"]
                })
    
    return results[:limit]

# 原有API端点
@app.post("/api/v1/extract", response_model=ExtractResponse)
async def extract_terms(request: ExtractRequest):
    """从文本中抽取建筑专门用语"""
    try:
        terms = extract_terms_minimal(request.text, request.min_confidence)
        
        term_infos = [
            TermInfo(
                term=t["term"],
                confidence=t["confidence"],
                category=t["category"]
            )
            for t in terms
        ]
        
        return ExtractResponse(
            terms=term_infos,
            count=len(term_infos)
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"抽取错误: {str(e)}")

@app.post("/api/v1/search")
async def search_construction_terms(request: SearchRequest):
    """建筑专门用语检索"""
    try:
        results = search_terms(request.query, request.limit)
        
        return {
            "query": request.query,
            "results": results,
            "count": len(results)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检索错误: {str(e)}")

@app.get("/api/v1/terms")
async def list_all_terms():
    """显示全部登录的专门用语"""
    terms = []
    for term, info in CONSTRUCTION_TERMS.items():
        terms.append({
            "term": term,
            "category": info["category"],
            "aliases": info["aliases"]
        })
    
    return {
        "terms": terms,
        "count": len(terms)
    }

# 新增API端点
@app.post("/api/v1/upload", response_model=UploadResponse)
async def upload_terms_file(file: UploadFile = File(...)):
    """上传术语文件 (支持 .txt, .csv, .md 格式)"""
    try:
        # 检查文件类型
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in ['.txt', '.csv', '.md']:
            raise HTTPException(
                status_code=400, 
                detail="不支持的文件格式。请上传 .txt, .csv 或 .md 文件"
            )
        
        # 读取文件内容
        content = await file.read()
        content_str = content.decode('utf-8')
        
        # 根据文件类型解析
        if file_extension == '.txt':
            parsed_terms = parse_text_file(content_str)
        elif file_extension == '.csv':
            parsed_terms = parse_csv_file(content_str)
        elif file_extension == '.md':
            parsed_terms = parse_markdown_file(content_str)
        
        # 添加术语到词典
        added_terms = []
        skipped_terms = []
        
        for term_data in parsed_terms:
            if add_term_to_dictionary(
                term_data['term'], 
                term_data['category'], 
                term_data['aliases']
            ):
                added_terms.append(term_data['term'])
            else:
                skipped_terms.append(term_data['term'])
        
        # 保存到文件
        save_custom_terms()
        
        return UploadResponse(
            message=f"成功处理 {file.filename}",
            processed_count=len(parsed_terms),
            added_terms=added_terms,
            skipped_terms=skipped_terms
        )
        
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="文件编码错误，请使用UTF-8编码")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件处理错误: {str(e)}")

@app.post("/api/v1/terms/add", response_model=TermManagementResponse)
async def add_single_term(request: AddTermRequest):
    """手动添加单个术语"""
    try:
        success = add_term_to_dictionary(
            request.term, 
            request.category, 
            request.aliases
        )
        
        if success:
            save_custom_terms()
            return TermManagementResponse(
                message=f"成功添加术语: {request.term}",
                affected_count=1
            )
        else:
            return TermManagementResponse(
                message=f"术语已存在: {request.term}",
                affected_count=0
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加术语失败: {str(e)}")

@app.delete("/api/v1/terms/delete/{term}")
async def delete_term(term: str):
    """删除术语"""
    try:
        if term in CONSTRUCTION_TERMS and term not in DEFAULT_CONSTRUCTION_TERMS:
            del CONSTRUCTION_TERMS[term]
            save_custom_terms()
            return TermManagementResponse(
                message=f"成功删除术语: {term}",
                affected_count=1
            )
        elif term in DEFAULT_CONSTRUCTION_TERMS:
            return TermManagementResponse(
                message=f"无法删除内置术语: {term}",
                affected_count=0
            )
        else:
            return TermManagementResponse(
                message=f"术语不存在: {term}",
                affected_count=0
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除术语失败: {str(e)}")

@app.get("/api/v1/terms/stats")
async def get_terms_stats():
    """获取术语统计信息"""
    total_terms = len(CONSTRUCTION_TERMS)
    default_terms = len(DEFAULT_CONSTRUCTION_TERMS)
    custom_terms = total_terms - default_terms
    
    categories = {}
    for term, info in CONSTRUCTION_TERMS.items():
        cat = info['category']
        categories[cat] = categories.get(cat, 0) + 1
    
    return {
        "total_terms": total_terms,
        "default_terms": default_terms,
        "custom_terms": custom_terms,
        "categories": categories,
        "storage_file": TERMS_STORAGE_FILE
    }

@app.get("/api/v1/upload/formats")
async def get_supported_formats():
    """获取支持的文件格式说明"""
    return {
        "supported_formats": [
            {
                "format": ".txt",
                "description": "纯文本格式",
                "example": "术语名|分类|别名1,别名2"
            },
            {
                "format": ".csv",
                "description": "CSV表格格式",
                "columns": ["term", "category", "aliases"]
            },
            {
                "format": ".md",
                "description": "Markdown格式",
                "features": ["支持标题作为分类", "支持列表和表格"]
            }
        ],
        "encoding": "UTF-8",
        "max_file_size": "10MB"
    }

@app.get("/")
async def root():
    return {
        "message": "建築業界専門用語抽出API - Enhanced",
        "version": "2.0.0-enhanced",
        "description": "支持文件上传和术语管理的增强版",
        "features": [
            "专门用语抽取",
            "用语检索",
            "分类",
            "文件上传 (txt/csv/md)",
            "术语管理",
            "与RAG系统集成"
        ],
        "endpoints": {
            "extract": "/api/v1/extract",
            "search": "/api/v1/search", 
            "list_terms": "/api/v1/terms",
            "upload_file": "/api/v1/upload",
            "add_term": "/api/v1/terms/add",
            "delete_term": "/api/v1/terms/delete/{term}",
            "stats": "/api/v1/terms/stats",
            "formats": "/api/v1/upload/formats"
        }
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "python_version": "3.12+", "version": "enhanced"}

@app.get("/demo")
async def demo():
    """デモ用サンプル"""
    sample_text = "本工事は鉄筋コンクリート造の建築物の基礎工事を含みます。RC構造で耐震性能を確保し、品質管理を徹底します。"
    
    terms = extract_terms_minimal(sample_text)
    
    return {
        "sample_text": sample_text,
        "extracted_terms": terms,
        "usage": {
            "extract": "POST /api/v1/extract with {'text': 'your text here'}",
            "upload": "POST /api/v1/upload with file upload",
            "add_term": "POST /api/v1/terms/add with term data"
        }
    }

if __name__ == "__main__":
    # 启动时加载自定义术语
    load_custom_terms()
    
    print("🏗️  建築業界専門用語抽出API (Enhanced) starting...")
    print("📡 API docs: http://localhost:8000/docs")
    print("🎯 Demo: http://localhost:8000/demo")
    print("📁 Upload: http://localhost:8000/api/v1/upload")
    print("📊 Stats: http://localhost:8000/api/v1/terms/stats")
    
    uvicorn.run(
        "main_enhanced:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )