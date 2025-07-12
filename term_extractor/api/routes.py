from fastapi import APIRouter, HTTPException, BackgroundTasks
from pathlib import Path
from typing import List
import logging
from datetime import datetime

from ..core.pdf_extractor import PDFTermExtractor
from ..core.term_database import TermDatabase
from .models import (
    SearchRequest, SearchResponse,
    ExtractRequest, ExtractResponse,
    BatchExtractRequest, BatchExtractResponse,
    DatabaseInfo, TermInfo
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Global instances
pdf_extractor = PDFTermExtractor()
term_db = TermDatabase()

# Try to load existing database
try:
    term_db.load()
    logger.info("Loaded existing term database")
except:
    logger.info("No existing database found")


@router.post("/search", response_model=SearchResponse)
async def search_terms(request: SearchRequest):
    """
    Search for construction terms in the database
    """
    try:
        if request.search_type == "vector":
            results = term_db.search_vector(request.query, request.limit)
        elif request.search_type == "text":
            results = term_db.search_text(request.query, request.limit)
        else:  # hybrid
            results = term_db.hybrid_search(request.query, request.limit, request.alpha)
        
        # Convert to TermInfo models
        term_infos = []
        for result in results:
            term_infos.append(TermInfo(**result))
        
        return SearchResponse(
            query=request.query,
            results=term_infos,
            count=len(term_infos),
            search_type=request.search_type
        )
    
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract", response_model=ExtractResponse)
async def extract_terms(request: ExtractRequest):
    """
    Extract construction terms from provided text
    """
    try:
        # Extract terms
        raw_terms = pdf_extractor.extract_terms_from_text(request.text)
        
        # Filter by confidence
        filtered_terms = [
            term for term in raw_terms 
            if term['confidence'] >= request.min_confidence
        ]
        
        # Convert to TermInfo models
        term_infos = []
        for term in filtered_terms:
            term_info = TermInfo(
                term=term['term'],
                category=pdf_extractor._categorize_term(term['term']),
                confidence=term['confidence'],
                frequency=term.get('frequency', 1),
                aliases=pdf_extractor._generate_aliases(term['term'])
            )
            term_infos.append(term_info)
        
        return ExtractResponse(
            terms=term_infos,
            count=len(term_infos)
        )
    
    except Exception as e:
        logger.error(f"Extraction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract/batch", response_model=BatchExtractResponse)
async def batch_extract(request: BatchExtractRequest, background_tasks: BackgroundTasks):
    """
    Extract terms from multiple PDFs and optionally rebuild database
    """
    try:
        pdf_folder = Path(request.pdf_folder)
        
        if not pdf_folder.exists():
            raise HTTPException(status_code=400, detail="PDF folder not found")
        
        # Extract terms from PDFs
        terms = pdf_extractor.extract_terms_from_pdfs(pdf_folder)
        
        # Get statistics
        pdf_count = len(list(pdf_folder.glob("*.pdf")))
        unique_terms = len(set(t['term'] for t in terms))
        
        # Rebuild database if requested
        if request.rebuild_db and terms:
            background_tasks.add_task(rebuild_database, terms)
            message = "Terms extracted and database rebuild initiated"
        else:
            message = "Terms extracted successfully"
        
        return BatchExtractResponse(
            total_pdfs=pdf_count,
            total_terms=len(terms),
            unique_terms=unique_terms,
            message=message
        )
    
    except Exception as e:
        logger.error(f"Batch extraction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def rebuild_database(terms: List[dict]):
    """Background task to rebuild database"""
    try:
        global term_db
        term_db.build_from_terms(terms)
        logger.info("Database rebuilt successfully")
    except Exception as e:
        logger.error(f"Database rebuild error: {e}")


@router.get("/database/info", response_model=DatabaseInfo)
async def get_database_info():
    """
    Get information about the term database
    """
    try:
        all_terms = term_db.get_all_terms()
        
        # Count by category
        categories = {}
        for term in all_terms:
            cat = term.get('category', '一般')
            categories[cat] = categories.get(cat, 0) + 1
        
        # Get last update time
        metadata_path = term_db.db_path / "metadata.json"
        last_updated = None
        if metadata_path.exists():
            last_updated = datetime.fromtimestamp(
                metadata_path.stat().st_mtime
            ).isoformat()
        
        return DatabaseInfo(
            total_terms=len(all_terms),
            categories=categories,
            last_updated=last_updated
        )
    
    except Exception as e:
        logger.error(f"Database info error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/terms", response_model=List[TermInfo])
async def list_terms(
    limit: int = 100,
    offset: int = 0,
    category: str = None
):
    """
    List all terms in the database with pagination
    """
    try:
        all_terms = term_db.get_all_terms()
        
        # Filter by category if specified
        if category:
            all_terms = [t for t in all_terms if t.get('category') == category]
        
        # Apply pagination
        paginated_terms = all_terms[offset:offset + limit]
        
        # Convert to TermInfo models
        term_infos = []
        for term in paginated_terms:
            term_infos.append(TermInfo(**term))
        
        return term_infos
    
    except Exception as e:
        logger.error(f"List terms error: {e}")
        raise HTTPException(status_code=500, detail=str(e))