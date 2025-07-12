"""
Minimal version that works with Python 3.12 without any complex dependencies
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import re
import json
from typing import List, Optional

app = FastAPI(
    title="Minimal Term Extractor API",
    description="超轻量级术语提取API - 专为Python 3.12优化",
    version="1.0.0-minimal"
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

# 建筑业专业术语词典
CONSTRUCTION_TERMS = {
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

# 正規表現パターン
TERM_PATTERNS = [
    (r'[ァ-ヴー]{3,}', "カタカナ", 0.7),  # カタカナ用語
    (r'[一-龯]{2,}[工事|施工|構造|材料|設備|管理]', "建築専門", 0.9),  # 建築専門用語
    (r'[A-Z]{2,}', "略語", 0.8),  # 略語
    (r'\d+[級|種|号|型|㎜|cm|m|階]', "規格", 0.8),  # 規格・寸法
    (r'[一-龯]{2,}[性|度|率|量|値]', "性能", 0.6),  # 性能関連
]

def extract_terms_minimal(text: str, min_confidence: float = 0.5) -> List[dict]:
    """軽量版術語抽出"""
    found_terms = []
    seen_terms = set()
    
    # 1. 既知の専門用語をチェック
    for term, info in CONSTRUCTION_TERMS.items():
        if term in text and term not in seen_terms:
            seen_terms.add(term)
            found_terms.append({
                "term": term,
                "confidence": 0.95,
                "category": info["category"]
            })
        
        # エイリアスもチェック
        for alias in info["aliases"]:
            if alias in text and alias not in seen_terms:
                seen_terms.add(alias)
                found_terms.append({
                    "term": alias,
                    "confidence": 0.85,
                    "category": info["category"]
                })
    
    # 2. パターンマッチング
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
    
    # 3. 信頼度でフィルタリング
    return [term for term in found_terms if term["confidence"] >= min_confidence]

def search_terms(query: str, limit: int = 10) -> List[dict]:
    """術語検索"""
    results = []
    query_lower = query.lower()
    
    # 既知の術語から検索
    for term, info in CONSTRUCTION_TERMS.items():
        if query in term or query_lower in term.lower():
            results.append({
                "term": term,
                "confidence": 0.95,
                "category": info["category"]
            })
        
        # エイリアスからも検索
        for alias in info["aliases"]:
            if query in alias or query_lower in alias.lower():
                results.append({
                    "term": alias,
                    "confidence": 0.85,
                    "category": info["category"]
                })
    
    return results[:limit]

# API エンドポイント
@app.post("/api/v1/extract", response_model=ExtractResponse)
async def extract_terms(request: ExtractRequest):
    """テキストから建築専門用語を抽出"""
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
        raise HTTPException(status_code=500, detail=f"抽出エラー: {str(e)}")

@app.post("/api/v1/search")
async def search_construction_terms(request: SearchRequest):
    """建築専門用語を検索"""
    try:
        results = search_terms(request.query, request.limit)
        
        return {
            "query": request.query,
            "results": results,
            "count": len(results)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"検索エラー: {str(e)}")

@app.get("/api/v1/terms")
async def list_all_terms():
    """全ての登録済み専門用語を表示"""
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

@app.get("/")
async def root():
    return {
        "message": "建築業界専門用語抽出API",
        "version": "1.0.0-minimal",
        "description": "Python 3.12対応・軽量版",
        "features": [
            "専門用語抽出",
            "用語検索",
            "カテゴリ分類"
        ],
        "endpoints": {
            "extract": "/api/v1/extract",
            "search": "/api/v1/search", 
            "list_terms": "/api/v1/terms"
        }
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "python_version": "3.12+"}

@app.get("/demo")
async def demo():
    """デモ用サンプル"""
    sample_text = "本工事は鉄筋コンクリート造の建築物の基礎工事を含みます。RC構造で耐震性能を確保し、品質管理を徹底します。"
    
    terms = extract_terms_minimal(sample_text)
    
    return {
        "sample_text": sample_text,
        "extracted_terms": terms,
        "usage": "POST /api/v1/extract with {'text': 'your text here'}"
    }

if __name__ == "__main__":
    print("🏗️  建築業界専門用語抽出API starting...")
    print("📡 API docs: http://localhost:8000/docs")
    print("🎯 Demo: http://localhost:8000/demo")
    
    uvicorn.run(
        "main_minimal:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )