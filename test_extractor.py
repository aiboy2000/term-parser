import asyncio
from pathlib import Path
import logging
from term_extractor.core.pdf_extractor import PDFTermExtractor
from term_extractor.core.term_database import TermDatabase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_extraction():
    """Test term extraction functionality"""
    
    # Initialize components
    extractor = PDFTermExtractor()
    db = TermDatabase()
    
    # Test text
    test_text = """
    本工事は鉄筋コンクリート造の建築物の基礎工事を含みます。
    使用する材料は、セメント、鋼材、防水材料等です。
    施工管理においては、品質管理と安全管理を重視します。
    空調設備および給排水設備の設置も行います。
    耐震性能はS造（鉄骨造）と同等以上を確保します。
    """
    
    # Extract terms
    logger.info("Extracting terms from test text...")
    terms = extractor.extract_terms_from_text(test_text)
    
    logger.info(f"Found {len(terms)} terms:")
    for term in terms[:10]:  # Show first 10
        logger.info(f"  - {term['term']} (confidence: {term['confidence']:.2f})")
    
    # Build database
    if terms:
        logger.info("\nBuilding term database...")
        db.build_from_terms(terms)
        
        # Test search
        test_queries = ["コンクリート", "設備", "施工"]
        
        for query in test_queries:
            logger.info(f"\nSearching for '{query}':")
            
            # Hybrid search
            results = db.hybrid_search(query, k=5)
            for result in results:
                logger.info(f"  - {result['term']} (score: {result['score']:.3f})")


async def test_pdf_extraction(pdf_folder: str):
    """Test PDF extraction if folder provided"""
    folder = Path(pdf_folder)
    if not folder.exists():
        logger.error(f"PDF folder not found: {pdf_folder}")
        return
    
    extractor = PDFTermExtractor()
    db = TermDatabase()
    
    logger.info(f"Extracting terms from PDFs in {pdf_folder}...")
    terms = extractor.extract_terms_from_pdfs(folder)
    
    logger.info(f"Extracted {len(terms)} unique terms")
    
    # Show top terms by frequency
    logger.info("\nTop 10 terms by frequency:")
    for term in terms[:10]:
        logger.info(f"  - {term['term']} (freq: {term['frequency']}, conf: {term['confidence']:.2f})")
    
    # Build and save database
    if terms:
        db.build_from_terms(terms)
        logger.info("Database built and saved successfully")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Test with PDF folder
        asyncio.run(test_pdf_extraction(sys.argv[1]))
    else:
        # Test with sample text
        asyncio.run(test_extraction())