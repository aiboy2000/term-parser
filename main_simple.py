"""
Simplified version of main.py that works with minimal dependencies
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import re
from typing import List

app = FastAPI(
    title="Simple Term Extractor API",
    description="Simplified API for term extraction without heavy NLP dependencies",
    version="1.0.0-simple"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple models
class ExtractRequest(BaseModel):
    text: str

class TermInfo(BaseModel):
    term: str
    confidence: float

class ExtractResponse(BaseModel):
    terms: List[TermInfo]
    count: int

# Simple term extraction using regex
def simple_extract_terms(text: str) -> List[dict]:
    """Simple term extraction using regex patterns"""
    patterns = [
        (r'[ァ-ヴ]{3,}', 0.8),  # Katakana terms
        (r'[一-龯]{2,}[工事|施工|構造|材料|設備|管理]', 0.9),  # Construction terms
        (r'[A-Z]{2,}', 0.7),  # Abbreviations
        (r'\d+[級|種|号|型]', 0.8),  # Classifications
    ]
    
    terms = []
    seen = set()
    
    for pattern, confidence in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            if match not in seen and len(match) >= 2:
                seen.add(match)
                terms.append({
                    'term': match,
                    'confidence': confidence
                })
    
    return terms

@app.post("/api/v1/extract", response_model=ExtractResponse)
async def extract_terms(request: ExtractRequest):
    """Extract terms from text using simple regex"""
    try:
        terms = simple_extract_terms(request.text)
        
        term_infos = [
            TermInfo(term=t['term'], confidence=t['confidence']) 
            for t in terms
        ]
        
        return ExtractResponse(
            terms=term_infos,
            count=len(term_infos)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {
        "message": "Simple Term Extractor API",
        "version": "1.0.0-simple",
        "note": "This is a simplified version with minimal dependencies"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(
        "main_simple:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )