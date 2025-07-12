from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from enum import Enum


class SearchType(str, Enum):
    VECTOR = "vector"
    TEXT = "text"
    HYBRID = "hybrid"


class TermInfo(BaseModel):
    term: str = Field(..., description="The extracted term")
    category: str = Field(..., description="Term category")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score")
    frequency: int = Field(..., ge=1, description="Frequency of occurrence")
    aliases: List[str] = Field(default_factory=list, description="Known aliases")
    score: Optional[float] = Field(None, description="Search relevance score")


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query")
    search_type: SearchType = Field(SearchType.HYBRID, description="Type of search")
    limit: int = Field(10, ge=1, le=100, description="Maximum results to return")
    alpha: Optional[float] = Field(0.5, ge=0, le=1, description="Weight for hybrid search (vector vs text)")


class SearchResponse(BaseModel):
    query: str
    results: List[TermInfo]
    count: int
    search_type: SearchType


class ExtractRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text to extract terms from")
    min_confidence: float = Field(0.5, ge=0, le=1, description="Minimum confidence threshold")


class ExtractResponse(BaseModel):
    terms: List[TermInfo]
    count: int


class BatchExtractRequest(BaseModel):
    pdf_folder: str = Field(..., description="Path to folder containing PDFs")
    rebuild_db: bool = Field(False, description="Whether to rebuild the database")


class BatchExtractResponse(BaseModel):
    total_pdfs: int
    total_terms: int
    unique_terms: int
    message: str


class DatabaseInfo(BaseModel):
    total_terms: int
    categories: Dict[str, int]
    last_updated: Optional[str]